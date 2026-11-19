"""P0只读商品事实比较：跨品类共用三态约束匹配，不将厂商资料冒充独立横评。

不抓取电商账户、不提供实时成交价、不排序为购买推荐。
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from .contracts import PurchaseRequest
from .evidence_policy import valid_https_url
from .printer_conditions import printer_conditions
from .retail import load_retail_checks, assess_quote
from .printer_case import compare_case

CATALOG_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "printer_products_official.json"


def load_official_catalog(path: Path = CATALOG_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("products"), list):
        raise ValueError("产品事实目录格式不正确")
    try:
        recorded = date.fromisoformat(data["recorded_on"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("产品目录缺失有效抓取日期") from exc
    if recorded > date.today():
        raise ValueError("产品目录抓取日期不能在未来")
    seen = set()
    for item in data["products"]:
        if not isinstance(item, dict) or not item.get("model_id") or item["model_id"] in seen:
            raise ValueError("型号标识缺失或重复")
        seen.add(item["model_id"])
        if not all(isinstance(item.get(field), str) and item[field].strip()
                   for field in ("category", "brand", "name")):
            raise ValueError("产品必要字段缺失")
        if not valid_https_url(item.get("official_url")):
            raise ValueError("产品缺少可核对的官方URL")
        facts = item.get("facts")
        if not isinstance(facts, dict) or not facts:
            raise ValueError("型号缺少结构化事实")
        for key, fact in facts.items():
            if (not isinstance(key, str) or not isinstance(fact, dict)
                    or fact.get("value") not in (True, False, None)
                    or type(fact.get("value")) not in (bool, type(None))):
                raise ValueError("型号事实必须是true、false或null")
            if fact["value"] is not None and not valid_https_url(fact.get("source_url")):
                raise ValueError("已核实的事实必须携带HTTPS证据URL")
            if fact["value"] is None and fact.get("source_url") is not None:
                raise ValueError("未知事实不能绑定声称已核实的URL")
        if item.get("manufacturer_suggested_retail_cny") is not None:
            v = item["manufacturer_suggested_retail_cny"]
            if type(v) is not int or v < 0 or not valid_https_url(item.get("manufacturer_suggested_retail_url")):
                raise ValueError("建议零售价缺少金额或官方来源")
        if item.get("marketplace_sku") or item.get("live_price_cny"):
            raise ValueError("官网快照不能夹带未经平台授权核实的SKU或实时报价")
        for key in ('manufacturer_service', 'included_consumables_reference'):
            reference = item.get(key)
            if reference is not None:
                if (not isinstance(reference, dict) or not valid_https_url(reference.get('source_url'))
                        or not isinstance(reference.get('summary'), str) or not reference['summary'].strip()):
                    raise ValueError('厂商耗材/服务资料缺少来源或说明')
                try:
                    captured = date.fromisoformat(reference['captured_on'])
                    if captured > date.today():
                        raise ValueError('资料获取日在未来')
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError('厂商耗材/服务资料缺少有效获取日') from exc
    return data


def compare_products(catalog: dict, *, category: str, required: dict[str, bool],
                     preferred: dict[str, bool] | None = None, budget_max_cny: int | None = None,
                     today: date | None = None, target_region: str | None = None) -> dict:
    """通用比较器：硬条件假为排除，未知为待验证；偏好只影响待核查顺序。

    实际成交价缺失时预算一定是未核实：官网建议零售价不得替代报价。
    """
    if budget_max_cny is not None and (type(budget_max_cny) is not int or budget_max_cny < 0):
        raise ValueError("预算必须为非负整数")
    if target_region is not None and catalog.get('market_region') != target_region:
        return {'status': 'catalog_region_mismatch', 'category': category, 'candidates': [],
                'purchase_recommendation_approved': False, 'transactions_enabled': False}
    preferred = preferred or {}
    for group in (required, preferred):
        if not isinstance(group, dict) or any(not isinstance(k, str) or type(v) is not bool
                                              for k, v in group.items()):
            raise ValueError("对比约束应为特征名到布尔值的映射")
    recorded = date.fromisoformat(catalog["recorded_on"])
    today = today or date.today()
    if recorded > today:
        raise ValueError("来源快照日期晚于比较日期")
    stale_days = (today - recorded).days
    entries = []
    for item in catalog["products"]:
        if item.get("category") != category:
            continue
        facts = item["facts"]
        detail = item.get("manufacturer_detail_evidence")
        detail_age_days = None
        if detail is not None:
            if (not isinstance(detail, dict)
                    or detail.get("source_url") != item.get("official_url")
                    or not isinstance(detail.get("response_sha256"), str)
                    or len(detail["response_sha256"]) != 64
                    or detail.get("billing_model") not in ("unknown", "buy_print_pages_to_claim_consumables")):
                raise ValueError("invalid_manufacturer_detail_evidence")
            try:
                observed = datetime.fromisoformat(detail["observed_at"].replace("Z", "+00:00"))
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                raise ValueError("invalid_manufacturer_detail_observation") from exc
            if (observed.tzinfo is None or observed > datetime.now(timezone.utc)
                    or observed.date() > today or observed.year < 2020):
                raise ValueError("future_or_invalid_manufacturer_detail_observation")
            detail_age_days = (today - observed.date()).days
        detail_stale = detail_age_days is not None and detail_age_days > 30

        def current_fact_value(key: str):
            field = facts.get(key, {})
            # 逐型号详情超过30天后，来自该详情页的当前功能判断全部降级为未知；
            # 不改写目录原始事实，历史记录仍可审计。
            if detail_stale and detail and field.get("source_url") == detail.get("source_url"):
                return None
            return field.get("value")

        failed, unknown, met, preference_met, preference_unknown, preference_unmet = [], [], [], [], [], []
        evidence = {}
        for key, expected in required.items():
            field = facts.get(key, {})
            actual = current_fact_value(key)
            if actual is None:
                unknown.append(key)
            elif actual is expected:
                met.append(key)
                evidence[key] = field["source_url"]
            else:
                failed.append(key)
                evidence[key] = field["source_url"]
        for key, expected in preferred.items():
            field = facts.get(key, {})
            actual = current_fact_value(key)
            if actual is None:
                preference_unknown.append(key)
            elif actual is expected:
                preference_met.append(key)
                evidence[key] = field["source_url"]
            else:
                preference_unmet.append(key)
                evidence[key] = field["source_url"]
        budget_status = "not_checked" if budget_max_cny is None else "unverified_no_authorized_live_quote"
        if failed:
            state = "excluded_by_verified_spec"
        elif unknown or budget_max_cny is not None or stale_days > 30 or detail_stale:
            state = "needs_verification"
        else:
            state = "specs_matched_not_purchase_approved"
        entries.append({
            "model_id": item["model_id"], "brand": item["brand"], "name": item["name"],
            "official_url": item["official_url"], "status": state,
            "required_met": met, "required_unknown": unknown, "required_failed": failed,
            "preferred_met": preference_met, "preferred_unknown": preference_unknown,
            "preferred_failed": preference_unmet, "evidence_by_feature": evidence,
            "budget_status": budget_status, "live_price_cny": None, "marketplace_sku": None,
            "manufacturer_suggested_retail_cny": item.get("manufacturer_suggested_retail_cny"),
            "manufacturer_suggested_retail_is_live_price": False,
            # 过期逐型号详情只能作为历史审计，不能继续展示为当期耗材配置。
            "consumables": [] if detail_stale else item.get("consumables", []),
            "manufacturer_detail_evidence": detail,
            "manufacturer_detail_age_days": detail_age_days,
            "manufacturer_detail_is_stale": detail_stale,
            "billing_model": (detail.get("billing_model") if detail and not detail_stale else "unknown"),
            "durability_independently_verified": bool(item.get("independent_durability_test", False)),
            "unknowns": (
                (["实际到手价、库存及预算匹配尚无授权实时核验"] if budget_max_cny is not None else [])
                + (["独立耐用性/故障率未核实"] if not item.get("independent_durability_test") else [])
                + (["官网产品事实已超过30天，请复核"] if stale_days > 30 else [])
                + (["逐型号详情证据已超过30天，请重新核对"] if detail_age_days is not None and detail_age_days > 30 else [])
                + (["此型号采用购买打印页数、申领耗材的模式；必须另核套餐费用、期限、剩余页数和低印量成本"]
                    if detail and not detail_stale and detail.get("billing_model") == "buy_print_pages_to_claim_consumables" else [])
                + (["历史详情曾记载页数套餐或耗材，超过30天的内容不构成当前有效套餐/耗材配置"]
                    if detail_stale and detail and (detail.get("billing_model") != "unknown" or item.get("consumables")) else [])
            ),
        })
    # 这是“下一步核查优先次序”，不是购买榜单或官方性价比评分。
    priority = {"specs_matched_not_purchase_approved": 0, "needs_verification": 1, "excluded_by_verified_spec": 2}
    entries.sort(key=lambda x: (priority[x["status"]], len(x["required_failed"]),
                                len(x["required_unknown"]), -len(x["preferred_met"]),
                                len(x["preferred_unknown"]), x["model_id"]))
    return {
        "status": "facts_comparison_only",
        "category": category, "catalog_recorded_on": catalog["recorded_on"],
        "catalog_age_days": stale_days, "catalog_source_kind": catalog["source_kind"],
        "searched_models": len(entries), "purchase_recommendation_approved": False,
        "all_prices_real_time_verified": False, "transactions_enabled": False,
        "constraints": {"required": required, "preferred": preferred, "budget_max_cny": budget_max_cny},
        "candidates": entries,
        "limitations": [
            "排序仅表示硬约束与有来源的偏好匹配，非质量/耐用/性价比排名。",
            "事实来自厂商公开技术说明或支持页面，不能替代独立对照测试。",
            "厂商建议零售价不等于实际到手价，不能用来判断预算是否通过。",
            "无现售SKU、实时库存、实时平台售价与实际设备微信打印连接测试。",
        ],
    }


def compare_printer_request(req: PurchaseRequest, *, path: Path = CATALOG_PATH) -> dict:
    """仅打印机适配层抽取已经确认的结构化条件；通用比较器不写打印机分支。"""
    if req.category != "printer":
        return {"status": "unsupported_category", "candidates": []}
    if req.needs_color is None:
        return {"status": "requires_color_clarification", "candidates": []}
    conditions = printer_conditions(req)
    if conditions['conflicts']:
        return {"status": "condition_conflict", "candidates": [], "questions": conditions['conflicts'],
                "purchase_recommendation_approved": False, "transactions_enabled": False}
    catalog = load_official_catalog(path)
    result = compare_products(catalog, category="printer",
                              required=conditions['required'], preferred=conditions['preferred'],
                              budget_max_cny=req.budget_max_cny,
                              target_region=req.market_region)
    if result['status'] != 'facts_comparison_only':
        return result
    checks = load_retail_checks()
    result['questions'] = conditions['questions']
    result['unresolved_hard_conditions'] = conditions['unresolved_hard_conditions']
    result['retail_check_status'] = checks.get('status', checks.get('provider_capability'))
    for candidate in result['candidates']:
        observations = [c for c in checks.get('checks', []) if c['model_id'] == candidate['model_id']]
        candidate['retail_checks'] = observations
        candidate['quote_assessment'] = assess_quote(None, model_id=candidate['model_id'],
            delivery_region=req.delivery_region, budget_scope=req.budget_scope, budget_max_cny=req.budget_max_cny)
        candidate['purchasable'] = False
        candidate['budget_scope'] = req.budget_scope
        candidate['delivery_region'] = req.delivery_region
        candidate['unknowns'] += conditions['unresolved_hard_conditions']
        candidate['unknowns'] += (["预算支出口径未确认"] if req.budget_scope == 'unknown' else [])
        candidate['unknowns'] += (["收货地区未确认，不能判断库存与运费"] if not req.delivery_region else [])
        candidate['supporting_evidence'] = [{"feature": key, "source_url": candidate['evidence_by_feature'][key],
                                            "captured_on": result['catalog_recorded_on']}
                                           for key in candidate['required_met'] + candidate['preferred_met']]
        candidate['opposing_evidence'] = [{"feature": key, "source_url": candidate['evidence_by_feature'][key],
                                          "captured_on": result['catalog_recorded_on']}
                                         for key in candidate['required_failed'] + candidate['preferred_failed']]
        candidate['cost_summary'] = {"device_delivered_minor": None, "extra_consumables_minor": None,
                                     "lifetime_total_minor": None,
                                     "limitation": "主机到手价与后续耗材分列；无期限/用量/价格假设，不计算精确单页或多年成本"}
        original = next(p for p in catalog['products'] if p['model_id'] == candidate['model_id'])
        candidate['manufacturer_service'] = original.get('manufacturer_service', {})
        candidate['included_consumables_reference'] = original.get('included_consumables_reference', {})
    result['limitations'].append("微信硬要求与工作流分别确认；原文未理解的硬要求进入每款候选未知项并阻止购买结论。")
    result['case_comparison'] = compare_case(req, result['candidates'])
    return result


def catalogue_sha256(path: Path = CATALOG_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
