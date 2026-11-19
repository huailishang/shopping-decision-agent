"""只读、数据驱动的比较依据：不执行任意表达式，不将厂家建议价视作成交价。"""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import unicodedata

CRITERIA_PATH = Path(__file__).resolve().parent.parent / "knowledge/printer_selection_criteria.json"
_ALLOWED_OPS = {"boolean_equal", "number_le", "interval_relation"}
_ALLOWED_KINDS = {"hard", "hard_when_miniprogram_confirmed", "informational"}
_ALLOWED_ACTIVATIONS = {"provided", "true_only"}
_ALLOWED_CONFIG_KEYS = {"schema_version", "config_version", "status", "category",
                        "captured_on", "market_scope", "source_registry", "criteria", "models",
                        "purchase_recommendation_approved", "transactions_enabled"}
_ALLOWED_RULE_KEYS = {"id", "why", "user_field", "product_field", "op",
                      "activation", "kind", "unit", "source_ids", "unknown"}
_ALLOWED_FACT_KEYS = {"value", "unit", "source_ids", "status", "valid_until"}
_ALLOWED_MODEL_KEYS = {"model_id", "brand", "facts", "wechat_setup", "source_ids"}
_ALLOWED_SOURCE_KEYS = {"type", "group", "url", "published_on", "checked_on",
                        "method", "limit"}


def is_unanswered_device_deployment_region(region: object) -> bool:
    """仅归一化明确缺答值；无法识别的真实地名不等于本人未作答。"""
    if region is None:
        return True
    if not isinstance(region, str):
        return False
    marker = unicodedata.normalize("NFKC", region).strip().casefold()
    return marker in {"", "未知", "待确认", "未确认", "尚未确认",
                      "不清楚", "不知道", "不确定", "待定",
                      "unknown", "not sure", "unsure", "pending", "tbd"}


def classify_device_deployment_region(region: object) -> str:
    """设备实际部署地的保守分类；收货地或定位信息不作代填。"""
    if not isinstance(region, str) or not region.strip():
        return "unknown"
    overseas = ("香港", "澳门", "台湾", "日本", "新加坡", "Singapore", "Japan",
                "海外", "境外", "Hong Kong", "Taiwan", "Macau")
    mainland = ("中国大陆", "中国内地", "中国", "北京", "上海", "天津", "重庆",
                "河北", "山西", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽",
                "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "海南",
                "四川", "贵州", "云南", "陕西", "甘肃", "青海", "内蒙古",
                "广西", "西藏", "宁夏", "新疆")
    if any(term.lower() in region.lower() for term in overseas):
        return "outside_mainland_china"
    if any(term in region for term in mainland):
        return "mainland_china"
    return "unknown"


def _interval_relation(actual: list[int], recommended: list[int]) -> str:
    """actual是用户月印量区间，recommended是厂家建议区间。"""
    a, b = actual
    lo, hi = recommended
    if b < lo:
        return "below"
    if a > hi:
        return "above"
    if a == lo and b == hi:
        return "equal"
    if a >= lo and b <= hi:
        return "within"
    if a <= lo and b >= hi:
        return "contains"
    return "overlap"


def _valid_number(v: object) -> bool:
    return type(v) is int and 0 <= v <= 10_000_000


def _valid_interval(v: object) -> bool:
    return (isinstance(v, (list, tuple)) and len(v) == 2
            and _valid_number(v[0]) and _valid_number(v[1]) and v[0] <= v[1])


