"""多来源商品候选池：只汇总型号搜索线索，不更改购买决策。

接收已完成安全规范化的 JD 联盟、淘宝物料、用户手选京东链接三类报告。
同一京东 SKU 可以记录多个来源，但京东和淘宝绝不因数字 ID 相同而合并。
"""
from __future__ import annotations

from datetime import datetime, timezone
import re

from .listing_identity import _has_exact_anchor
from .discovery_ingest import parse_jd_item_url

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
    now: datetime | None = None, max_candidates: int = 30
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
    for report in reports:
        if not isinstance(report, dict):
            blocked_reports += 1
            continue
        mode = FORMATS.get(report.get("operation"))
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
                if item.get("canonical_url") != f"https://item.taobao.com/item.htm?id={product_id}":
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
    return {
        "operation": "merge_unverified_marketplace_leads",
        "status": "unverified_candidates_only",
        "candidate_count": len(items), "rejected_count": rejected,
        "blocked_report_count": blocked_reports, "candidates": items,
        "verified_quote_count": 0, "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "limitations": [
            "同一个SKU的来源汇总不代表卖家、套餐、地区或价格已获核实",
            "型号标题锚点仅帮助回查厂商规格；不证明是主机而非配件",
            "京东和淘宝平台商品标识永远不互换",
            "不同平台候选不构成价格/质量/销量排名，推荐门禁保持关闭",
        ],
    }
