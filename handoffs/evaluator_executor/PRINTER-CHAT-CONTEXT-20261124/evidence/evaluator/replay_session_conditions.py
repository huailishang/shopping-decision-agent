"""Replay independently built synthetic data through the public chat renderer."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from shopping_decision.chat_bridge import confirmed_values, render_chat, submit_message
from shopping_decision.dialogue_flow import new_dialogue
from shopping_decision.evidence_comparison import SAFE_FLAGS, digest


def source(source_id, region, models):
    return {
        "id": source_id,
        "url": f"https://review.invalid/{source_id}",
        "type": "official_exact_model_document",
        "allowed_use": "model_research_short_summary",
        "scope_region": region,
        "scope_models": models,
        "captured_on": "2026-11-22",
        "observed_at": "2026-11-22T12:00:00+08:00",
        "valid_until": "2026-11-24",
        "limitations": "离线合成来源",
    }


def fact(fact_id, model, src, dimension, unit, value, kind):
    return {
        "id": fact_id, "candidate_id": model, "source_id": src,
        "dimension": dimension, "unit": unit, "value": value,
        "kind": kind, "statement": "独立合成输入", "limitations": "无商品证明",
    }


def cases():
    state = new_dialogue()
    for field, answer in (
        ("category", "打印机"),
        ("usage", "家用学习资料"),
        ("wechat_required", "必须"),
        ("device_deployment_region", "日本"),
        ("delivery_region", "河南"),
        ("budget_max_cny", "1000"),
    ):
        state = submit_message(state, field, answer)
    model = "review-model"
    price = source("practice-shop", "河南", [model])
    price.update(quote_sku="review-sku", quote_merchant="离线模拟商家", quote_region="河南")
    bundle = {
        "schema_version": 1, "request_id": "independent-print", "category": "printer",
        "as_of": "2026-11-23", "region": "河南", "dialogue_version": state["version"],
        "confirmed_values_sha256": digest(confirmed_values(state)),
        "candidates": [{"id": model}],
        "requirements": [
            {"id": "ceiling", "dimension": "cost", "unit": "CNY",
             "op": "lte", "value": 1000, "importance": "hard"},
            {"id": "wx", "dimension": "wechat_print", "unit": "bool",
             "op": "eq", "value": True, "importance": "hard"},
        ],
        "sources": [price, source("practice-japan", "日本", [model])],
        "facts": [
            fact("device-price", model, "practice-shop", "cost", "CNY", 900, "live_quote"),
            fact("wechat-support", model, "practice-japan", "wechat_print", "bool", True,
                 "official_feature"),
        ],
    }
    absent = deepcopy(bundle)
    absent["facts"][1]["value"] = False
    reversed_condition = deepcopy(absent)
    reversed_condition["requirements"][1]["value"] = False
    omitted_condition = deepcopy(absent)
    omitted_condition["requirements"].pop()
    reordered = deepcopy(bundle)
    reordered["candidates"].insert(0, {"id": "other"})
    reordered["sources"].append(source("other-henan", "河南", ["other"]))
    reordered["facts"].extend([
        fact("irrelevant-quote", model, "practice-shop", "wechat_print", "CNY", 42, "live_quote"),
        fact("unrelated-feature", "other", "other-henan", "wechat_print", "bool", True,
             "official_feature"),
    ])
    for collection in ("requirements", "facts", "sources"):
        reordered[collection].reverse()
    mini = submit_message(deepcopy(state), "wechat_workflow", "微信小程序直接打印")
    generic_only = deepcopy(bundle)
    generic_only["dialogue_version"] = mini["version"]
    generic_only["confirmed_values_sha256"] = digest(confirmed_values(mini))
    matched = deepcopy(generic_only)
    matched["requirements"].append({"id": "mini", "dimension": "wechat_miniprogram",
                                    "unit": "bool", "op": "eq", "value": True,
                                    "importance": "hard"})
    matched["facts"].append(fact("miniprogram-support", model, "practice-japan",
                                 "wechat_miniprogram", "bool", True, "official_feature"))
    return {
        "positive_control": (state, bundle), "negative_control": (state, absent),
        "reordered_two_candidates": (state, reordered),
        "reversed_required_feature": (state, reversed_condition),
        "omitted_required_feature": (state, omitted_condition),
        "generic_fact_for_specific_workflow": (mini, generic_only),
        "specific_workflow_control": (mini, matched),
    }


def replay(state, bundle):
    analysis = {"recommendation": {"status": "defer"}, "verified_research_bundle": bundle}
    with (
        patch("shopping_decision.chat_bridge._analysis", return_value=analysis),
        patch("shopping_decision.chat_bridge.date") as clock,
    ):
        clock.today.return_value = date(2026, 11, 23)
        view = render_chat(deepcopy(state))
    report = json.loads(view["report_json"])
    public = report["public_decision"] or {}
    return {
        "text": view["result_text"], "claims": public.get("claims", []),
        "assessments": public.get("assessments", []),
        "chat_flags": {key: report.get(key) for key in SAFE_FLAGS[:3]},
        "public_flags": {key: public.get(key) for key in SAFE_FLAGS} if public else {},
    }


def status(result, requirement, model="review-model"):
    return next((claim["status"] for claim in result["claims"]
                 if claim["requirement_id"] == requirement and claim["candidate_id"] == model), None)


def main():
    inputs = cases()
    results = {name: replay(state, bundle) for name, (state, bundle) in inputs.items()}
    moved = results["reordered_two_candidates"]
    reversed_condition = results["reversed_required_feature"]
    omitted = results["omitted_required_feature"]
    generic_only = results["generic_fact_for_specific_workflow"]
    checks = {
        "positive_control": status(results["positive_control"], "wx") == "met",
        "negative_control": status(results["negative_control"], "wx") == "failed",
        "reordered_candidates_keep_own_evidence": status(moved, "ceiling") == "met"
        and status(moved, "wx") == "met" and status(moved, "wx", "other") == "unknown"
        and all(claim["claim_id"] in moved["text"] for claim in moved["claims"]),
        "reversed_required_feature_cannot_be_met": status(reversed_condition, "wx") != "met"
        and all(row["research_status"] != "eligible_for_research"
                for row in reversed_condition["assessments"]),
        "omitted_required_feature_cannot_be_eligible": all(
            row["research_status"] != "eligible_for_research" for row in omitted["assessments"]),
        "generic_feature_cannot_resolve_specific_workflow": status(generic_only, "mini") != "met"
        and all(row["research_status"] != "eligible_for_research"
                for row in generic_only["assessments"]),
        "specific_workflow_control": status(results["specific_workflow_control"], "mini") == "met"
        and status(results["specific_workflow_control"], "ceiling") == "met",
        "safety_flags": all(value is False for result in results.values()
                            for key in ("chat_flags", "public_flags")
                            for value in result[key].values()),
    }
    print(json.dumps({"checks": checks, "inputs": inputs, "results": results},
                     ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
