"""共享的只读研究投影：对已审选择准则的全部候选作来源关联与下一动作整理。

只消费受校验的条件与来源快照；不凭历史案例ID生成结论，不认定现价、订单或购买资格。
旧打印机CASE/DEC叙述可在上层保留作兼容输出；新研究结果只读取当前事实检查。
"""
from __future__ import annotations

from datetime import date
from copy import deepcopy

from .selection_criteria import evaluate_selection


def render_research_snapshot(values: dict, checks: dict) -> dict:
    """对同一份有效资格检查生成可审报告；不重新计算或变更其门禁。"""
    if not isinstance(values, dict) or not isinstance(checks, dict):
        raise ValueError("invalid_research_snapshot_input")
    sources = checks.get("source_registry")
    models = checks.get("models")
    category = checks.get("category")
    if (not isinstance(sources, dict) or not isinstance(models, list)
            or (category is not None and not isinstance(category, str))):
        raise ValueError("invalid_research_snapshot_checks")
    request_category = values.get("category")
    if request_category is not None and request_category != category:
        raise ValueError("research_snapshot_category_mismatch")

    candidate_rows = []
    evidence_judgments = []
    missing_sources = set()
    for model in models:
        if not isinstance(model, dict) or not isinstance(model.get("model_id"), str):
            raise ValueError("invalid_research_snapshot_model")
        model_id = model["model_id"]
        material_checks = []
        for check in model.get("checks", []):
            source_refs = []
            for source_id in check.get("source_ids", []):
                source = sources.get(source_id)
                if not isinstance(source, dict):
                    raise ValueError("unmapped_research_snapshot_source:" + str(source_id))
                source_refs.append({
                    "id": source_id,
                    "url": source["url"],
                    "source_group": source.get("group"),
                    "type": source.get("type"),
                    "checked_on": source.get("checked_on"),
                    "published_on": source.get("published_on"),
                    "limit": source["limit"],
                })
            relation = check["relation"]
            is_current_fact = (check["evidence_state"] == "manufacturer_fact_research_only"
                               and bool(source_refs) and relation not in
                               ("unknown", "incomparable_unit", "workflow_unconfirmed",
                                "other_workflow_unverified", "deployment_region_unconfirmed",
                                "deployment_outside_verified_scope"))
            entry = {
                "criterion_id": check["criterion_id"],
                "user_field": check["user_field"],
                "user_value": deepcopy(check["user_value"]),
                "product_field": check["product_field"],
                "product_value": deepcopy(check["product_value"]),
                "unit": check["unit"],
                "relation": relation,
                "kind": check["kind"],
                "evidence_state": check["evidence_state"],
                "source_refs": source_refs,
                "has_applicable_model_fact": is_current_fact,
                "counter": check["unknown_or_counter"],
            }
            material_checks.append(entry)
            if is_current_fact:
                evidence_judgments.append({
                    "model_id": model_id,
                    "criterion_id": entry["criterion_id"],
                    "relation": relation,
                    "user_value": deepcopy(entry["user_value"]),
                    "product_value": deepcopy(entry["product_value"]),
                    "unit": entry["unit"],
                    "source_refs": deepcopy(source_refs),
                    "counter": entry["counter"],
                    "status": "attributed_model_fact_for_research_only",
                })
            else:
                missing_sources.add(model_id + ":" + check["criterion_id"])
        candidate_rows.append({
            "model_id": model_id,
            "brand": model.get("brand"),
            "eligibility": model["eligibility"],
            "hard_failed": list(model["hard_failed"]),
            "hard_unknown": list(model["hard_unknown"]),
            "checks": material_checks,
            "platform_identity_verified": False,
            "regional_live_price_verified": False,
            "purchase_recommendation_approved": False,
        })

    # R2: question provenance is a typed contract, never inferred from punctuation.
    # Legacy case-research conflict details are attached after the criteria evaluator.
    conflicts = list(checks.get("user_condition_conflicts", []))
    question_items = [{"text": text, "kind": "user_conflict", "field": "requirements"}
                      for text in conflicts]
    question_items.extend(deepcopy(checks.get("question_items", [])))
    typed_text = {item["text"] for item in question_items}
    # Older callers may append evidence limitations through the historical strings.
    question_items.extend({"text": text, "kind": "external_evidence", "field": "unspecified"}
                          for text in checks.get("questions", []) if text not in typed_text)
    question_items = list({item["text"]: item for item in question_items}.values())
    user_questions = [item["text"] for item in question_items
                      if item["kind"] in ("user_input", "user_conflict")]
    evidence_limitations = [item["text"] for item in question_items
                            if item["kind"] == "external_evidence"]
    if conflicts:
        next_action = "resolve_user_condition_conflict"
    elif user_questions:
        next_action = "clarify_user_conditions"
    elif any(row["hard_failed"] for row in candidate_rows):
        next_action = "review_excluded_conditions_and_other_candidates"
    elif any(row["hard_unknown"] for row in candidate_rows):
        next_action = "verify_missing_hard_model_evidence"
    else:
        next_action = "verify_sale_identity_region_price_and_optional_preferences"

    # 排序只影响展示，不影响计算。第三个候选应被计算并完整留在审计里。
    visible = candidate_rows[:3]
    hidden = [{"model_id": row["model_id"], "reason": "display_limit_three"}
              for row in candidate_rows[3:]]
    result = {
        "schema_version": 1,
        "status": "research_snapshot_only_not_purchase",
        "category": category,
        "category_binding": checks.get("category_binding"),
        "criteria_version": checks.get("criteria_version"),
        "criteria_sha256": checks.get("criteria_sha256"),
        "fact_captured_on": checks.get("fact_captured_on"),
        "evaluated_at": date.today().isoformat(),
        "total_candidate_count": len(candidate_rows),
        "displayed_candidates": deepcopy(visible),
        "hidden_candidates": hidden,
        "all_candidates": candidate_rows,
        "judgments": evidence_judgments,
        "next_action": next_action,
        "necessary_user_questions": list(dict.fromkeys(user_questions)),
        "question_items": question_items,
        "evidence_missing": sorted(missing_sources),
        "evidence_limitations": list(dict.fromkeys(evidence_limitations)),
        "source_registry": deepcopy(sources),
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "verified_platform_identity_count": 0,
        "verified_live_quote_count": 0,
        "note": "研究投影只复述本轮有效检查；来源/型号事实不等于所售配置、当前价或购买许可",
    }
    from .printer_decision_plan import build_printer_decision_plan
    plan = build_printer_decision_plan(values, result, conflicts=conflicts)
    if plan is not None:
        result["decision_plan"] = plan
    return result


def compare_research_snapshot(values: dict, *, config: dict | None = None,
                              today: date | None = None) -> dict:
    """允许调用者注入同一受校验的候选/来源/准则快照，不能注入任意已批准事实。"""
    if not isinstance(values, dict):
        raise ValueError("invalid_research_snapshot_input")
    checks = evaluate_selection(values, config=config, today=today)
    result = render_research_snapshot(values, checks)
    result["evaluated_at"] = (today or date.today()).isoformat()
    return result