def validate_criteria(data: object) -> dict:
    """加载时全部校验。来源和事实字段只能是数据，不存在表达式/脚本执行口。"""
    if (not isinstance(data, dict) or set(data) - _ALLOWED_CONFIG_KEYS
            or data.get("schema_version") != 1
            or data.get("status") != "executor_source_checked_pending_independent_review"
            or data.get("purchase_recommendation_approved") is not False
            or data.get("transactions_enabled") is not False
            or not isinstance(data.get("config_version"), str)
            or ("category" in data and (not isinstance(data["category"], str)
                                         or not data["category"].strip()))
            or not isinstance(data.get("source_registry"), dict)
            or not isinstance(data.get("criteria"), list)
            or not isinstance(data.get("models"), list)):
        raise ValueError("invalid_selection_contract")
    try:
        recorded = date.fromisoformat(data["captured_on"])
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("invalid_selection_capture_date") from exc
    if recorded > date.today():
        raise ValueError("future_selection_capture_date")
    sources = data["source_registry"]
    if (not sources or len(sources) > 128 or len(data["criteria"]) > 64
            or len(data["models"]) > 20
            or any(not isinstance(key, str) or not isinstance(value, dict)
                          or set(value) - _ALLOWED_SOURCE_KEYS
                          or not isinstance(value.get("url"), str)
                          or not value["url"].startswith("https://")
                          or not isinstance(value.get("limit"), str)
                          for key, value in sources.items())):
        raise ValueError("invalid_selection_sources")
    seen = set()
    for rule in data["criteria"]:
        if (not isinstance(rule, dict) or set(rule) != _ALLOWED_RULE_KEYS
                or not isinstance(rule.get("id"), str)
                or rule["id"] in seen or rule.get("op") not in _ALLOWED_OPS
                or rule.get("kind") not in _ALLOWED_KINDS
                or rule.get("activation") not in _ALLOWED_ACTIVATIONS
                or not isinstance(rule.get("user_field"), str)
                or not isinstance(rule.get("product_field"), str)
                or not isinstance(rule.get("why"), str)
                or not isinstance(rule.get("unknown"), str)
                or not isinstance(rule.get("unit"), str)
                or not isinstance(rule.get("source_ids"), list)
                or not rule["source_ids"]
                or any(s not in sources for s in rule["source_ids"])):
            raise ValueError("invalid_selection_rule")
        seen.add(rule["id"])
    seen = set()
    for model in data["models"]:
        if (not isinstance(model, dict) or set(model) - _ALLOWED_MODEL_KEYS
                or not isinstance(model.get("model_id"), str)
                or model["model_id"] in seen or not isinstance(model.get("facts"), dict)
                or (data.get("category") == "printer" and not isinstance(model.get("wechat_setup"), str))):
            raise ValueError("invalid_selection_model")
        seen.add(model["model_id"])
        for rule in data["criteria"]:
            fact = model["facts"].get(rule["product_field"])
            if not isinstance(fact, dict) or set(fact) - _ALLOWED_FACT_KEYS:
                raise ValueError("missing_or_unknown_selection_fact_entry")
            value = fact.get("value")
            refs = fact.get("source_ids")
            if not isinstance(refs, list) or any(s not in sources for s in refs):
                raise ValueError("invalid_selection_fact_source")
            if value is not None and not refs:
                raise ValueError("unattributed_selection_fact")
            if rule["op"] == "boolean_equal" and value is not None and type(value) is not bool:
                raise ValueError("invalid_selection_bool")
            if rule["op"] == "number_le" and value is not None and not _valid_number(value):
                raise ValueError("invalid_selection_number")
            if rule["op"] == "interval_relation" and value is not None and not _valid_interval(value):
                raise ValueError("invalid_selection_interval")
            if fact.get("status") not in (None, "withdrawn") or (
                    fact.get("valid_until") is not None
                    and (not isinstance(fact["valid_until"], str)
                         or not _valid_iso_date(fact["valid_until"]))):
                raise ValueError("invalid_selection_fact_validity")
    return data


def _valid_iso_date(raw: str) -> bool:
    try:
        date.fromisoformat(raw)
        return True
    except ValueError:
        return False


def load_criteria(path: Path = CRITERIA_PATH) -> tuple[dict, str]:
    data_bytes = path.read_bytes()
    if len(data_bytes) > 100_000:
        raise ValueError("selection_contract_too_large")
    data = json.loads(data_bytes)
    return validate_criteria(data), hashlib.sha256(data_bytes).hexdigest()


