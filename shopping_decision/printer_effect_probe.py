"""真实打印机案例的有限认知增量：只补有据取舍/关键澄清，不修改型号资格或授权。

本模块只消费现有 compare_case_research 已校验过的厂家资料与资格检查。
不会读取账号/密钥，不发起网络请求，不推断平台SKU、现价或耐用排名。
"""
from __future__ import annotations

from copy import deepcopy
import math


def _source_refs(source_index: dict, *identifiers: str) -> list[dict]:
    refs = []
    for identifier in identifiers:
        row = source_index.get(identifier)
        if not isinstance(row, dict) or not isinstance(row.get("url"), str) or not row["url"].startswith("https://"):
            continue
        if "status" in row or "valid_until" in row:
            raise ValueError("unsupported_model_comparison_source_validity:" + identifier)
        refs.append({
            "source_id": identifier, "url": row["url"],
            "source_group": row.get("source_group"),
            "scope": row.get("scope"), "audit": row.get("fact_audit"),
            "counter": row.get("counter"),
            "captured_on": row.get("captured_on"),
            "validity": "dated_research_summary_no_live_validity_verified",
        })
    return refs


def derive_printer_decision_effects(*, values: dict, criteria: dict,
                                    model_comparison: dict,
                                    wechat_preferred: bool = False,
                                    reliability_required: bool = False) -> dict:
    """返回待独立评审的判断与问题；没有观测成绩时，增益保持未知。"""
    sources = {row["id"]: row for row in model_comparison.get("sources", [])
               if isinstance(row, dict) and isinstance(row.get("id"), str)}
    by_model = {row["model_id"]: row for row in criteria.get("models", [])}
    judgments = []
    questions = []
    conflicts = criteria.get("user_condition_conflicts", [])
    required = criteria.get("normalized_required", {})
    color_conflict = bool(conflicts and (
        (required.get("color_print") is True and values.get("needs_color") is False)
        or (required.get("monochrome_print") is True and values.get("needs_color") is True)))
    wechat_conflict = bool(conflicts and (
        (any(required.get(k) for k in ("wechat_miniprogram", "wechat_transfer_to_app",
                                      "wechat_workflow_unconfirmed"))
         and values.get("wechat_required") is False)
        or (required.get("wechat_miniprogram") is True
            and values.get("wechat_workflow") == "transfer_to_app")))

    if values.get("wechat_required") is True or wechat_preferred or wechat_conflict:
        refs = _source_refs(sources, "R7", "R10")
        if len(refs) == 2:
            need_answer = not wechat_conflict and (
                (values.get("wechat_required") is True
                 and values.get("wechat_workflow") in (None, "unknown"))
                or (wechat_preferred and values.get("wechat_required") is None)
            )
            question = ("微信打印是必须还是加分？是否接受首次使用厂家App/扫码配置后再打印？"
                        if values.get("wechat_required") is None else
                        "是否能接受首次安装/使用厂家App或扫码完成绑定？微信必须在小程序内直接打印吗？")
            judgments.append({
                "id": "E-WECHAT-SETUP",
                "status": ("source_supported_with_user_condition_conflict" if wechat_conflict else
                           "source_supported_with_user_environment_unknown"),
                "claim": "Brother HL-L1238W首次启用微信畅享印需要Brother Mobile Connect配置；HP M232系列先连Wi-Fi，再用信息页二维码绑定惠普云打印。",
                "decision_effect": ("微信硬要求与确认项存在冲突，先解决冲突；不能把当前流程视为已确认。"
                                    if wechat_conflict else
                                    "无线或微信功能标签不等于开箱即用；增加首次配置与真实地区核验，而不是据此给品牌加分。"),
                "source_refs": refs, "missing": ["设备部署地区与本地网络",
                                               "本人能否接受首次配置", "实际连通验证"],
                "needs_user_answer_now": need_answer,
            })
            if need_answer:
                questions.append(question)

    if values.get("monthly_pages_range") is not None:
        hp = by_model.get("M232dw", {})
        volume = next((c for c in hp.get("checks", [])
                       if c.get("criterion_id") == "C-VOLUME"), None)
        interval = volume.get("product_value") if volume else None
        valid_interval = (isinstance(interval, list) and len(interval) == 2
                          and all(type(n) in (int, float) and n >= 0
                                  and (type(n) is int or math.isfinite(n))
                                  for n in interval) and interval[0] <= interval[1])
        if (hp.get("eligibility") != "excluded_by_hard_condition"
                and volume and volume.get("evidence_state") == "manufacturer_fact_research_only"
                and valid_interval and volume.get("unit") == "pages_per_month"
                and volume.get("product_unit") == volume.get("unit")
                and volume.get("relation") == "below"):
            refs = _source_refs(sources, *volume.get("source_ids", []))
            if refs and len(refs) == len(volume.get("source_ids", [])):
                judgments.append({
                    "id": "E-VOLUME-NOT-MINIMUM",
                    "status": "source_supported_informational_only",
                    "claim": (f"本案月印量低于HP M232系列建议的{interval[0]}—{interval[1]}页/月；"
                              "建议区间不等于最低使用量，也不证明低频易损坏。"),
                    "current_check": deepcopy(volume),
                    "decision_effect": "阻止按建议月印量直接淘汰HP；低频真正的长期成本和闲置可靠性仍需独立证据。",
                    "source_refs": refs,
                    "missing": ["准确耗材现价", "真实覆盖页数", "长期闲置维护实测"],
                    "needs_user_answer_now": False,
                })
        if values.get("needs_color") is False and values.get("accepts_outsourced_color") is True:
            judgments.append({
                "id": "E-DEFER-OR-OUTSOURCE",
                "status": ("blocked_by_user_condition_conflict" if color_conflict else
                           "user_condition_only_not_product_fact"),
                "claim": ("家中彩印原话与黑白确认存在冲突；外包路线暂停判断，须先明确最新彩印要求。"
                          if color_conflict else
                          "已确认家中黑白、偶尔彩印可以外包；外包或暂缓购买是可讨论的路线，不是已核实更便宜的方案。"),
                "decision_effect": ("暂缓购买可以保留；不能把有争议的黑白/外包前提视为已确认。"
                                    if color_conflict else
                                    "避免为凑三台机器虚构商品；在现价/耗材价未知时保留暂缓选择。"),
                "source_refs": [],
                "missing": ["实际外包单价与频次", "家用机器总成本"],
                "needs_user_answer_now": color_conflict,
            })
    if color_conflict or wechat_conflict:
        questions.extend(conflicts)

    if reliability_required:
        judgments.append({
            "id": "E-RELIABILITY-UNKNOWN",
            "status": "independent_model_comparison_missing",
            "claim": "现有厂家功能、建议印量与少量历史方法资料，不能给这两款型号做长期耐用性胜负排名。",
            "decision_effect": "保留耐用性待核，不以营销防卡纸卖点或未发现投诉代替长期故障率。",
            "source_refs": [], "missing": ["同型号可迁移的长期故障/返修数据及样本方法"],
            "needs_user_answer_now": False,
        })

    model_routes = [
        {"name": m.get("model_id"), "route": "manufacturer_model_research",
         "eligibility": m.get("eligibility"), "platform_identity_verified": False,
         "regional_live_price_verified": False}
        for m in criteria.get("models", [])[:2]
    ]
    if any(j["id"] == "E-DEFER-OR-OUTSOURCE" for j in judgments):
        model_routes.append({
            "name": "暂缓购买/按需外包", "route": "non_purchase_alternative",
            "eligibility": ("blocked_by_user_condition_conflict" if color_conflict else
                            "requires_actual_cost_and_convenience_comparison"),
            "platform_identity_verified": False, "regional_live_price_verified": False,
        })
    return {
        "status": "source_limited_development_not_independent_effect",
        "judgments": judgments,
        "questions": list(dict.fromkeys(questions)),
        "routes": model_routes[:3],
        "supported_context_count": sum(bool(j["source_refs"]) for j in judgments),
        "independent_reliability_rank_available": False,
        "numeric_total_cost_available": False,
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "note": "普通筛选组与认知组须共享同一资格、型号事实、候选范围和价格未知；这里不是推荐效果分数。",
    }


