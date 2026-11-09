"""淘宝联盟 `taobao.tbk.dg.material.optional` 的离线只读响应导入。

不联网、不授权、不计算到手价。只信官方当前文档中的 item_id，
不再用已标注废弃的 num_iid 充当商品主键。
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

METHOD = "taobao.tbk.dg.material.optional"
WRAPPER = "tbk_dg_material_optional_response"
_ITEM_ID = re.compile(r"[0-9]{5,20}")
MAX_BYTES = 256_000


def _id(value) -> str | None:
    if type(value) is int:
        value = str(value)
    return value if isinstance(value, str) and _ITEM_ID.fullmatch(value) else None


def _observed(value: str, now: datetime | None) -> datetime:
    if not isinstance(value, str):
        raise ValueError("invalid_observation")
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        current = now or datetime.now(timezone.utc)
        if moment.tzinfo is None or current.tzinfo is None or moment > current or moment.year < 2000:
            raise ValueError("invalid_observation")
    except ValueError as exc:
        raise ValueError("invalid_observation") from exc
    return moment.astimezone(timezone.utc)


def _item_link_id(url: str) -> str | None:
    if not isinstance(url, str) or not url or len(url) > 2048:
        return None
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname not in
                ("item.taobao.com", "detail.tmall.com") or parsed.port is not None
                or parsed.username or parsed.password or parsed.path != "/item.htm"):
            return None
        values = parse_qs(parsed.query, strict_parsing=False).get("id")
        if not values or len(values) != 1:
            return None
        return _id(values[0])
    except ValueError:
        return None


def import_tbk_material_snapshot(
    response: dict, *, keyword: str, observed_at: str,
    now: datetime | None = None, max_items: int = 10
) -> dict:
    """标准化获准取得的淘宝物料搜索快照；来源真实性需独立复核。"""
    result = {
        "operation": "offline_tbk_material_import",
        "platform": "TAOBAO_TBK_IMPORT_UNVERIFIED",
        "status": "invalid_response", "items": [], "rejected_count": 0,
        "warnings": [], "authorized_api_calls": 0,
        "verified_quote_count": 0, "purchase_recommendation_approved": False,
        "transactions_enabled": False,
    }
    if (not isinstance(response, dict) or not isinstance(keyword, str)
            or not keyword.strip() or len(keyword.strip()) > 100
            or type(max_items) is not int or not 1 <= max_items <= 20):
        result["warnings"].append("invalid_input")
        return result
    try:
        stamp = _observed(observed_at, now)
    except ValueError:
        result["warnings"].append("invalid_observed_at")
        return result
    result.update(keyword=keyword.strip(), observed_at=stamp.isoformat(),
                  source_assurance="offline_import_not_platform_authorization",
                  provenance_sha256=hashlib.sha256(
                      json.dumps(response, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":")).encode("utf-8")).hexdigest())
    if "error_response" in response:
        result.update(status="api_error", warnings=["tbk_gateway_error"])
        return result
    wrapper = response.get(WRAPPER)
    if not isinstance(wrapper, dict):
        result["warnings"].append("missing_material_wrapper")
        return result
    list_wrapper = wrapper.get("result_list")
    if not isinstance(list_wrapper, dict) or not isinstance(list_wrapper.get("map_data"), list):
        result["warnings"].append("material_map_data_missing")
        return result
    goods = list_wrapper["map_data"]
    if len(goods) > 100:
        result["warnings"].append("too_many_material_rows")
        return result
    if len(goods) > max_items:
        result["warnings"].append("sample_truncated")
    seen = {}
    for row in goods[:max_items]:
        if not isinstance(row, dict):
            result["rejected_count"] += 1
            continue
        # num_iid 从最新官方接口文档已废弃；绝不降级到它作为 item_id。
        item_id = _id(row.get("item_id"))
        title = row.get("title")
        if item_id is None or not isinstance(title, str) or not title.strip() or len(title) > 500:
            result["rejected_count"] += 1
            continue
        seller = row.get("shop_title")
        seller = seller[:100] if isinstance(seller, str) else None
        if item_id in seen:
            if seen[item_id]["displayed_title"] != title.strip() or seen[item_id]["seller_hint"] != seller:
                seen[item_id]["status"] = "conflicting_snapshot_entries"
                seen[item_id]["warnings"].append("duplicate_item_conflict")
            continue
        warnings = ["promotion_material_pool_not_all_taobao_products"]
        status = "discovered_unverified"
        legacy = _id(row.get("num_iid"))
        if legacy is not None and legacy != item_id:
            warnings.append("deprecated_num_iid_conflicts_with_item_id")
            status = "conflicting_identifiers_unverified"
        page_link = row.get("item_url")
        if page_link is not None:
            link_id = _item_link_id(page_link)
            if link_id is None or link_id != item_id:
                warnings.append("item_url_not_matching_item_id")
                status = "conflicting_identifiers_unverified"
        output = {
            "platform": "TAOBAO_TBK_IMPORT_UNVERIFIED",
            "platform_namespace": "TAOBAO_TBK",
            "platform_item_id": item_id,
            "canonical_url": f"https://item.taobao.com/item.htm?id={item_id}",
            "displayed_title": title.strip(), "seller_hint": seller,
            "seller_id_hint": str(row["seller_id"]) if type(row.get("seller_id")) in (str, int) else None,
            "source_id": f"tbk_material_snapshot:{item_id}",
            "observed_at": stamp.isoformat(),
            "source_assurance": "unverified_imported_snapshot",
            "status": status, "identity_verified": False,
            "quote_verified": False, "purchasable": False,
            "reference_price_present_but_not_verified": (
                row.get("zk_final_price") is not None or row.get("reserve_price") is not None),
            "missing_fields": [
                "selected_model", "selected_variant", "verified_seller",
                "delivery_region_stock", "applicable_discounts",
                "authorized_fresh_quote", "shipping_and_service",
            ],
            "warnings": warnings,
        }
        seen[item_id] = output
        result["items"].append(output)
    result["status"] = "candidates_unverified" if result["items"] else "no_valid_candidates"
    if ((now or datetime.now(timezone.utc)) - stamp).total_seconds() > 86400:
        result["warnings"].append("snapshot_over_one_day_old")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="仅离线读取已合法取得的淘宝客物料响应，不调用API")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    path = Path(args.snapshot)
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        parser.error("snapshot_missing_or_too_large")
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        parser.error("snapshot_invalid_json")
    output = import_tbk_material_snapshot(
        body, keyword=args.keyword, observed_at=args.observed_at)
    safe = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(safe, encoding="utf-8")
    print(safe, end="")


if __name__ == "__main__":
    main()
