"""海纳 MCP 多工具响应的受控离线适配器。

当前只接受 synthetic_test。真实响应在用途许可核准前一律阻断。
供应商 SPU/SKU/商品ID不是京东/淘宝平台ID；供应商报价和评论摘要
只作为待核线索，绝不进入实时价格、独立评测或购买批准。
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit

from .model_identifiers import extract_model_tokens

REAL_MCP_IMPORT_ENABLED = False
MAX_REPORT_BYTES = 200_000
SYNTHETIC_FIXTURE_PATH = (Path(__file__).resolve().parent.parent /
                          "tests/fixtures/haina_mcp_synthetic_bundle.json")
SYNTHETIC_FIXTURE_SHA256 = "bd1de6e313b6fcfd854e53287e5a2d91363a9c697790e984c7a5df97cd61db0d"
MAX_CALLS = 12
MAX_ENTITIES_PER_CALL = 5
MAX_PRODUCTS_PER_SKU = 20
_ALLOWED_TOOLS = frozenset({
    "product_sku_search",
    "product_basic_search",
    "product_parameter_search",
    "product_comment_search",
})
_ALLOWED_REPORT_KEYS = frozenset({"schema_version", "operation", "source_mode", "calls"})
_ALLOWED_CALL_KEYS = frozenset({"tool", "query", "observed_at", "payload"})
_ACCESSORY_HINTS = ("硒鼓", "墨粉", "粉盒", "鼓架", "打印纸", "标签纸", "墨水", "碳粉", "配件", "连接线")
_USED_HINTS = ("二手", "拆机", "翻新", "维修机", "官翻")
_BUNDLE_HINTS = ("套装", "套餐", "多型号", "多规格", "可选型号", "随机型号")


def _text(value: object, limit: int = 500) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > limit:
        return None
    if any(ord(ch) < 32 and ch not in "\n\t\r" for ch in value):
        return None
    return value


def _first_text(row: dict, keys: tuple[str, ...], limit: int = 500) -> str | None:
    for key in keys:
        value = _text(row.get(key), limit)
        if value is not None:
            return value
    return None


def _safe_string_list(value: object, *, limit: int = 20, text_limit: int = 500) -> list[str]:
    if not isinstance(value, list):
        return []
    output = []
    for item in value[:limit]:
        text = _text(item, text_limit)
        if text is not None and text not in output:
            output.append(text)
    return output


def _safe_string_map(value: object, *, limit: int = 20) -> dict[str, str]:
    if not isinstance(value, dict) or len(value) > limit:
        return {}
    result = {}
    for key, item in value.items():
        k, v = _text(key, 80), _text(item, 200)
        if k is not None and v is not None:
            result[k] = v
    return result


def _safe_provider_id(value: object) -> str | None:
    return _text(value, 100)


def _safe_for_size_check(value: object, depth: int = 0) -> object:
    """为 200KB 输入预算计数保留坏整数的近似字节量，不触发 Python 大整数转十进制限制。

    返回副本仅用于检查大小；原始内容仍由各行字段解析并拒绝异常值。
    """
    if depth > 16:
        raise ValueError("deep_provider_payload")
    if type(value) is int and value.bit_length() > 100:
        # 十进制位数的安全上界；不调用str(巨整数)。
        digits = value.bit_length() * 30103 // 100000 + 2
        if digits > MAX_REPORT_BYTES:
            raise ValueError("oversized_provider_integer")
        return "0" * digits
    if type(value) is float and not math.isfinite(value):
        return "non_finite_provider_number"
    if isinstance(value, list):
        if len(value) > 20_000:
            raise ValueError("provider_payload_list_too_large")
        return [_safe_for_size_check(x, depth + 1) for x in value]
    if isinstance(value, dict):
        if len(value) > 20_000:
            raise ValueError("provider_payload_object_too_large")
        return {k: _safe_for_size_check(v, depth + 1) for k, v in value.items()}
    return value


def _provider_price_hint(value: object) -> str | None:
    if isinstance(value, str):
        raw = _text(value, 60)
        if raw is None or not re.fullmatch(r"(?:¥|￥)?\s*[0-9]{1,10}(?:\.[0-9]{1,2})?", raw):
            return None
        # 供应商价格只是线索；此处验语法/上限而不是算平台地区实价。
        from decimal import Decimal
        return raw if Decimal(raw.lstrip("¥￥").strip()) <= 10_000_000_000 else None
    # 巨整数转换 float 会触发 OverflowError；供应商坏报价不得损坏其他好线索。
    if type(value) is int:
        return str(value) if 0 <= value <= 10_000_000_000 else None
    if type(value) is float and math.isfinite(value) and 0 <= value <= 10_000_000_000:
        return str(value)
    return None


def _url_host_only(value: object) -> str | None:
    raw = _text(value, 4096)
    if raw is None:
        return None
    try:
        parsed = urlsplit(raw)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return None
        host = parsed.hostname.lower()
        if len(host) > 253 or any(not part for part in host.split(".")):
            return None
        return host
    except ValueError:
        return None


def _collect_model_text(value: object, *, depth: int = 0) -> str:
    if depth > 5:
        return ""
    if isinstance(value, str):
        return value[:4000]
    if isinstance(value, dict):
        return " ".join(_collect_model_text(k, depth=depth + 1) + " " +
                        _collect_model_text(v, depth=depth + 1)
                        for k, v in list(value.items())[:30])
    if isinstance(value, list):
        return " ".join(_collect_model_text(v, depth=depth + 1) for v in value[:30])
    return ""


def _parse_spec(value: object) -> object:
    if isinstance(value, (dict, list)):
        return value
    raw = _text(value, 20_000)
    if raw is None:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, (dict, list)) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def _identity_status(query: str, entity_name: str, title: str,
                     axes: dict, spec: object, sku_prop: str | None) -> tuple[list[str], list[str], str]:
    query_models = extract_model_tokens(query)
    entity_models = extract_model_tokens(entity_name)
    title_models = extract_model_tokens(title)
    spec_text = " ".join((sku_prop or "", _collect_model_text(axes),
                          _collect_model_text(_parse_spec(spec))))
    spec_models = extract_model_tokens(spec_text)
    if len(query_models) > 1 or len(entity_models) > 1 or len(title_models) > 1 or len(spec_models) > 1:
        return title_models, spec_models, "multiple_model_or_variant_ambiguous"
    target = query_models or entity_models
    if target and title_models and target[0] != title_models[0]:
        return title_models, spec_models, "entity_title_model_conflict"
    if title_models and spec_models and title_models[0] != spec_models[0]:
        return title_models, spec_models, "title_spec_model_conflict"
    if len(title_models) == 1:
        return title_models, spec_models, "title_model_candidate_only"
    if len(spec_models) == 1:
        return title_models, spec_models, "spec_model_candidate_only"
    if len(target) == 1:
        return title_models, spec_models, "query_model_only_not_listing"
    return title_models, spec_models, "model_not_confirmed"


def _product_kind(title: str) -> str:
    if any(word in title for word in _ACCESSORY_HINTS):
        return "likely_accessory_or_consumable"
    if "打印机" in title or "一体机" in title:
        return "printer_host_candidate"
    return "product_kind_unknown"


def _entity_bucket(buckets: dict, query: str, entity_name: str, observed_at: str) -> dict:
    key = (query, entity_name)
    if key not in buckets:
        buckets[key] = {
            "query": query,
            "entity_name": entity_name,
            "first_observed_at": observed_at,
            "sources": [],
            "basic_facts": [],
            "parameters": [],
            "opinion_summaries": [],
            "sale_leads": [],
            "count_audits": [],
        }
    return buckets[key]


def _record_source(bucket: dict, tool: str, observed_at: str) -> None:
    entry = {"tool": tool, "observed_at": observed_at, "source_mode": "synthetic_test",
             "assurance": "provider_return_unverified"}
    if entry not in bucket["sources"]:
        bucket["sources"].append(entry)


def _parse_sku_entity(bucket: dict, row: dict, query: str, call_index: int,
                      entity_index: int, observed_at: str) -> int:
    sku_result = row.get("sku_result")
    if not isinstance(sku_result, dict):
        return 1
    spu_id = _safe_provider_id(sku_result.get("spu_id"))
    bucket["supplier_spu_name_hint"] = _first_text(sku_result, ("spu_name",), 200)
    sku_list = sku_result.get("sku_list")
    if not isinstance(sku_list, list) or len(sku_list) > 20:
        return 1
    reported_sku_count = sku_result.get("sku_count")
    reported_sku_count = (reported_sku_count if type(reported_sku_count) is int
                          and 0 <= reported_sku_count <= 100_000 else None)
    bucket["count_audits"].append({
        "kind": "sku_count", "reported_count": reported_sku_count,
        "observed_count": len(sku_list),
        "count_matches": (reported_sku_count == len(sku_list)
                          if reported_sku_count is not None else None),
    })
    rejected = 0
    if not sku_list:
        # 空SKU是实体研究线索，不是一个可销售商品；保持独立空结果标记。
        bucket["sku_empty_result_count"] = bucket.get("sku_empty_result_count", 0) + 1
    for sku_index, sku in enumerate(sku_list, start=1):
        if not isinstance(sku, dict):
            rejected += 1
            continue
        sku_id = _safe_provider_id(sku.get("sku_id"))
        axes = _safe_string_map(sku.get("sku_axes"))
        products = sku.get("sku_products")
        if not isinstance(products, list) or len(products) > MAX_PRODUCTS_PER_SKU:
            rejected += 1
            continue
        reported_product_count = sku.get("sku_products_count")
        reported_product_count = (reported_product_count if type(reported_product_count) is int
                                  and 0 <= reported_product_count <= 100_000 else None)
        bucket["count_audits"].append({
            "kind": "sku_products_count", "sku_id_present": sku_id is not None,
            "reported_count": reported_product_count, "observed_count": len(products),
            "count_matches": (reported_product_count == len(products)
                              if reported_product_count is not None else None),
        })
        for product_index, product in enumerate(products, start=1):
            if not isinstance(product, dict):
                rejected += 1
                continue
            title = _first_text(product, ("title",), 500) or ""
            mall = _first_text(product, ("mall_name",), 120)
            shop = _first_text(product, ("shop_name",), 160)
            shop_type = _first_text(product, ("shop_type",), 80)
            sku_prop = _first_text(product, ("sku_prop",), 300)
            spec = product.get("union_spec") if product.get("union_spec") is not None else product.get("spec_detail")
            title_models, spec_models, identity = _identity_status(
                query, bucket["entity_name"], title, axes, spec, sku_prop)
            used_hint = any(word in title for word in _USED_HINTS)
            bundle_hint = (any(word in title for word in _BUNDLE_HINTS)
                           or (len(products) > 1 and not axes))
            lead = {
                "source_id": f"haina-mcp-synthetic:{call_index:02d}:{entity_index:02d}:{sku_index:02d}:{product_index:02d}",
                "supplier_spu_id": spu_id,
                "supplier_sku_id": sku_id,
                "supplier_product_id": _safe_provider_id(product.get("id")),
                "supplier_ids_are_platform_ids": False,
                "platform_item_id": None,
                "title": title or None,
                "title_model_candidates": title_models,
                "spec_model_candidates": spec_models,
                "identity_status": identity,
                "product_kind_status": _product_kind(title),
                "used_or_refurbished_hint": used_hint,
                "bundle_or_variant_ambiguous_hint": bundle_hint,
                "sku_axes_hint": axes,
                "sku_prop_hint": sku_prop,
                "mall_hint": mall,
                "seller_hint": shop,
                "seller_type_hint": shop_type,
                "link_host": _url_host_only(product.get("url")),
                "supplier_price_hint": _provider_price_hint(product.get("final_price")),
                "quote_status": "provider_price_hint_unverified",
                "quote_verified": False,
                "live_price_cny": None,
                "purchasable": False,
                "status": "source_lead_only",
                "observed_at": observed_at,
            }
            bucket["sale_leads"].append(lead)
    return rejected


def _parse_basic_entity(bucket: dict, row: dict, observed_at: str) -> int:
    description = _first_text(row, ("entity_description", "description", "summary", "content"), 1200)
    brand = _first_text(row, ("brand_name", "brand"), 120)
    entity_type = _first_text(row, ("entity_type", "category", "type"), 120)
    features = _safe_string_list(row.get("features", row.get("feature_list")), limit=20, text_limit=300)
    if description or brand or entity_type or features:
        bucket["basic_facts"].append({
            "brand_hint": brand,
            "entity_type_hint": entity_type,
            "description_hint": description,
            "feature_hints": features,
            "observed_at": observed_at,
            "trust_label": "provider_basic_description_unverified",
        })
        return 0
    return 1


def _parse_parameter_entity(bucket: dict, row: dict, observed_at: str) -> int:
    values = row.get("entity_parameter", row.get("entity_parameters", row.get("parameters")))
    if not isinstance(values, list) or len(values) > 30:
        return 1
    rejected = 0
    for item in values:
        if not isinstance(item, dict):
            rejected += 1
            continue
        name = _first_text(item, ("parameter_name", "param_name", "name", "key", "attribute_name"), 120)
        value = _first_text(item, ("parameter_value", "param_value", "value", "attribute_value"), 300)
        description = _first_text(item, ("full_text", "description", "parameter_description", "desc"), 500)
        confidence = _first_text(item, ("confidence", "score"), 60)
        if not any((name, value, description)):
            rejected += 1
            continue
        bucket["parameters"].append({
            "name": name, "value": value, "description": description,
            "provider_confidence_hint": confidence,
            "confidence_is_independent_probability": False,
            "observed_at": observed_at,
            "trust_label": "provider_parameter_unverified",
        })
    return rejected


def _parse_comment_entity(bucket: dict, row: dict, observed_at: str) -> int:
    values = row.get("entity_comments", row.get("comments", row.get("comment_summaries")))
    if not isinstance(values, list) or len(values) > 20:
        return 1
    rejected = 0
    for item in values:
        if not isinstance(item, dict):
            rejected += 1
            continue
        name = _first_text(item, ("attribute_name", "dimension", "name"), 120)
        value = _first_text(item, ("attribute_value", "value", "sentiment"), 160)
        description = _safe_string_list(item.get("attribute_description", item.get("descriptions")),
                                        limit=10, text_limit=400)
        count = item.get("count")
        reported_count = count if type(count) is int and 0 <= count <= 10_000_000 else None
        links = item.get("list_link", item.get("links"))
        source_titles = []
        if isinstance(links, list):
            for link in links[:10]:
                if not isinstance(link, dict):
                    continue
                title = _first_text(link, ("title", "name"), 200)
                host = _url_host_only(link.get("url", link.get("link")))
                if title or host:
                    source_titles.append({"title_hint": title, "host_hint": host})
        if not any((name, value, description, reported_count is not None, source_titles)):
            rejected += 1
            continue
        bucket["opinion_summaries"].append({
            "entity_name_std_hint": _first_text(item, ("entity_name_std",), 200),
            "dimension_hint": _first_text(item, ("dimension",), 120),
            "attribute_name": name,
            "attribute_value": value,
            "description_hints": description,
            "reported_count_hint": reported_count,
            "reported_count_is_verified_sample_size": False,
            "source_link_hints": source_titles,
            "observed_at": observed_at,
            "trust_label": "provider_aggregated_opinion_unverified_not_independent_test",
        })
    return rejected


def _empty(status: str, *, error: str | None = None) -> dict:
    result = {
        "operation": "haina_mcp_research_ingest",
        "status": status,
        "source_mode": ("blocked" if status.startswith("blocked") else
                        "synthetic_test" if status == "no_valid_mcp_calls" else "unknown"),
        "call_count": 0,
        "accepted_call_count": 0,
        "rejected_call_count": 0,
        "entity_count": 0,
        "entities": [],
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "limitations": [
            "供应商SPU/SKU/商品ID均为供应商内部标识，不映射为京东或淘宝平台商品ID",
            "供应商价格只保留为未核验线索，不作为地区到手价、预算通过或实时报价",
            "参数和基础信息属于供应商返回，不替代厂商原始规格",
            "评价是供应商聚合摘要，不等于独立评测、原始评论或经核样本",
            "合成报告仅验证接线，不计入真实商品证据、比较效果或购买批准",
        ],
    }
    if error:
        result["error"] = error
    return result


def ingest_haina_mcp_bundle(report: object, *, now: datetime | None = None) -> dict:
    """只接收明确 synthetic_test 的 MCP 工具结果包；真实响应无条件阻断。"""
    if not isinstance(report, dict):
        return _empty("invalid_report", error="report_not_object")
    if report.get("source_mode") != "synthetic_test":
        return _empty("blocked_real_data_use_not_approved")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        return _empty("invalid_report", error="naive_clock")
    if set(report) != _ALLOWED_REPORT_KEYS or report.get("schema_version") != 1:
        return _empty("invalid_report", error="report_schema_invalid")
    if report.get("operation") != "haina_mcp_synthetic_bundle":
        return _empty("invalid_report", error="operation_invalid")
    try:
        encoded = json.dumps(_safe_for_size_check(report), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        return _empty("invalid_report", error="report_not_json_serializable")
    if len(encoded) > MAX_REPORT_BYTES:
        return _empty("invalid_report", error="report_too_large")
    calls = report.get("calls")
    if not isinstance(calls, list) or not 1 <= len(calls) <= MAX_CALLS:
        return _empty("invalid_report", error="call_count_invalid")

    buckets: dict[tuple[str, str], dict] = {}
    call_summaries = []
    accepted_calls = rejected_calls = 0
    for call_index, call in enumerate(calls, start=1):
        summary = {
            "call_id": f"synthetic-call:{call_index:02d}",
            "status": "blocked",
            "tool": None,
            "query": None,
            "observed_at": None,
            "reported_rows": 0,
            "accepted_entities": 0,
            "rejected_rows": 0,
        }
        if not isinstance(call, dict) or set(call) != _ALLOWED_CALL_KEYS:
            summary["reason"] = "call_schema_invalid"
            call_summaries.append(summary)
            rejected_calls += 1
            continue
        tool = call.get("tool")
        query = _text(call.get("query"), 200)
        observed_raw = _text(call.get("observed_at"), 50)
        if not isinstance(tool, str) or tool not in _ALLOWED_TOOLS or query is None or observed_raw is None:
            summary["reason"] = "call_header_invalid"
            call_summaries.append(summary)
            rejected_calls += 1
            continue
        try:
            observed = datetime.fromisoformat(observed_raw.replace("Z", "+00:00"))
            if observed.tzinfo is None or observed > current:
                raise ValueError("invalid_observation")
        except (TypeError, ValueError, OverflowError):
            summary["reason"] = "observation_invalid"
            call_summaries.append(summary)
            rejected_calls += 1
            continue
        payload = call.get("payload")
        if not isinstance(payload, dict) or type(payload.get("error_code")) is not int:
            summary["reason"] = "payload_invalid"
            call_summaries.append(summary)
            rejected_calls += 1
            continue
        if payload.get("error_code") != 0:
            summary["reason"] = "provider_business_error"
            summary["business_code"] = payload.get("error_code")
            call_summaries.append(summary)
            rejected_calls += 1
            continue
        rows = payload.get("data")
        if not isinstance(rows, list) or len(rows) > MAX_ENTITIES_PER_CALL:
            summary["reason"] = "data_shape_invalid"
            call_summaries.append(summary)
            rejected_calls += 1
            continue
        summary.update({"tool": tool, "query": query, "observed_at": observed.isoformat(),
                        "reported_rows": len(rows), "status": "accepted"})
        for entity_index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                summary["rejected_rows"] += 1
                continue
            entity_name = _first_text(row, ("entity_name", "entity_name_std", "name"), 200)
            if entity_name is None:
                summary["rejected_rows"] += 1
                continue
            bucket = _entity_bucket(buckets, query, entity_name, observed.isoformat())
            _record_source(bucket, tool, observed.isoformat())
            if tool == "product_sku_search":
                summary["rejected_rows"] += _parse_sku_entity(
                    bucket, row, query, call_index, entity_index, observed.isoformat())
            elif tool == "product_basic_search":
                summary["rejected_rows"] += _parse_basic_entity(bucket, row, observed.isoformat())
            elif tool == "product_parameter_search":
                summary["rejected_rows"] += _parse_parameter_entity(bucket, row, observed.isoformat())
            elif tool == "product_comment_search":
                summary["rejected_rows"] += _parse_comment_entity(bucket, row, observed.isoformat())
            summary["accepted_entities"] += 1
        if summary["accepted_entities"] or not rows:
            accepted_calls += 1
        else:
            summary["status"] = "no_valid_entities"
            rejected_calls += 1
        call_summaries.append(summary)

    entities = list(buckets.values())
    for entity in entities:
        models = set()
        for lead in entity["sale_leads"]:
            models.update(lead.get("title_model_candidates", []))
            models.update(lead.get("spec_model_candidates", []))
        entity["model_candidates"] = sorted(models)
        entity["sale_lead_count"] = len(entity["sale_leads"])
        entity["platform_identity_verified_count"] = 0
        entity["quote_verified_count"] = 0
        entity["research_status"] = "supplier_research_clues_only"
    return {
        "operation": "haina_mcp_research_ingest",
        "status": "synthetic_mcp_report_ingested" if accepted_calls else "no_valid_mcp_calls",
        "source_mode": "synthetic_test",
        "call_count": len(calls),
        "accepted_call_count": accepted_calls,
        "rejected_call_count": rejected_calls,
        "call_summaries": call_summaries,
        "total_reported_rows": sum(x["reported_rows"] for x in call_summaries),
        "total_accepted_entities": sum(x["accepted_entities"] for x in call_summaries),
        "total_rejected_rows": sum(x["rejected_rows"] for x in call_summaries),
        "entity_count": len(entities),
        "entities": entities,
        "platform_identity_verified_count": 0,
        "quote_verified_count": 0,
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "limitations": [
            "供应商SPU/SKU/商品ID均为供应商内部标识，不映射为京东或淘宝平台商品ID",
            "推广链接仅保留host提示，不保存完整URL、路径或跟踪参数",
            "供应商价格只保留为未核验线索，不作为地区到手价、预算通过或实时报价",
            "参数和基础信息属于供应商返回，不替代厂商原始规格",
            "评价是供应商聚合摘要，不等于独立评测、原始评论或经核样本",
            "合成报告仅验证接线，不计入真实商品证据、比较效果或购买批准",
        ],
    }


def load_haina_mcp_report(path: Path | str, *, now: datetime | None = None) -> dict:
    """仅加载仓库内固定哈希的合成夹具；任意用户文件不得自标synthetic绕过真实数据门禁。"""
    try:
        file_path = Path(path)
        if not file_path.is_file():
            return _empty("report_unavailable", error="report_file_missing")
        resolved = file_path.resolve(strict=True)
        expected = SYNTHETIC_FIXTURE_PATH.resolve(strict=True)
        if resolved != expected:
            return _empty("blocked_non_fixture_report", error="only_pinned_synthetic_fixture_is_loadable")
        size = file_path.stat().st_size
        if size < 1 or size > MAX_REPORT_BYTES:
            return _empty("report_unavailable", error="report_file_size_invalid")
        raw = file_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != SYNTHETIC_FIXTURE_SHA256:
            return _empty("blocked_fixture_hash_mismatch", error="synthetic_fixture_hash_mismatch")
        report = json.loads(raw.decode("utf-8-sig"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return _empty("report_unavailable", error="report_read_or_json_invalid")
    result = ingest_haina_mcp_bundle(report, now=now)
    result["report_sha256"] = digest
    result["report_size_bytes"] = len(raw)
    return result
