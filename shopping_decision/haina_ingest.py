"""海纳商品检索 Pro 的受控离线线索导入。

真实响应用途许可尚未核准；当前只允许合成测试数据进入解析器。
本模块不发网络请求、不保留推广URL/价格/评价分数，也不生成平台商品ID。
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from urllib.parse import urlsplit

from .model_identifiers import extract_model_tokens

SOURCE_KIND = "haina_product_search_pro"
REAL_RESPONSE_IMPORT_ENABLED = False
MAX_ROWS = 20
MAX_PAYLOAD_BYTES = 200_000
_SPEC_MODEL_KEYS = frozenset(("认证型号", "型号", "能效网规格型号", "国补备案型号"))
_ACCESSORY_HINTS = ("硒鼓", "墨粉", "粉盒", "鼓架", "打印纸", "标签纸", "连接线", "打印服务器", "墨水", "碳粉", "配件")
_USED_HINTS = ("二手", "拆机", "翻新", "维修机", "官翻")
_BUNDLE_HINTS = ("套餐", "套装", "加小白盒", "组合", "颜色分类", "多型号", "可选")


def _valid_observed_at(value: object, now: datetime) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None or moment > now or moment.year < 2020:
        return None
    return moment.astimezone(timezone.utc).isoformat()


def _model_tokens(value: object) -> list[str]:
    return extract_model_tokens(value)


def _spec_model_tokens(value: object) -> list[str]:
    found: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for key, child in node.items():
                if key in _SPEC_MODEL_KEYS and isinstance(child, str):
                    found.update(_model_tokens(child))
                else:
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return sorted(found)


def _parse_spec(value: object) -> tuple[dict | None, str]:
    if isinstance(value, dict):
        return value, "parsed_object"
    if not isinstance(value, str) or not value.strip() or len(value) > 50_000:
        return None, "missing_or_invalid"
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None, "invalid_json"
    return (parsed, "parsed_json") if isinstance(parsed, dict) else (None, "unexpected_shape")


def _link_kind(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        return "missing"
    try:
        host = (urlsplit(value).hostname or "").lower()
    except ValueError:
        return "invalid"
    if host == "union-click.jd.com":
        return "jd_promotion_redirect"
    if host == "s.click.taobao.com":
        return "taobao_promotion_redirect"
    if host in ("item.jd.com", "item.m.jd.com", "item.taobao.com", "detail.tmall.com"):
        return "platform_detail_host_only_unverified"
    return "other_or_unknown_host"


def _classify_host(title: str, category: object) -> str:
    if any(word in title for word in _ACCESSORY_HINTS):
        return "likely_accessory_or_consumable"
    if "打印机" in title and isinstance(category, str) and "打印机" in category:
        return "printer_host_candidate"
    if "打印机" in title:
        return "printer_host_title_category_unconfirmed"
    return "product_kind_unknown"


def _identity_status(title_models: list[str], spec_models: list[str]) -> str:
    if title_models and spec_models and not set(title_models).intersection(spec_models):
        return "title_spec_model_conflict"
    if len(title_models) > 1 or len(spec_models) > 1:
        return "multiple_model_or_option_ambiguous"
    if len(spec_models) == 1 and len(title_models) == 1:
        return "manufacturer_model_candidate_only"
    if len(spec_models) == 1:
        return "spec_model_only_title_unconfirmed"
    if len(title_models) == 1:
        return "title_model_only_unverified"
    return "model_not_confirmed"


def ingest_haina_product_search(
    payload: dict,
    *,
    observed_at: str,
    source_mode: str = "synthetic_test",
    now: datetime | None = None,
    max_results: int = MAX_ROWS,
) -> dict:
    """将合成海纳响应转换为待核线索；真实响应在用途许可核准前一律阻断。"""
    base = {
        "operation": "haina_product_search_offline_ingest",
        "source": SOURCE_KIND,
        "source_mode": source_mode,
        "status": "invalid_input",
        "items": [],
        "input_rows": 0,
        "imported_leads": 0,
        "rejected_count": 0,
        "warnings": [],
        "verified_platform_id_count": 0,
        "verified_quote_count": 0,
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
    }
    if source_mode == "real_response" and not REAL_RESPONSE_IMPORT_ENABLED:
        base.update(status="blocked_real_data_use_not_approved")
        base["warnings"].append("haina_usage_terms_not_verified_real_response_not_processed")
        return base
    if source_mode != "synthetic_test":
        base["warnings"].append("unsupported_source_mode")
        return base
    if (not isinstance(payload, dict) or type(max_results) is not int
            or not 1 <= max_results <= MAX_ROWS):
        base["warnings"].append("invalid_payload_or_limit")
        return base
    try:
        payload_size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError):
        base["warnings"].append("payload_not_json_serializable")
        return base
    if payload_size > MAX_PAYLOAD_BYTES:
        base["warnings"].append("payload_too_large")
        return base
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        base["warnings"].append("invalid_reference_time")
        return base
    capture = _valid_observed_at(observed_at, current)
    if capture is None:
        base["warnings"].append("missing_or_invalid_observed_at")
        return base
    if type(payload.get("error_code")) is not int or payload.get("error_code") != 0:
        base.update(status="api_error")
        base["warnings"].append("provider_business_error")
        return base
    data = payload.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list) or len(rows) > 100:
        base["warnings"].append("invalid_rows_shape")
        return base

    base.update(status="source_leads_unverified", observed_at=capture, input_rows=len(rows))
    if len(rows) > max_results:
        base["warnings"].append("result_limit_truncated")
    for index, row in enumerate(rows[:max_results], 1):
        if not isinstance(row, dict):
            base["rejected_count"] += 1
            continue
        title = row.get("title")
        if not isinstance(title, str) or not title.strip() or len(title) > 500:
            base["rejected_count"] += 1
            continue
        spec, spec_parse_status = _parse_spec(row.get("union_spec"))
        title_models = _model_tokens(title)
        spec_models = _spec_model_tokens(spec)
        shop_name = row.get("shop_name")
        shop_type = row.get("shop_type")
        mall_name = row.get("mall_name")
        mall_id = row.get("mall_id")
        category = row.get("cate3_name")
        used_hint = any(word in title for word in _USED_HINTS) or (
            isinstance(shop_name, str) and any(word in shop_name for word in _USED_HINTS)
        )
        bundle_hint = any(word in title for word in _BUNDLE_HINTS)
        lead = {
            "source_id": f"haina-synthetic-row:{index:03d}",
            "source_mode": "synthetic_test",
            "source_kind": SOURCE_KIND,
            "observed_at": capture,
            "displayed_title": title.strip(),
            "brand_hint": row.get("brand_name") if isinstance(row.get("brand_name"), str) else None,
            "mall_hint": mall_name if isinstance(mall_name, str) else None,
            "mall_id_hint": str(mall_id) if mall_id is not None else None,
            "seller_hint": shop_name if isinstance(shop_name, str) else None,
            "seller_type_hint": shop_type if isinstance(shop_type, str) else None,
            "link_kind": _link_kind(row.get("url")),
            "category_hint": category if isinstance(category, str) else None,
            "product_kind_status": _classify_host(title, category),
            "title_model_candidates": title_models,
            "spec_model_candidates": spec_models,
            "spec_parse_status": spec_parse_status,
            "identity_status": _identity_status(title_models, spec_models),
            "used_or_refurbished_hint": used_hint,
            "bundle_or_variant_ambiguous_hint": bundle_hint,
            "platform_item_id": None,
            "canonical_url": None,
            "status": "source_lead_only",
            "identity_verified": False,
            "quote_verified": False,
            "purchasable": False,
            "missing_fields": [
                "stable_platform_item_id",
                "selected_model_and_variant_binding",
                "seller_and_newness_verification",
                "host_or_accessory_verification",
                "authorized_live_quote",
                "delivery_region_and_stock",
                "shipping_and_discount_eligibility",
                "official_model_fact_binding",
            ],
        }
        base["items"].append(lead)
    base["imported_leads"] = len(base["items"])
    if not base["items"]:
        base["status"] = "no_valid_source_leads"
    base["limitations"] = [
        "当前只接受合成测试输入；真实海纳响应因用途许可未核准而阻断",
        "推广跳转URL只识别链接类型，不保存URL、不解析参数、不猜平台商品ID",
        "价格、历史价、评论汇总、搜索score和图片字段不导入",
        "型号/店铺/类别均是待核线索，不等于平台销售项身份或厂商事实",
    ]
    return base
