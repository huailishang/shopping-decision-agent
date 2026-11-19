"""多来源商品候选池：只汇总型号搜索线索，不更改购买决策。

接收已完成安全规范化的 JD 联盟、淘宝物料、用户手选京东链接三类报告。
同一京东 SKU 可以记录多个来源，但京东和淘宝绝不因数字 ID 相同而合并。
"""
from __future__ import annotations

from datetime import datetime, timezone
import re

from .listing_identity import _has_exact_anchor
from .discovery_ingest import parse_jd_item_url, parse_taobao_item_url
from .model_identifiers import is_model_token

ID_RE = re.compile(r"[0-9]{5,20}")
FORMATS = {
    "offline_jd_union_response_import": ("JD_UNION_IMPORT_UNVERIFIED", "JD"),
    "offline_tbk_material_import": ("TAOBAO_TBK_IMPORT_UNVERIFIED", "TAOBAO"),
    "user_selected_marketplace_link_review": ("JD_PUBLIC_UNVERIFIED", "JD"),
}


def _is_recent_timestamp(value: object, now: datetime) -> bool:
    if not isinstance(value, str):
        return False
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return moment.tzinfo is not None and moment <= now
    except ValueError:
        return False


_HAINA_LEAD_FIELDS = frozenset((
    "source_id", "source_mode", "source_kind", "observed_at", "displayed_title",
    "brand_hint", "mall_hint", "mall_id_hint", "seller_hint", "seller_type_hint",
    "link_kind", "category_hint", "product_kind_status", "title_model_candidates",
    "spec_model_candidates", "spec_parse_status", "identity_status",
    "used_or_refurbished_hint", "bundle_or_variant_ambiguous_hint",
    "platform_item_id", "canonical_url", "status", "identity_verified",
    "quote_verified", "purchasable", "missing_fields",
))
_HAINA_HINT_FIELDS = ("brand_hint", "mall_hint", "seller_hint", "seller_type_hint", "category_hint", "mall_id_hint")
# 线索标签只允许描述文字，不能作为推广链接/追踪参数的透传通道。
_HAINA_LINK_TEXT = re.compile(
    r"(?:https?://|(?<!\w)www\.|(?<!\w)(?:s\.click\.taobao\.com|union-click\.jd\.com)|"
    r"[?&](?:utm_[\w]+|tracking|click_id|aff_id)=|%3a%2f%2f)", re.IGNORECASE
)
_HAINA_LINK_KINDS = frozenset((
    "missing", "invalid", "jd_promotion_redirect", "taobao_promotion_redirect",
    "platform_detail_host_only_unverified", "other_or_unknown_host",
))
_HAINA_PRODUCT_STATUSES = frozenset((
    "likely_accessory_or_consumable", "printer_host_candidate",
    "printer_host_title_category_unconfirmed", "product_kind_unknown",
))
_HAINA_IDENTITY_STATUSES = frozenset((
    "title_spec_model_conflict", "multiple_model_or_option_ambiguous",
    "manufacturer_model_candidate_only", "spec_model_only_title_unconfirmed",
    "title_model_only_unverified", "model_not_confirmed",
))
def _valid_haina_lead(row: dict, now: datetime) -> bool:
    """导入报告也属于不可信输入；逐字段验证，拒绝嵌套对象与越界值。"""
    if not set(row).issubset(_HAINA_LEAD_FIELDS):
        return False
    if (row.get("source_mode") != "synthetic_test"
            or row.get("source_kind") != "haina_product_search_pro"
            or row.get("status") != "source_lead_only"
            or row.get("platform_item_id") is not None
            or row.get("canonical_url") is not None
            or row.get("identity_verified") is not False
            or row.get("quote_verified") is not False
            or row.get("purchasable") is not False
            or not _is_recent_timestamp(row.get("observed_at"), now)):
        return False
    if (not isinstance(row.get("source_id"), str)
            or re.fullmatch(r"haina-synthetic-row:[0-9]{3}", row["source_id"]) is None
            or not isinstance(row.get("displayed_title"), str)
            or not row["displayed_title"].strip()
            or len(row["displayed_title"]) > 500
            or _HAINA_LINK_TEXT.search(row["displayed_title"])):
        return False
    if any(row.get(k) is not None and (
        not isinstance(row[k], str) or len(row[k]) > 120 or _HAINA_LINK_TEXT.search(row[k])
    ) for k in _HAINA_HINT_FIELDS):
        return False
    if (not isinstance(row.get("link_kind"), str)
            or not isinstance(row.get("product_kind_status"), str)
            or not isinstance(row.get("identity_status"), str)
            or row["link_kind"] not in _HAINA_LINK_KINDS
            or row["product_kind_status"] not in _HAINA_PRODUCT_STATUSES
            or row["identity_status"] not in _HAINA_IDENTITY_STATUSES):
        return False
    for key in ("title_model_candidates", "spec_model_candidates"):
        items = row.get(key)
        if (not isinstance(items, list) or len(items) > 10
                or any(not is_model_token(x) for x in items)):
            return False
    return (type(row.get("used_or_refurbished_hint")) is bool
            and type(row.get("bundle_or_variant_ambiguous_hint")) is bool)


