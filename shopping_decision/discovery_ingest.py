"""京东公开商品搜索/用户提供链接的离线候选导入（非平台 API）。

受 JD-Shopping-MCP 的来源标签思想启发，但完全独立实现，且不发网络请求。
该模块不验证卖家、型号、券、地区报价，也不授予任何购买/登录权限。
第三方商品搜索 JSON 是未受信任数据，永远不会写入已核实时价格。
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
from urllib.parse import urlsplit


_JD_ID = re.compile(r"^[0-9]{5,20}$")
_JD_DESKTOP = re.compile(r"^/([0-9]{5,20})\.html$")
_JD_MOBILE = re.compile(r"^/(?:product/)?([0-9]{5,20})\.html$")
_SEARCH_SOURCE_KIND = {
    "jd-search": "public_site_search",
    "bing-fallback": "external_search_index",
    "proxy": "third_party_proxy",
}

# 状态由本项目的外部许可检查决定，不由第三方 MCP 的工具列表推断。
SOURCE_READINESS = {
    "JD_SHOPPING_MCP_PUBLIC": {
        "offline_candidate_ingest": True, "real_search_authorized": False,
        "live_verified": False, "verified_quote": False, "usage": "research_only"
    },
    "JD_UNION": {
        "offline_candidate_ingest": True, "real_search_authorized": False,
        "live_verified": False, "verified_quote": False, "usage": "needs_application_grant"
    },
    "TAOBAO_TBK": {
        "offline_candidate_ingest": True, "real_search_authorized": False,
        "live_verified": False, "verified_quote": False, "usage": "needs_application_grant"
    },
    "PLAYWRIGHT_USER_BROWSER": {
        "offline_candidate_ingest": False, "real_search_authorized": False,
        "live_verified": False, "verified_quote": False, "usage": "needs_user_consent_and_site_permission"
    },
}


def parse_jd_item_url(value: str) -> dict | None:
    """只接受官方京东商品域名上的完整 HTTPS 商品 URL；拒绝模糊数字猜 SKU。"""
    if not isinstance(value, str) or not value or len(value) > 2048:
        return None
    try:
        parsed = urlsplit(value)
        # 不能允许 userinfo、非标准端口、外部域名、非商品路径；禁止猜短链跳转。
        if (parsed.scheme != "https" or parsed.username is not None
                or parsed.password is not None or parsed.port is not None):
            return None
        host = (parsed.hostname or "").lower()
        if host == "item.jd.com":
            match = _JD_DESKTOP.fullmatch(parsed.path)
        elif host == "item.m.jd.com":
            match = _JD_MOBILE.fullmatch(parsed.path)
        else:
            return None
        if not match:
            return None
        sku = match.group(1)
        return {"platform": "JD_PUBLIC_UNVERIFIED", "platform_item_id": sku,
                "canonical_url": f"https://item.jd.com/{sku}.html"}
    except ValueError:
        return None


def _valid_time(value: object, now: datetime) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if moment.tzinfo is None or moment > now or moment.year < 2000:
            return None
        return moment.astimezone(timezone.utc).isoformat()
    except ValueError:
        return None


def ingest_jd_search_snapshot(payload: dict, *, now: datetime | None = None,
                              max_results: int = 10) -> dict:
    """转换已有的公开搜索 JSON 为发现线索；不是主动搜索或核价。

    输入兼容 JD-Shopping-MCP 的 jd_search_products 结果形状：
    {query, source: jd-search|bing-fallback|proxy, fetchedAt,
     results:[{sku, title, url, price, shopName, source},...]}。
    第三方结果可能失败、篡改或过期，返回字段没有价格值以防误用。
    """
    base = {"operation": "offline_public_discovery_ingest",
            "source": "JD_SHOPPING_MCP_PUBLIC", "status": "invalid_input",
            "items": [], "rejected_count": 0, "warnings": [],
            "quote_verified_count": 0, "transactions_enabled": False,
            "authorized_platform_search": False}
    if (not isinstance(payload, dict) or not isinstance(max_results, int)
            or isinstance(max_results, bool) or not 1 <= max_results <= 20):
        base["warnings"].append("invalid_input_or_limit")
        return base
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        base["warnings"].append("invalid_reference_time")
        return base
    query = payload.get("query")
    results = payload.get("results")
    source = payload.get("source")
    capture = _valid_time(payload.get("fetchedAt"), current)
    if (not isinstance(query, str) or not query.strip() or len(query) > 200
            or not isinstance(results, list) or len(results) > 100
            or source not in _SEARCH_SOURCE_KIND or capture is None):
        base["warnings"].append("missing_query_source_or_timestamp")
        return base
    base.update(status="candidates_unverified", query=query.strip(),
                fetched_at=capture, search_source=source)
    if source == "bing-fallback":
        base["warnings"].append("external_index_not_jd_ranking")
    elif source == "proxy":
        base["warnings"].append("third_party_proxy_not_authorized_jd_api")
    if len(results) > max_results:
        base["warnings"].append("result_limit_truncated")
    seen = {}
    for entry in results[:max_results]:
        if not isinstance(entry, dict):
            base["rejected_count"] += 1
            continue
        parsed = parse_jd_item_url(entry.get("url"))
        raw_sku = entry.get("sku")
        title = entry.get("title")
        entry_source = entry.get("source", source)
        if (parsed is None or not isinstance(raw_sku, str)
                or not _JD_ID.fullmatch(raw_sku)
                or raw_sku != parsed["platform_item_id"]
                or not isinstance(title, str) or not title.strip() or len(title) > 500
                or entry_source != source):
            base["rejected_count"] += 1
            continue
        key = raw_sku
        # 任何冲突候选都标 ambiguous，不能选第一个作为权威真值。
        if key in seen:
            prev = seen[key]
            if title != prev["displayed_title"] or entry_source != prev["discovery_source"]:
                prev["status"] = "conflicting_sources_unverified"
                prev["warnings"].append("duplicate_sku_conflicting_fields")
            continue
        candidate = {
            **parsed, "displayed_title": title.strip(),
            "seller_hint": entry.get("shopName") if isinstance(entry.get("shopName"), str) else None,
            "discovery_source": entry_source,
            "discovery_method": _SEARCH_SOURCE_KIND[entry_source],
            "source_id": f"jd-search-result:{source}:{raw_sku}",
            "observed_at": capture, "status": "discovered_unverified",
            "identity_verified": False, "quote_verified": False, "purchasable": False,
            "reference_price_present_but_not_verified": entry.get("price") is not None,
            "missing_fields": ["selected_model", "item_kind", "selected_variant",
                               "verified_seller", "region_stock", "shipping_and_discounts",
                               "authorized_live_quote"],
            "warnings": ["third_party_snapshot_not_official_platform_api"],
        }
        seen[key] = candidate
        base["items"].append(candidate)
    if not base["items"]:
        base["status"] = "no_valid_candidates"
    return base


def ingest_user_jd_item_link(url: str, *, observed_at: str,
                             now: datetime | None = None) -> dict:
    """用户主动提供的链接，供候选池使用；没有登录自动化和价格核验。"""
    current = now or datetime.now(timezone.utc)
    parsed = parse_jd_item_url(url)
    moment = _valid_time(observed_at, current) if current.tzinfo else None
    if parsed is None or moment is None:
        return {"status": "invalid_input", "purchasable": False}
    return {**parsed, "source_id": "user_supplied_link",
            "observed_at": moment, "status": "discovered_unverified",
            "identity_verified": False, "quote_verified": False,
            "purchasable": False, "transactions_enabled": False}
