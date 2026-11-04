"""P0只读商品事实比较：跨品类共用三态约束匹配，不将厂商资料冒充独立横评。

不抓取电商账户、不提供实时成交价、不排序为购买推荐。
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from .contracts import PurchaseRequest
from .evidence_policy import valid_https_url

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
        failed, unknown, met, preference_met, preference_unknown, preference_unmet = [], [], [], [], [], []
        evidence = {}
        for key, expected in required.items():
            field = facts.get(key, {})
            actual = field.get("value")
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
            actual = field.get("value")
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
        elif unknown or budget_max_cny is not None or stale_days > 30:
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
            "consumables": item.get("consumables", []),
            "durability_independently_verified": bool(item.get("independent_durability_test", False)),
            "unknowns": (
                (["实际到手价、库存及预算匹配尚无授权实时核验"] if budget_max_cny is not None else [])
                + (["独立耐用性/故障率未核实"] if not item.get("independent_durability_test") else [])
                + (["官网产品事实已超过30天，请复核"] if stale_days > 30 else [])
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
    required = {"color_print": True} if req.needs_color else {"monochrome_print": True}
    if req.requires_wireless is True:
        required["wireless"] = True
    if req.requires_scan is True:
        required["scan"] = True
    words = "；".join(req.requirements)
    want_wechat = "微信" in words
    must_mini = any(s in words for s in ("必须微信小程序", "必须从微信小程序", "必须用微信小程序"))
    preferred = {}
    if must_mini:
        required["wechat_miniprogram"] = True
    elif want_wechat:
        preferred["wechat_miniprogram"] = True
        # 无线连接只作为辅助偏好：不能代替微信兼容性证据。
        preferred["wireless"] = True
    result = compare_products(load_official_catalog(path), category="printer",
                              required=required, preferred=preferred,
                              budget_max_cny=req.budget_max_cny,
                              target_region=req.market_region)
    if want_wechat and not must_mini:
        result["limitations"].append("用户只说希望微信打印：先作为偏好，不能代填必须使用官方小程序；若要求特定微信工作流需再确认。")
    return result


def catalogue_sha256(path: Path = CATALOG_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
