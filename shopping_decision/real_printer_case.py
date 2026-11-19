"""首个真人打印机需求：固定来源的审计型研究理由，只读/不可批准购买。

本模块不接真实电商SKU，不自动提升H08旧卡审批状态。所有条件仍来自正常
dialogue_flow的本轮显式字段；未给出的真人答案绝不能猜测。
"""
from __future__ import annotations

import json
from pathlib import Path

from .contracts import PurchaseRequest
from .printer_conditions import printer_conditions
from .selection_criteria import evaluate_selection, classify_device_deployment_region

RESEARCH_PATH = (Path(__file__).resolve().parent.parent /
                 "knowledge/real_printer_case_research_20261113.json")
COMPARISON_PATH = (Path(__file__).resolve().parent.parent /
                   "knowledge/real_printer_case_comparison_20261115.json")


def _load_model_comparison(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("schema_version") != 1
            or data.get("review_status") != "research_only_pending_independent_review"
            or not isinstance(data.get("sources"), list)
            or not isinstance(data.get("models"), list)
            or not isinstance(data.get("comparisons"), list)
            or not isinstance(data.get("conditional_decisions"), list)
            or data.get("purchase_recommendation_approved") is not False
            or data.get("transactions_enabled") is not False):
        raise ValueError("invalid_model_comparison_contract")
    source_by_id = {item["id"]: item for item in data["sources"]
                    if isinstance(item, dict) and isinstance(item.get("id"), str)}
    if len(source_by_id) != len(data["sources"]):
        raise ValueError("invalid_model_comparison_sources")
    # 这个历史摘要合同尚不能把源撤回/有效期传播到所有旧取舍。
    # 显式拒绝，避免重建来源时丢掉元数据后仍使用旧结论。
    for source in data["sources"]:
        if "status" in source or "valid_until" in source:
            raise ValueError("unsupported_model_comparison_source_validity:" + source["id"])
    for group in ("models", "comparisons"):
        for item in data[group]:
            if (not isinstance(item, dict)
                    or not isinstance(item.get("source_ids"), list)
                    or any(source_id not in source_by_id for source_id in item["source_ids"])):
                raise ValueError("unmapped_model_comparison_source")
    for decision in data["conditional_decisions"]:
        if (not isinstance(decision, dict)
                or decision.get("status") != "conditional_research_candidate_not_purchase_approved"
                or not isinstance(decision.get("conditions_before_purchase"), list)):
            raise ValueError("invalid_conditional_decision")
    return {
        "case_id": data["case_id"],
        "captured_on": data["captured_on"],
        "review_status": data["review_status"],
        "usage_limit": data["usage_limit"],
        "models": data["models"],
        "comparisons": data["comparisons"],
        "conditional_decisions": data["conditional_decisions"],
        "sources": [{
            "id": source["id"], "source_group": source["source_group"],
            "source_kind": source["source_kind"], "url": source["url"],
            "claim": source["claim"], "counter": source["counter"],
            "scope": source["scope"], "fact_audit": source["fact_audit"],
            "captured_on": data["captured_on"],
        } for source in data["sources"]],
        "limits": data["limits"],
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "real_sale_identity_verified_count": 0,
        "regional_live_quote_count": 0,
    }


