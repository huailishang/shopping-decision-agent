"""只读本轮打印机条件回放：不联网、不读取Key、不覆盖旧文件。

运行:
PYTHONUTF8=1 python3 -m scripts.cognition_case_replay --output reports/cognition_case_replay_20261115_run01.json
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from shopping_decision.selection_criteria import CRITERIA_PATH
from shopping_decision.real_printer_case import RESEARCH_PATH, COMPARISON_PATH


ORIGINAL = {
    "category": "printer", "usage": "家用黑白打印",
    "budget_max_cny": 1000, "budget_scope": "unknown",
    "monthly_pages_range": [0, 50], "needs_color": False,
    "accepts_outsourced_color": True, "wechat_required": None,
    "wechat_workflow": "unknown", "requires_scan": None,
    "requires_auto_duplex": None,
    "requirements": ["月打印0至50页、家里黑白为主，偶尔彩印可去打印店，希望微信打印、可靠耐用，比较兄弟与惠普"],
}

TURNS = [
    ("R0_original", ORIGINAL),
    ("R1_scan_required_synthetic", {"requires_scan": True}),
    ("R2_duplex_required_scan_revoked_synthetic",
     {"requires_scan": False, "requires_auto_duplex": True}),
    ("R2b_duplex_revoked_synthetic", {"requires_auto_duplex": False}),
    ("R3_home_color_required_synthetic", {"needs_color": True}),
    ("R4_restore_and_require_miniprogram_synthetic",
     {"needs_color": False, "wechat_required": True, "wechat_workflow": "miniprogram"}),
    ("R4b_wechat_optional_accept_app_synthetic",
     {"wechat_required": False, "wechat_workflow": "transfer_to_app"}),
    ("R5_budget_down_500_synthetic", {"budget_max_cny": 500}),
    ("R5b_budget_and_wechat_cleared_synthetic",
     {"budget_max_cny": None, "wechat_required": None, "wechat_workflow": "unknown",
      "requirements": ["可靠耐用，重点比较兄弟与惠普"]}),
    ("R6_budget_3000_pages_250_300_synthetic",
     {"budget_max_cny": 3000, "monthly_pages_range": [250, 300]}),
    ("R6b_budget_equal_msrp_synthetic", {"budget_max_cny": 1906}),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True,
                        help="需为尚不存在的新 JSON 文件；不覆盖历史")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite existing output")
    turns = [{"text": label, "answers": changes} for label, changes in TURNS]
    command = [sys.executable, "-m", "shopping_decision.dialogue_flow", "--real-printer-case"]
    completed = subprocess.run(command,
                               input="".join(json.dumps(x, ensure_ascii=False) + "\n" for x in turns),
                               capture_output=True, encoding="utf-8", text=True, timeout=75)
    if completed.returncode:
        raise SystemExit("CLI failed: " + completed.stderr[-3000:])
    lines = [json.loads(line) for line in completed.stdout.splitlines()]
    if len(lines) != len(turns) + 1 or lines[0].get("status") != "ready":
        raise RuntimeError("unexpected_replay_response_count")
    observations = []
    for ((label, changes), turn) in zip(TURNS, lines[1:]):
        context = turn["real_printer_case_research"]
        selection = context["criteria_comparison"]
        source_result = turn.get("comparison", {})
        if (selection.get("purchase_recommendation_approved") is not False
                or selection.get("transactions_enabled") is not False
                or context.get("real_sale_identity_verified_count") != 0
                or context.get("regional_live_quote_count") != 0):
            raise RuntimeError("safety_or_real_data_gate_regressed:" + label)
        budget_cmp = next(c for c in context["model_comparison"]["comparisons"]
                          if c["dimension"] == "budget")
        volume_cmp = next(c for c in context["model_comparison"]["comparisons"]
                          if c["dimension"] == "low_volume_fit")
        observations.append({
            "round": label, "origin": "known_original_requirements" if label == "R0_original"
                     else "explicitly_synthetic_condition_change",
            "changes": changes, "session_version": turn["version"],
            "latest_conditions": source_result.get("comparison", {}).get("comparison", {}).get("constraints"),
            "source_mode": source_result.get("source_mode"),
            "criteria_sha256": selection["criteria_sha256"],
            "criteria_version": selection["criteria_version"],
            "model_results": [{
                "model": model["model_id"], "eligibility": model["eligibility"],
                "hard_failed": model["hard_failed"], "hard_unknown": model["hard_unknown"],
                "relations": {c["criterion_id"]: c["relation"] for c in model["checks"]},
                "values": {c["criterion_id"]: {"user": c["user_value"], "product": c["product_value"],
                                                "unit": c["unit"], "source_ids": c["source_ids"]}
                           for c in model["checks"]},
            } for model in selection["models"]],
            "current_budget_explanation": budget_cmp["result"],
            "current_volume_explanation": volume_cmp["result"],
            "active_conditional_decisions": [d["id"] for d in
                                            context["model_comparison"]["active_conditional_decisions"]],
            "reason_ids": [x["id"] for x in context["reasons"]],
            "reason_texts": [{"id": x["id"], "reason": x["reason"]}
                             for x in context["reasons"]],
            "necessary_questions": selection["questions"],
            "purchase_recommendation_approved": False,
            "transactions_enabled": False,
        })
    lookup = {item["round"]: item for item in observations}
    if set(m["eligibility"] for m in lookup["R3_home_color_required_synthetic"]["model_results"]) != {
            "excluded_by_hard_condition"}:
        raise RuntimeError("color_hard_exclusion_failed")
    if lookup["R3_home_color_required_synthetic"]["active_conditional_decisions"]:
        raise RuntimeError("excluded_model_reactivated_by_soft_advantage")
    model = lookup["R6_budget_3000_pages_250_300_synthetic"]["model_results"][0]
    if model["relations"].get("C-BUDGET") != "at_or_below":
        raise RuntimeError("budget_3000_relation_failed")
    model_hp = lookup["R6_budget_3000_pages_250_300_synthetic"]["model_results"][1]
    if model_hp["relations"].get("C-VOLUME") != "within":
        raise RuntimeError("monthly_250_300_relation_failed")
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "offline_cli_real_entrypoint_synthetic_followups",
        "case_id": "REAL-PRINTER-H08B-20261113",
        "identity_verified_count": 0, "old20_verified": 0, "regional_quote_count": 0,
        "purchase_recommendation_approved": False, "transactions_enabled": False,
        "new_external_api_calls": 0,
        "source_artifacts_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (CRITERIA_PATH, RESEARCH_PATH, COMPARISON_PATH)},
        "passed_rounds": len(observations), "rounds": observations,
    }
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({
        "rounds": len(observations), "budget_3000": model["relations"].get("C-BUDGET"),
        "volume_250_300": model_hp["relations"].get("C-VOLUME"),
        "color_exclusions": len(lookup["R3_home_color_required_synthetic"]["model_results"]),
        "purchase_approved": False, "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