def _known_title_models(titles: list[str], known_aliases: dict) -> tuple[str | None, str]:
    if not titles:
        return None, "no_title_source"
    found = set()
    for model_id, aliases in known_aliases.items():
        if not isinstance(aliases, (list, tuple)):
            continue
        for title in titles:
            if any(isinstance(a, str) and a and _has_exact_anchor(title, a)
                   for a in aliases):
                found.add(model_id)
    if len(found) == 1:
        return next(iter(found)), "title_anchor_only_unverified"
    if found:
        return None, "conflicting_model_title_anchors"
    return None, "model_not_in_verified_registry"


def build_discovery_pool(
    reports: list[dict], *, known_aliases: dict | None = None,
    now: datetime | None = None, max_candidates: int = 30,
    sale_configuration_report: dict | None = None
) -> dict:
    """去重并关联型号候选。不会批准价格、库存、图片或交易。"""
    current = now or datetime.now(timezone.utc)
    if (not isinstance(reports, list) or len(reports) > 10
            or not isinstance(known_aliases if known_aliases is not None else {}, dict)
            or current.tzinfo is None or type(max_candidates) is not int
            or not 1 <= max_candidates <= 50):
        raise ValueError("discovery_pool_input_invalid")
    known_aliases = known_aliases or {}
    grouped = {}
    rejected = 0
    blocked_reports = 0
    unverified_source_leads = []
    for report in reports:
        if not isinstance(report, dict):
            blocked_reports += 1
            continue
        if report.get("operation") == "haina_product_search_offline_ingest":
            if (report.get("source") != "haina_product_search_pro"
                    or report.get("source_mode") != "synthetic_test"
                    or report.get("status") != "source_leads_unverified"):
                blocked_reports += 1
                continue
            rows = report.get("items")
            if not isinstance(rows, list) or len(rows) > 20:
                blocked_reports += 1
                continue
            for row in rows:
                if not isinstance(row, dict) or not _valid_haina_lead(row, current):
                    rejected += 1
                    continue
                title = row["displayed_title"]
                unverified_source_leads.append({
                    "source_id": row.get("source_id"),
                    "source_mode": "synthetic_test",
                    "displayed_title": title,
                    "brand_hint": row.get("brand_hint"),
                    "mall_hint": row.get("mall_hint"),
                    "seller_hint": row.get("seller_hint"),
                    "seller_type_hint": row.get("seller_type_hint"),
                    "link_kind": row.get("link_kind"),
                    "product_kind_status": row.get("product_kind_status"),
                    "title_model_candidates": row.get("title_model_candidates", []),
                    "spec_model_candidates": row.get("spec_model_candidates", []),
                    "identity_status": row.get("identity_status"),
                    "used_or_refurbished_hint": bool(row.get("used_or_refurbished_hint")),
                    "bundle_or_variant_ambiguous_hint": bool(row.get("bundle_or_variant_ambiguous_hint")),
                    "observed_at": row.get("observed_at"),
                    "status": "source_lead_only_not_platform_candidate",
                    "platform_item_id": None,
                    "identity_verified": False,
                    "quote_verified": False,
                    "purchasable": False,
                })
            continue
        mode = FORMATS.get(report.get("operation"))
        if report.get("operation") == "user_selected_marketplace_link_review" and report.get("marketplace_platform") == "taobao":
            mode = ("TAOBAO_PUBLIC_UNVERIFIED", "TAOBAO")
        if mode is None or report.get("status") != "candidates_unverified":
            blocked_reports += 1
            continue
        required_platform, shared_platform = mode
        rows = report.get("candidates") if report.get("operation") == "user_selected_marketplace_link_review" else report.get("items")
        if not isinstance(rows, list) or len(rows) > 100:
            blocked_reports += 1
            continue
        for item in rows:
            if not isinstance(item, dict):
                rejected += 1
                continue
            product_id = item.get("platform_item_id")
            if (item.get("platform") != required_platform or not isinstance(product_id, str)
                    or not ID_RE.fullmatch(product_id)
                    or not _is_recent_timestamp(item.get("observed_at"), current)):
                rejected += 1
                continue
            if shared_platform == "JD":
                url = parse_jd_item_url(item.get("canonical_url"))
                if url is None or url["platform_item_id"] != product_id:
                    rejected += 1
                    continue
            else:
                if required_platform == "TAOBAO_PUBLIC_UNVERIFIED":
                    link = parse_taobao_item_url(item.get("canonical_url"))
                    if link is None or link["platform_item_id"] != product_id:
                        rejected += 1
                        continue
                elif item.get("canonical_url") != f"https://item.taobao.com/item.htm?id={product_id}":
                    rejected += 1
                    continue
            key = (shared_platform, product_id)
            if key not in grouped and len(grouped) >= max_candidates:
                rejected += 1
                continue
            entry = grouped.setdefault(key, {
                "platform": shared_platform, "platform_item_id": product_id,
                "canonical_url": item["canonical_url"], "model_hint": None,
                "model_hint_status": "not_checked", "title_hints": [],
                "provenance": [], "status": "unverified_sales_lead",
                "identity_verified": False, "quote_verified": False,
                "live_price_cny": None, "purchasable": False,
                "within_budget": None,
                "missing_fields": [
                    "product_kind", "selected_variant", "verified_seller",
                    "delivery_region", "regional_stock", "shipping_promotions",
                    "authorized_live_quote", "warranty_and_compatibility",
                ],
            })
            title = item.get("displayed_title")
            if isinstance(title, str) and title and len(title) <= 500 and title not in entry["title_hints"]:
                entry["title_hints"].append(title)
            entry["provenance"].append({
                "source_platform": required_platform,
                "source_operation": report["operation"],
                "source_id": item.get("source_id"),
                "observed_at": item.get("observed_at"),
                "source_assurance": item.get("source_assurance", "unverified_user_link"),
                "status": item.get("status", "unknown"),
            })
    items = list(grouped.values())
    for item in items:
        item["model_hint"], item["model_hint_status"] = _known_title_models(
            item["title_hints"], known_aliases)
        if (item["model_hint_status"] == "conflicting_model_title_anchors" or
                any(p["status"] in ("conflicting_snapshot_entries",
                                    "conflicting_identifiers_unverified",
                                    "conflicting_sources_unverified")
                    for p in item["provenance"])):
            item["status"] = "needs_identity_conflict_review"
    result = {
        "operation": "merge_unverified_marketplace_leads",
        "status": "unverified_candidates_only",
        "candidate_count": len(items), "rejected_count": rejected,
        "blocked_report_count": blocked_reports, "candidates": items,
        "unverified_source_lead_count": len(unverified_source_leads),
        "unverified_source_leads": unverified_source_leads,
        "verified_quote_count": 0, "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "limitations": [
            "同一个SKU的来源汇总不代表卖家、套餐、地区或价格已获核实",
            "型号标题锚点仅帮助回查厂商规格；不证明是主机而非配件",
            "京东和淘宝平台商品标识永远不互换",
            "无平台商品ID的海纳线索单独展示，不进入平台候选池或价格比较",
            "不同平台候选不构成价格/质量/销量排名，推荐门禁保持关闭",
        ],
    }
    if sale_configuration_report is not None:
        # 合成配置证据在池中另设隔离区，不计入已核平台候选或报价。
        from .sale_configuration_evidence import assess_sale_evidence_report
        result["sale_configuration_evidence"] = assess_sale_evidence_report(
            sale_configuration_report, now=current)
    return result