def compare_case_research(values: dict, *, path: Path = RESEARCH_PATH,
                          comparison_path: Path = COMPARISON_PATH) -> dict:
    base = {
        "case_id": "REAL-PRINTER-H08B-20261113",
        "status": "research_context_pending_independent_review",
        "source_mode": "dated_public_source_summary_offline_not_current_marketplace",
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "real_sale_identity_verified_count": 0,
        "regional_live_quote_count": 0,
    }
    if values.get("category") != "printer":
        return {**base, "reasons": [], "reason_count": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("schema_version") != 1
            or data.get("review_status") != "research_only_pending_independent_review"
            or not isinstance(data.get("sources"), list)
            or not isinstance(data.get("claims"), list)):
        raise ValueError("invalid_case_research_contract")
    source_by_id = {s["id"]: s for s in data["sources"]
                    if isinstance(s, dict) and isinstance(s.get("id"), str)}
    if len(source_by_id) != len(data["sources"]):
        raise ValueError("invalid_case_research_sources")

    requirements = values.get("requirements", ())
    if not isinstance(requirements, (list, tuple)):
        requirements = ()
    request = PurchaseRequest(
        category="printer", budget_max_cny=values.get("budget_max_cny"),
        needs_color=values.get("needs_color"),
        accepts_outsourced_color=values.get("accepts_outsourced_color"),
        requires_wireless=values.get("requires_wireless"),
        requires_scan=values.get("requires_scan"),
        requires_auto_duplex=values.get("requires_auto_duplex"),
        requirements=tuple(x for x in requirements if isinstance(x, str)),
        wechat_required=values.get("wechat_required"),
        wechat_workflow=values.get("wechat_workflow", "unknown"),
        delivery_region=values.get("delivery_region"),
        budget_scope=values.get("budget_scope", "unknown"),
    )
    condition_view = printer_conditions(request)
    wechat_preferred = condition_view["preferred"].get("wechat_miniprogram") is True
    reliability_required = any("可靠" in x or "耐用" in x for x in requirements if isinstance(x, str))
    model_comparison = _load_model_comparison(comparison_path)
    # 继承普通比较已经识别的原文硬要求，不能因结构化字段未单独填写而漏掉。
    # 这是原话条件的规范化，不是冒充用户逐字段确认。
    normalized = dict(values)
    normalized_from_text = []
    text_required = condition_view["required"]
    for feature, field in (("color_print", "needs_color"),
                           ("scan", "requires_scan"),
                           ("auto_duplex", "requires_auto_duplex")):
        if text_required.get(feature) is True and normalized.get(field) is None:
            normalized[field] = True
            normalized_from_text.append(field)
    if (text_required.get("wechat_miniprogram") is True
            and normalized.get("wechat_required") is not False):
        if normalized.get("wechat_required") is not True:
            normalized["wechat_required"] = True
            normalized_from_text.append("wechat_required")
        if normalized.get("wechat_workflow") in (None, "unknown"):
            normalized["wechat_workflow"] = "miniprogram"
            normalized_from_text.append("wechat_workflow")
    # 原话要求微信打印时，转App与流程未确认也必须进入同一硬条件算子；
    # 不要求用户再勾选一次“微信打印必须”，且明确否定由上游冲突门禁处理。
    if (normalized.get("wechat_required") is None
            and (text_required.get("wechat_workflow_unconfirmed") is True
                 or text_required.get("wechat_transfer_to_app") is True)):
        normalized["wechat_required"] = True
        normalized_from_text.append("wechat_required")
    criteria_view = evaluate_selection(normalized)
    criteria_view["normalized_from_requirement_text"] = normalized_from_text
    # 后续取舍与解释必须读同一份规范化需求，不能另取裸字段。
    values = normalized
    # 同一规范化硬要求同时约束主比较与研究比较。
    criteria_view["normalized_required"] = dict(condition_view["required"])
    criteria_view["unresolved_hard_conditions"] = list(condition_view["unresolved_hard_conditions"])
    # 无线是普通比较可识别的要求，但本轮选择依据JSON没有C-WIRELESS规则。
    # 在补齐准确型号规则前，不把它默默视为已满足。
    unmodeled_hard = ["wireless"] if text_required.get("wireless") is True else []
    criteria_view["unmodeled_hard_requirements"] = unmodeled_hard
    # 原文硬要求与结构化确认冲突时，所有型号仅供观察，禁止产生当前候选。
    if condition_view["conflicts"]:
        criteria_view["user_condition_conflicts"] = list(condition_view["conflicts"])
        criteria_view["research_eligible_models"] = []
        criteria_view["pending_models"] = []
        criteria_view["excluded_models"] = []
        criteria_view["questions"] = list(dict.fromkeys(
            condition_view["conflicts"] + criteria_view["questions"]))
        for model in criteria_view["models"]:
            model["eligibility"] = "blocked_by_user_condition_conflict"
            model["hard_unknown"] = list(dict.fromkeys(
                model["hard_unknown"] + ["user_condition_conflict"]))
    else:
        criteria_view["user_condition_conflicts"] = []
        if condition_view["unresolved_hard_conditions"] or unmodeled_hard:
            # 未识别/未建证据准则的强制要求：不能假设型号满足，也不能断言不满足。
            criteria_view["research_eligible_models"] = []
            criteria_view["pending_models"] = [m["model_id"] for m in criteria_view["models"]
                                              if m["eligibility"] != "excluded_by_hard_condition"]
            criteria_view["questions"] = list(dict.fromkeys(
                condition_view["questions"] + (
                    ["无线打印硬要求缺少当前选择准则与对应型号证据，必须先补证"]
                    if unmodeled_hard else []) + criteria_view["questions"]))
            for model in criteria_view["models"]:
                if model["eligibility"] != "excluded_by_hard_condition":
                    model["eligibility"] = "pending_hard_evidence"
                    model["hard_unknown"] = list(dict.fromkeys(
                        model["hard_unknown"] + ["unresolved_user_hard_requirement"]
                        + ["unmodeled_hard_requirement:" + name for name in unmodeled_hard]))
    model_comparison["criteria_comparison"] = criteria_view
    from .research_snapshot import render_research_snapshot
    shared_research_snapshot = render_research_snapshot(values, criteria_view)
    criteria_by_model = {item["model_id"]: item for item in criteria_view["models"]}

    def model_check(model_id: str, criterion_id: str) -> dict | None:
        return next((c for c in criteria_by_model[model_id]["checks"]
                     if c["criterion_id"] == criterion_id), None)

    def missing_fact_reason(check: dict | None) -> str:
        if check and check["evidence_state"] == "withdrawn_or_expired":
            return "相关厂家证据已撤回或过期"
        if check and check["evidence_state"] == "unit_not_proven_compatible":
            return "当前计量单位未核实兼容"
        return "缺少可用的型号事实证据"

    region = values.get("device_deployment_region")
    region_scope = classify_device_deployment_region(region)
    # 历史九维研究文字只作基线；本轮预算、印量、功能与适用地区均从当前校验结果求值。
    for item in model_comparison["comparisons"]:
        if item.get("dimension") == "scan_copy" and values.get("requires_scan") is True:
            scan_check = model_check("M232dw", "C-SCAN")
            if scan_check is None or scan_check["relation"] != "match":
                item["result"] = (f"本轮明确要求扫描，但HP扫描功能"
                                  f"{missing_fact_reason(scan_check)}，不能按旧规格资料断言此要求已满足；"
                                  "Brother扫描资料同样待核。")
                item["decision_effect"] = "扫描硬要求依当前证据待核，不能激活扫描优势推荐。"
        if item.get("dimension") == "automatic_duplex" and values.get("requires_auto_duplex") is True:
            duplex_check = model_check("M232dw", "C-DUPLEX")
            if duplex_check is None or duplex_check["relation"] != "match":
                item["result"] = (f"本轮明确要求自动双面，但HP相关功能"
                                  f"{missing_fact_reason(duplex_check)}，不能直接认定符合；"
                                  "Brother自动双面仍待核。")
                item["decision_effect"] = "自动双面硬要求依当前证据待核，不宣称已满足。"
        if item.get("dimension") == "wechat_print" and values.get("wechat_required") is True:
            if values.get("wechat_workflow") == "miniprogram" and region_scope != "mainland_china":
                item["result"] = ("两款型号均有中国区微信小程序功能/设置资料；"
                                  "但当前实际部署地不在已证实的中国区服务适用范围，"
                                  "不能用功能存在推断该地区服务可用。")
                item["decision_effect"] = "微信小程序硬要求进入地区服务待核，不按中国资料直接判符合。"
        if item.get("dimension") == "wechat_region":
            if region_scope == "outside_mainland_china":
                item["result"] = ("当前明确的设备部署地在中国大陆以外。Brother中国区小程序清单"
                                  "没有证明境外服务；HP历史支持答复提示境外限制，"
                                  "但不能据此推断今天所有境外环境必然不支持。需当前地区服务证据。")
            elif region_scope == "mainland_china":
                item["result"] = ("当前设备部署地为中国大陆；两款有中国区微信功能设置资料，"
                                  "仍需实际机型和网络绑定验证，不代表购买批准。")
            else:
                item["result"] = ("设备部署地尚未确认；现有中国区微信功能资料和"
                                  "HP历史境外服务答复不能证明实际使用地服务可用。")
        if item.get("dimension") == "budget":
            budget = values.get("budget_max_cny")
            brother = model_check("HL-L1238W", "C-BUDGET")
            if brother and brother["relation"] in ("above", "at_or_below"):
                relation = "高于" if brother["relation"] == "above" else "不高于"
                item["result"] = (
                    f"当前预算{budget}元，Brother HL-L1238W厂家建议零售价"
                    f"{brother['product_value']}元，{relation}当前预算；"
                    "建议价并非实价。HP M232dw缺厂家建议价，两款都没有地区到手价核验。"
                )
            elif budget is None:
                item["result"] = ("本轮未设置预算，无法形成厂家建议价预算关系；"
                                  "双方地区到手价仍未核。")
            else:
                item["result"] = (f"本轮预算{budget}元已确认，但Brother建议价"
                                  f"{missing_fact_reason(brother)}，无法形成确定预算大小关系；"
                                  "HP建议价及两款地区实价仍未核。")
            item["decision_effect"] = "建议价比较随本轮预算变化；地区预算符合仍是未知，不按建议价排除。"
        if item.get("dimension") == "low_volume_fit":
            volume = values.get("monthly_pages_range")
            hp = model_check("M232dw", "C-VOLUME")
            wording = {"below": "整体低于", "above": "整体高于", "equal": "完全等于",
                       "within": "落在", "contains": "完整覆盖", "overlap": "部分重叠"}
            if hp and hp["relation"] in wording:
                minimum, maximum = hp["product_value"]
                item["result"] = (
                    f"本轮月印量{volume[0]}—{volume[1]}页，与HP厂家建议{minimum}—{maximum}页范围"
                    f"关系为{wording[hp['relation']]}；厂家建议范围不是最低启动量或故障门槛。"
                    "Brother相应建议月印量未查明。"
                )
            elif volume is None:
                item["result"] = ("本轮月印量未确认；不能形成与厂家建议范围的关系，"
                                  "不得作低频适用性或成本胜负结论。")
            else:
                item["result"] = (f"本轮月印量{volume[0]}—{volume[1]}页已确认，但HP建议范围"
                                  f"{missing_fact_reason(hp)}，不能形成确定区间关系；"
                                  "Brother建议范围未知，不推断两款的耐用性。")
            item["decision_effect"] = "只生成区间关系与需要核实的低频维护问题，不以建议印量淘汰机型。"
    for source in model_comparison["sources"]:
        source_by_id[source["id"]] = source

    def applicable(rule: str) -> bool:
        if rule == "home_monochrome_outsource":
            return (values.get("needs_color") is False
                    and values.get("accepts_outsourced_color") is True)
        if rule == "wechat_specific_model":
            return values.get("wechat_required") is True or wechat_preferred
        if rule == "low_volume_cost_model":
            return isinstance(values.get("monthly_pages_range"), list)
        if rule == "scan_tradeoff":
            return values.get("requires_scan") is True
        if rule == "duplex_tradeoff":
            return values.get("requires_auto_duplex") is True
        if rule == "budget_tradeoff":
            return type(values.get("budget_max_cny")) is int
        if rule == "reliability_limit":
            return reliability_required
        if rule == "wechat_region_limit":
            return values.get("wechat_required") is True or wechat_preferred
        if rule == "color_required":
            return values.get("needs_color") is True
        return False

    decision_views = []
    for decision in model_comparison["conditional_decisions"]:
        rule = decision.get("rule")
        if rule == "scan_or_duplex_required":
            scan, duplex = values.get("requires_scan"), values.get("requires_auto_duplex")
            applicability = ("applicable" if scan is True or duplex is True else
                             "not_applicable" if scan is False and duplex is False else "unknown")
        elif rule == "simple_print_only":
            needs_color = values.get("needs_color")
            outsource = values.get("accepts_outsourced_color")
            scan, duplex = values.get("requires_scan"), values.get("requires_auto_duplex")
            applicability = ("applicable" if (needs_color is False and outsource is True
                                               and scan is False and duplex is False) else
                             "not_applicable" if (needs_color is True or outsource is False
                                                  or scan is True or duplex is True) else "unknown")
        elif rule == "outside_mainland_china":
            applicability = ("applicable" if region_scope == "outside_mainland_china" else
                             "not_applicable" if region_scope == "mainland_china" else "unknown")
        else:
            applicability = "unknown"
        eligibility = criteria_by_model.get(decision.get("model"), {}).get("eligibility")
        hard_excluded = eligibility == "excluded_by_hard_condition"
        if applicability == "applicable" and (hard_excluded or condition_view["conflicts"]):
            applicability = "not_applicable"
        elif applicability == "applicable" and (
                condition_view["unresolved_hard_conditions"] or unmodeled_hard or
                eligibility == "pending_hard_evidence"):
            applicability = "unknown"
        # 不能只凭DEC历史静态句子宣称某项硬功能已满足。
        if applicability == "applicable" and rule == "scan_or_duplex_required":
            required_checks = [
                model_check("M232dw", criterion)
                for required, criterion in (
                    (values.get("requires_scan"), "C-SCAN"),
                    (values.get("requires_auto_duplex"), "C-DUPLEX"))
                if required is True
            ]
            if any(check is None or check["relation"] != "match" for check in required_checks):
                applicability = "unknown"
        # 历史「购买前条件」不应继续固化原案1000元。
        current_budget = values.get("budget_max_cny")
        normalized_budget = (f"不超过{current_budget}元"
                             if type(current_budget) is int else "与尚未设置的预算核对")
        volume = values.get("monthly_pages_range")
        normalized_volume = (f"{volume[0]}至{volume[1]}页/月"
                             if isinstance(volume, (list, tuple)) and len(volume) == 2
                             else "尚未确认的月印量")
        conditions_before_purchase = [
            note.replace("不超过1000元", normalized_budget)
                .replace("0至50页/月", normalized_volume)
            for note in decision["conditions_before_purchase"]
        ]
        when = decision.get("when", "").replace("不超过1000元", normalized_budget)
        reason = decision["reason"]
        if decision.get("id") == "DEC-01":
            required_evidence = [
                (label, model_check("M232dw", criterion))
                for enabled, label, criterion in (
                    (values.get("requires_scan"), "扫描", "C-SCAN"),
                    (values.get("requires_auto_duplex"), "自动双面", "C-DUPLEX"))
                if enabled is True
            ]
            available = [label for label, check in required_evidence
                         if check is not None and check["relation"] == "match"]
            missing = [f"{label}：{missing_fact_reason(check)}" for label, check in required_evidence
                       if check is None or check["relation"] != "match"]
            if missing:
                reason = (f"本轮要求的{ '、'.join(label for label, _ in required_evidence) }"
                          f"仍有未核事项（{'；'.join(missing)}）；"
                          f"{'、'.join(available) + '已有型号证据，但' if available else ''}"
                          "不能继续使用历史功能优势宣布全部硬条件满足。")
            elif required_evidence:
                reason = (f"HP现有有效型号证据支持{'、'.join(available)}；"
                          "仍缺真实所售配置、地区价格和长期体验，不批准购买。")
        if decision.get("id") == "DEC-02":
            budget_check = model_check("HL-L1238W", "C-BUDGET")
            if budget_check and budget_check["relation"] in ("above", "at_or_below"):
                relation = "高于" if budget_check["relation"] == "above" else "不高于"
                budget_clause = (f"厂家建议价{budget_check['product_value']}元"
                                 f"{relation}当前{current_budget}元预算")
            elif type(current_budget) is int:
                budget_clause = (f"当前预算{current_budget}元已确认，但厂家建议价"
                                 f"{missing_fact_reason(budget_check)}，无法比较")
            else:
                budget_clause = "本轮尚未设置预算，不形成建议价大小关系"
            reason = ("Brother HL-L1238W有中国区微信小程序和鼓粉分离的厂家资料；"
                      f"{budget_clause}；实际地区到手价与所售配置仍未知。")
        decision_views.append({**decision, "reason": reason, "when": when,
                                "applicability": applicability,
                               "hard_condition_override_blocked": hard_excluded,
                               "model_eligibility": eligibility,
                               "conditions_before_purchase": conditions_before_purchase})
    model_comparison["conditional_decisions"] = decision_views
    model_comparison["active_conditional_decisions"] = [x for x in decision_views
                                                          if x["applicability"] == "applicable"]
    model_comparison["unknown_conditional_decisions"] = [x for x in decision_views
                                                           if x["applicability"] == "unknown"]
    model_comparison["deployment_region_scope"] = region_scope
    model_comparison["deployment_region_provided"] = bool(region)
    rendered = []
    for claim in data["claims"]:
        if not isinstance(claim, dict) or not applicable(claim.get("rule")):
            continue
        source_ids = claim["support_ids"]
        if not isinstance(source_ids, list) or any(x not in source_by_id for x in source_ids):
            raise ValueError("unmapped_research_source")
        description = claim["description"]
        if claim["id"] in ("CASE-04", "CASE-05"):
            feature = "扫描" if claim["id"] == "CASE-04" else "自动双面"
            criterion = "C-SCAN" if claim["id"] == "CASE-04" else "C-DUPLEX"
            hp_check = model_check("M232dw", criterion)
            if criteria_view["excluded_models"]:
                description = (f"当前{feature}的厂家功能资料只能作为规格背景；"
                               "有本轮硬条件不符的型号先排除，功能优势不能使其重新入选。")
            elif hp_check is None or hp_check["relation"] != "match":
                description = (f"本轮要求{feature}，但HP对应型号事实"
                               f"{missing_fact_reason(hp_check)}，本轮不能认定满足；"
                               "Brother相应能力也未核实，需补证据后重算。")
        if claim["id"] == "CASE-03":
            volume = values.get("monthly_pages_range")
            hp = next((check for check in criteria_by_model["M232dw"]["checks"]
                       if check["criterion_id"] == "C-VOLUME"), None)
            word = {"below": "整体低于", "above": "整体高于", "equal": "与之相等",
                    "within": "位于其中", "contains": "覆盖其全部", "overlap": "部分重叠"}
            relation = word.get(hp["relation"] if hp else None)
            if relation:
                lo, hi = hp["product_value"]
                description = (
                    f"本轮月印量{volume[0]}—{volume[1]}页，与HP建议{lo}—{hi}页关系为{relation}，"
                    "建议范围不是最低使用门槛。Brother鼓粉分离；缺现价、维护和闲置实测，不能断言谁更耐用或省钱。")
            else:
                description = (f"用户本轮月印量{volume[0]}—{volume[1]}页已确认；"
                               f"HP建议月印量{missing_fact_reason(hp)}，当前区间关系未知。"
                               "Brother鼓粉分离，但缺现价与维护实测，不据此判断胜负。")
        if claim["id"] == "CASE-06":
            budget = values.get("budget_max_cny")
            brother = next((check for check in criteria_by_model["HL-L1238W"]["checks"]
                            if check["criterion_id"] == "C-BUDGET"), None)
            if brother and brother["relation"] in ("above", "at_or_below"):
                relation = "高于" if brother["relation"] == "above" else "不高于"
                price_clause = f"Brother厂家建议价{brother['product_value']}元，{relation}该预算"
            else:
                price_clause = f"Brother厂家建议价{missing_fact_reason(brother)}，无法比较"
            description = (f"本轮预算上限{budget}元已确认；{price_clause}；"
                           "HP建议价和双方地区现价均未核。建议价关系仅供研究，不能判定实际预算通过或排除。")
        elif "{budget_max_cny}" in description:
            description = description.format(budget_max_cny=values.get("budget_max_cny"))
        rendered.append({
            "id": claim["id"], "reason": description,
            "applies_when": claim["applies_when"],
            "basis": claim["basis"], "counter_evidence": claim["counter"],
            "evidence": [{
                "source_id": x, "source_group": source_by_id[x]["source_group"],
                "source_url": source_by_id[x]["url"],
                "source_fact": source_by_id[x]["claim"],
                "source_limit": source_by_id[x]["counter"],
                "scope": source_by_id[x]["scope"],
                "fact_audit": source_by_id[x]["fact_audit"],
            } for x in source_ids],
            "review_status": "research_only_pending_independent_review",
            "actual_purchase_effect": "none_unapproved",
        })

    # 有据认知只产生解释与必要澄清，不能改变参数资格、实价或购买批准。
    from .printer_effect_probe import derive_printer_decision_effects
    decision_effects = derive_printer_decision_effects(
        values=values, criteria=criteria_view, model_comparison=model_comparison,
        wechat_preferred=wechat_preferred, reliability_required=reliability_required,
    )
    return {
        **base,
        "decision_effects": decision_effects,
        "research_captured_on": data["captured_on"],
        "usage_limit": data["usage_limit"],
        "model_comparison": model_comparison,
        "criteria_comparison": criteria_view,
        "shared_research_snapshot": shared_research_snapshot,
        "reasons": rendered, "reason_count": len(rendered),
        "limits": [
            "这是原案研究取舍，不是完成独立审批的推荐依据",
            "只有厂家型号和有限历史研究事实，真实平台商品/所选配置绑定仍为0",
            "没有地区有效成交价、券/库存/运费，也没有实际设备微信连接验证",
            "本轮答案改变后重新生成理由，不从历史轮次继承失效理由",
        ],
    }
