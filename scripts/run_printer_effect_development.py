"""固定公开开发组的普通参数筛选 vs 有据认知补充，默认完全离线。

用法：python3 -m scripts.run_printer_effect_development --output reports/printer_cognition_dev_20261115_run01.json
不能把本脚本输出当36条独立保留集成绩；参考判断在输入JSON中预先明示。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from shopping_decision.printer_effect_probe import pair_development_views
from shopping_decision.real_printer_case import compare_case_research

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = ROOT / "evaluation/printer_cognition_dev_20261115.json"
INPUTS = (
    "evaluation/printer_cognition_dev_20261115.json",
    "knowledge/printer_selection_criteria.json",
    "knowledge/real_printer_case_research_20261113.json",
    "knowledge/real_printer_case_comparison_20261115.json",
    "shopping_decision/printer_effect_probe.py",
    "shopping_decision/real_printer_case.py",
    "scripts/run_printer_effect_development.py",
)


def run(*, cases_path: Path = DEFAULT_CASES) -> dict:
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    if (payload.get("status") != "open_development_cases_not_independent_holdout"
            or payload.get("schema_version") != 1 or not isinstance(payload.get("cases"), list)
            or len(payload["cases"]) < 6):
        raise ValueError("invalid_unfrozen_development_case_set")
    details = []
    packets = []
    review_key = []
    review_form = []
    for sample in payload["cases"]:
        result = compare_case_research(sample["values"])
        paired = pair_development_views(result)
        if not paired["same_hard_eligibility"]:
            raise ValueError("development_arm_eligibility_mismatch:" + sample["id"])
        if paired["purchase_recommendation_approved"] or paired["transactions_enabled"]:
            raise ValueError("unsafe_experiment_action")
        packet_ids = {}
        for arm, view in (("baseline", paired["direct_parameter_screen"]),
                          ("cognition", paired["cognition_augmented"])):
            packet_id = hashlib.sha256((sample["id"] + ":" + arm).encode()).hexdigest()[:16]
            packet_ids[arm] = packet_id
            # 待评包只含这一组的回答/共同事实，无另一组、参考或成绩。
            packets.append({"packet_id": packet_id, "case_id": sample["id"],
                            "values": sample["values"],
                            "output": {k: view[k] for k in (
                                "models", "questions", "source_snapshot", "criterion_sources",
                                "condition_conflicts", "known_limits", "task_output",
                                "live_price_verified")}})
            review_key.append({"packet_id": packet_id, "case_id": sample["id"], "arm": arm})
        review_form.append({
            "case_id": sample["id"], "packet_ids": packet_ids,
            "tasks": [{"task_id": sample["id"] + ":T" + str(i),
                       "open_reference": ref, "independent_reference_status": "pending_evaluator_review",
                       "baseline": {"judgment": None, "output_location": None, "reason": None},
                       "cognition": {"judgment": None, "output_location": None, "reason": None}}
                      for i, ref in enumerate(sample["reference_from_sources"], 1)],
            "review_status": "unscored_executor_must_not_sign_independent_result",
        })
        details.append({
            "id": sample["id"], "origin": sample["origin"],
            "values": sample["values"], "reference_prewritten": sample["reference_from_sources"],
            "baseline": paired["direct_parameter_screen"],
            "cognition": paired["cognition_augmented"],
            "same_hard_eligibility": paired["same_hard_eligibility"],
            "source_backed_context_count": paired["source_backed_context_count"],
            "newly_acquired_source_count": paired["newly_acquired_source_count"],
            "incremental_decision_effect_proven": paired["incremental_decision_effect_proven"],
            "observed_effect": "prior_source_context_restructured_for_explanation; no_proven_new_decision",
            "primary_success_rate": None,
        })
    return {
        "status": "executor_development_diagnostic_only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_hashes_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in INPUTS
        },
        "case_count": len(details),
        "paired_hard_eligibility_equal_count": sum(r["same_hard_eligibility"] for r in details),
        "cases_with_at_least_two_source_backed_contexts":
            sum(r["source_backed_context_count"] >= 2 for r in details),
        "newly_acquired_source_count": 0,
        "incremental_decision_effect_proven_count": 0,
        "original_real_case_count": sum(r["origin"] == "one_real_user_case_with_unanswered_conditions"
                                        for r in details),
        "development_modified_condition_count": sum(r["origin"] == "simulated_changed_answer"
                                                    for r in details),
        "independent_holdout_tested": False,
        "independent_holdout_denominator": 0,
        "task_success_rate_baseline": None,
        "task_success_rate_cognition": None,
        "measured_improvement": None,
        "human_confirmed": False,
        "verified_marketplace_identities": 0,
        "verified_regional_quotes": 0,
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "method_limit": "两组已使用相同规格/硬条件，认知组增加有来源的解释。开放开发组可检查功能但不能独立验证增益；36个新保留场景与门槛冻结归评估者。",
        "cases": details,
        "observable_target": "局部判断/必要澄清任务；不是型号资格差异或真人阅读理解",
        "review_packets": sorted(packets, key=lambda row: row["packet_id"]),
        "review_key_do_not_show_to_blind_reviewer": review_key,
        "open_task_review_form": review_form,
        "review_rule": ("评估者先从原始资料确认允许判断、必要问题、禁止主张及争议处理，"
                        "再仅看单个待评包的实际输出逐项判定并标位置/理由；不能从另一组或完整结果补分。"
                        "硬资格一致只核控制；共同事实已有说明可获同等认可，允许零差异。"
                        "来源条数、解释条数与本表均不自动生成成绩。"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run()
    if args.output:
        dest = args.output.resolve()
        packets_dest = dest.with_name(dest.stem + "_review_packets.json")
        if dest.exists() or packets_dest.exists():
            raise FileExistsError("refuse_overwrite_existing_report_or_packets")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with packets_dest.open("x", encoding="utf-8") as stream:
            json.dump({"status": "open_development_single_arm_review_not_holdout",
                       "packets": report.pop("review_packets")}, stream, ensure_ascii=False, indent=2)
        report["review_packets_file"] = str(packets_dest)
        with dest.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("cases", "review_packets", "review_key_do_not_show_to_blind_reviewer",
                                   "open_task_review_form")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