def evaluate_selection(values: dict, *, path: Path = CRITERIA_PATH,
                       config: dict | None = None, today: date | None = None) -> dict:
    """对同一份数据做资格先行、信息性比较及必要追问；不生成品牌分数。"""
    if not isinstance(values, dict):
        raise ValueError("invalid_selection_input")
    if config is None:
        config, config_hash = load_criteria(path)
    else:
        config = validate_criteria(config)
        config_hash = hashlib.sha256(json.dumps(
            config, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    # R1: request/material category binding, with explicit legacy-unscoped fallback.
    material_category = config.get("category")
    request_category = values.get("category")
    if request_category is not None and (
            not isinstance(request_category, str) or not request_category.strip()):
        raise ValueError("invalid_selection_request_category")
    if material_category is not None and request_category is not None:
        if request_category != material_category:
            raise ValueError("selection_category_mismatch")
    elif material_category is None and request_category is not None:
        raise ValueError("unscoped_legacy_selection_category")
    effective_category = material_category
    today = today or date.today()
    region_scope = classify_device_deployment_region(values.get("device_deployment_region"))
    observations = []
    questions = []
    question_items = []

    def add_question(message: str, kind: str, field: str) -> None:
        if message not in questions:
            questions.append(message)
            question_items.append({"text": message, "kind": kind, "field": field})

    for model in config["models"]:
        checks, failed, unknown = [], [], []
        for rule in config["criteria"]:
            field = rule["user_field"]
            raw = values.get(field)
            if raw is None or (rule["activation"] == "true_only" and raw is not True):
                continue
            op = rule["op"]
            valid = ((type(raw) is bool if op == "boolean_equal" else
                      _valid_number(raw) if op == "number_le" else _valid_interval(raw)))
            if not valid:
                raise ValueError("invalid_selection_input_type:" + field)
            fact = model["facts"][rule["product_field"]]
            actual = fact["value"]
            unit_missing_or_mismatched = (
                op != "boolean_equal" and actual is not None
                and fact.get("unit") != rule["unit"])
            fact_unavailable = (fact.get("status") == "withdrawn"
                                or (fact.get("valid_until") is not None
                                    and date.fromisoformat(fact["valid_until"]) < today))
            actual = None if fact_unavailable else actual
            relation = "unknown"
            if unit_missing_or_mismatched:
                relation = "incomparable_unit"
            elif actual is not None:
                relation = ("match" if actual is raw else "mismatch") if op == "boolean_equal" else (
                    "at_or_below" if actual <= raw else "above") if op == "number_le" else (
                    _interval_relation(list(raw), actual))
            kind = rule["kind"]
            # 小程序是否为必须，需要用户确认流程；未确认流程不能凭Wi-Fi或宣传视为满足。
            if kind == "hard_when_miniprogram_confirmed":
                workflow = values.get("wechat_workflow")
                if workflow != "miniprogram":
                    relation = "workflow_unconfirmed" if workflow in (None, "unknown") else "other_workflow_unverified"
                    if workflow in (None, "unknown"):
                        add_question("微信必须用小程序直接打印，还是允许文件转到厂家App？", "user_input", "wechat_workflow")
                elif relation == "match" and region_scope != "mainland_china":
                    # 本轮证据仅覆盖中国区小程序功能；不得以功能存在推断境外服务可用。
                    relation = ("deployment_region_unconfirmed" if region_scope == "unknown"
                                else "deployment_outside_verified_scope")
                if workflow == "miniprogram" and region_scope == "outside_mainland_china":
                    add_question("该部署地区的小程序服务尚无有效适用证据，需地区官方说明或实机核验", "external_evidence", "regional_wechat_service")
            effective_hard = kind == "hard" or kind == "hard_when_miniprogram_confirmed"
            if effective_hard:
                if relation in ("mismatch", "above"):
                    failed.append(rule["id"])
                elif relation not in ("match", "at_or_below", "within", "equal"):
                    unknown.append(rule["id"])
            checks.append({
                "criterion_id": rule["id"], "why": rule["why"], "kind": kind,
                "user_field": field, "user_value": raw, "product_field": rule["product_field"],
                "product_value": actual, "unit": rule["unit"],
                "product_unit": fact.get("unit"), "op": op,
                "relation": relation, "source_ids": list(fact["source_ids"]),
                "method_source_ids": list(rule["source_ids"]),
                "unknown_or_counter": rule["unknown"],
                "evidence_state": "withdrawn_or_expired" if fact_unavailable else (
                    "unit_not_proven_compatible" if unit_missing_or_mismatched else
                    "manufacturer_fact_research_only" if actual is not None else "not_established"),
                "deployment_region_scope": region_scope if kind == "hard_when_miniprogram_confirmed" else None,
                "source_region_research_applicable": (region_scope == "mainland_china"
                                                      and relation == "match")
                                                     if kind == "hard_when_miniprogram_confirmed" else None,
                # 有中国区功能资料也不等于用户真实网络已完成服务验证。
                "regional_service_verified": False if kind == "hard_when_miniprogram_confirmed" else None,
                "budget_live_verified": False if op == "number_le" else None,
            })
        state = ("excluded_by_hard_condition" if failed else
                 "pending_hard_evidence" if unknown else "model_spec_research_only")
        observations.append({
            "model_id": model["model_id"], "brand": model.get("brand"),
            "eligibility": state, "hard_failed": failed, "hard_unknown": unknown,
            "checks": checks, "wechat_setup": model.get("wechat_setup"),
            "wechat_setup_source_ids": model.get("source_ids", []),
            "regional_live_price_cny": None, "regional_budget_verified": False,
            "platform_identity_verified": False, "purchase_recommendation_approved": False,
        })
    if (values.get("wechat_required") is True
            and is_unanswered_device_deployment_region(values.get("device_deployment_region"))):
        add_question("微信服务实际部署地区尚未确认，不能用收货地或当前登录地代替", "user_input", "device_deployment_region")
    if (config.get("category") == "printer" and values.get("budget_max_cny") is not None
            and values.get("budget_scope") in (None, "unknown")):
        add_question("预算是否包含运费和本次需另购的耗材？", "user_input", "budget_scope")
    if config.get("category") == "printer" and values.get("monthly_pages_range") is not None:
        add_question("低频闲置后首张输出、耗材维护与实际成本尚缺独立实测，不据此排除机型", "external_evidence", "low_volume_reliability")
    eligible = [m["model_id"] for m in observations if m["eligibility"] == "model_spec_research_only"]
    pending = [m["model_id"] for m in observations if m["eligibility"] == "pending_hard_evidence"]
    excluded = [m["model_id"] for m in observations if m["eligibility"] == "excluded_by_hard_condition"]
    return {
        "status": "criteria_driven_research_not_purchase",
        "category": effective_category,
        "category_binding": "material_explicit" if material_category is not None else "legacy_unscoped",
        "criteria_version": config["config_version"],
        "criteria_sha256": config_hash,
        "fact_captured_on": config["captured_on"],
        "source_scope": config.get("market_scope"),
        "deployment_region_scope": region_scope,
        "source_registry": config["source_registry"],
        "models": observations,
        "research_eligible_models": eligible, "pending_models": pending,
        "excluded_models": excluded,
        "questions": list(dict.fromkeys(questions)),
        "question_items": question_items,
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "verified_live_quote_count": 0,
        "verified_platform_identity_count": 0,
        "note": ("有据型号研究，不是实时售价或购买资格；硬条件失败先排除、未知单列；厂家建议印量不是最低使用门槛"
                 if config.get("category") == "printer" else
                 "仅为受审输入的中性比较合同验证，不代表真实品类推荐或购买资格"),
    }