def pair_development_views(case_result: dict) -> dict:
    """两组各自的待评回答；共用完整事实，不从完整结果替某组补答案。"""
    criteria = case_result["criteria_comparison"]
    effects = case_result["decision_effects"]
    sources = case_result["model_comparison"]["sources"]
    source_index = {row["id"]: row for row in sources}
    answers = []
    for model in criteria["models"]:
        for check in model["checks"]:
            answers.append({
                "id": model["model_id"] + ":" + check["criterion_id"],
                "claim": (f"{model['model_id']}：本轮条件{check['user_value']}；"
                          f"型号值{check['product_value']}，单位{check['unit']}；"
                          f"关系{check['relation']}；证据{check['evidence_state']}。"),
                "current_check": deepcopy(check),
                "source_refs": _source_refs(source_index, *check["source_ids"]),
                "counter": check["unknown_or_counter"],
            })
    common = {
        # 不能删掉原值、反证、普通筛选已有的说明/追问来制造认知优势。
        "models": deepcopy(criteria["models"]),
        "questions": list(criteria.get("questions", [])),
        "source_snapshot": deepcopy(sources),
        "criterion_sources": deepcopy(criteria["source_registry"]),
        "condition_conflicts": list(criteria.get("user_condition_conflicts", [])),
        "known_limits": list(case_result["limits"]) + [criteria["note"]],
        "task_output": {
            "answers": answers,
            "questions": list(criteria.get("questions", [])),
            "routes": [{"name": model["model_id"], "route": "manufacturer_model_research",
                        "eligibility": model["eligibility"], "platform_identity_verified": False,
                        "regional_live_price_verified": False}
                       for model in criteria["models"]],
            "purchase_recommendation_approved": False, "transactions_enabled": False,
        },
        "live_price_verified": False,
    }
    direct = deepcopy(common)
    augmented = deepcopy(common)
    augmented.update({"extra_judgments": deepcopy(effects["judgments"]),
                      "extra_questions": list(effects["questions"])})
    augmented["task_output"]["answers"].extend(deepcopy(effects["judgments"]))
    augmented["task_output"]["questions"] = list(dict.fromkeys(
        common["questions"] + effects["questions"]))
    augmented["task_output"]["routes"] = deepcopy(effects["routes"])
    return {
        "direct_parameter_screen": direct,
        "cognition_augmented": augmented,
        "same_hard_eligibility": direct["models"] == augmented["models"],
        "hard_eligibility_is_shared_control_not_effect_metric": True,
        "source_backed_context_count": effects["supported_context_count"],
        "newly_acquired_source_count": 0,
        "incremental_decision_effect_proven": False,
        "purchase_recommendation_approved": False, "transactions_enabled": False,
        "success_score": None,
        "why_unscored": "开发对照不等于评估者冻结门槛后的36条独立场景",
    }
