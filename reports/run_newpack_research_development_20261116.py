"""2026-11-16 新长包：六例开放开发对照与同源CLI/Web/Java桥接验证。

不碰36条未见样本，不写旧评估文件，不调用海纳或电商API。
"""
import base64
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from shopping_decision.real_printer_case import compare_case_research
from shopping_decision.printer_effect_probe import pair_development_views
from shopping_decision.web import evaluate_input

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "evaluation/printer_cognition_dev_20261115.json"
OUT = ROOT / "reports/newpack_research_development_20261116_run01.json"


def b64(value):
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def main():
    if OUT.exists():
        raise RuntimeError("output_exists_do_not_overwrite")
    inputs = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = []
    for case in inputs["cases"]:
        result = compare_case_research(case["values"])
        pairs = pair_development_views(result)
        snapshot = result["shared_research_snapshot"]
        assert snapshot["total_candidate_count"] == len(result["criteria_comparison"]["models"])
        assert snapshot["purchase_recommendation_approved"] is False
        assert snapshot["transactions_enabled"] is False
        assert pairs["same_hard_eligibility"] is True
        cases.append({
            "case_id": case["id"],
            "origin": case["origin"],
            "source_reference_before_run": case["reference_from_sources"],
            "normalized_input": case["values"],
            "criteria_version": snapshot["criteria_version"],
            "criteria_sha256": snapshot["criteria_sha256"],
            "snapshot_next_action": snapshot["next_action"],
            "snapshot_candidate_ids": [m["model_id"] for m in snapshot["all_candidates"]],
            "snapshot_missing_facts": snapshot["evidence_missing"],
            "baseline_task_output": pairs["direct_parameter_screen"]["task_output"],
            "cognition_task_output": pairs["cognition_augmented"]["task_output"],
            "same_hard_eligibility": pairs["same_hard_eligibility"],
            "independent_task_success": None,
            "formal_holdout": False,
        })
    original = inputs["cases"][0]["values"]
    normal_input = {
        "description": "预算1000以内，月打印0—50页，家中黑白，偶尔彩印可外包，希望微信打印，可靠耐用",
        "confirmed": True,
        "category": "printer",
        "monthly_pages_range": original["monthly_pages_range"],
        "budget_max_cny": original["budget_max_cny"],
        "needs_color": original["needs_color"],
        "accepts_outsourced_color": original["accepts_outsourced_color"],
        "wechat_required": None,
        "wechat_workflow": "unknown",
        "requirements": original["requirements"],
    }
    web_result = evaluate_input(normal_input)
    shared = web_result["real_printer_case_research"]["shared_research_snapshot"]
    assert shared["total_candidate_count"] == len(web_result["real_printer_case_research"]["criteria_comparison"]["models"])
    assert web_result["transactions_enabled"] is False
    payload = [
        normal_input["description"], "0–50", "1000", "", "false", "true", "", "",
        "\n".join(original["requirements"]), "", "unknown", "", "", "unknown", ""
    ]
    proc = subprocess.run(
        [sys.executable, "-m", "shopping_decision.desktop_bridge", *(b64(x) for x in payload)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=25, check=True,
    )
    parsed = {}
    for line in proc.stdout.splitlines():
        if "\t" in line:
            k, value = line.split("\t", 1)
            parsed[k] = base64.b64decode(value).decode("utf-8")
    raw_report = json.loads(parsed["report_json"])
    assert raw_report["real_printer_case_research"]["shared_research_snapshot"]["criteria_sha256"] == shared["criteria_sha256"]
    assert "共享研究结果" in parsed.get("audit", "") or any(
        "共享研究结果" in value for value in parsed.values()
    )
    output = {
        "run_date": "2026-11-16",
        "role": "executor",
        "type": "open_development_not_independent_effect",
        "cases": cases,
        "case_count": len(cases),
        "one_real_original_with_simulated_changes": True,
        "all_groups_share_model_fact_snapshot": True,
        "same_hard_eligibility_all": all(c["same_hard_eligibility"] for c in cases),
        "independent_reference_scored_this_round": False,
        "historical_independent_development_score": {
            "baseline_pass": 13, "cognition_pass": 14, "items": 15,
            "note": "2026-11-16 prior independent scoring only; not recalculated or upgraded"
        },
        "real_time_quote_count": 0,
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "formal_36_run": False,
        "web_shared_snapshot": {
            "candidate_count": shared["total_candidate_count"],
            "criteria_sha256": shared["criteria_sha256"],
            "next_action": shared["next_action"],
        },
        "desktop_bridge_smoke": {
            "status": parsed.get("status"),
            "report_json_chars": len(parsed["report_json"]),
            "same_source_hash": True,
            "new_section_visible_in_text": True,
            "native_swing_click_or_save": False,
        },
    }
    with OUT.open("x", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({
        "file": str(OUT.relative_to(ROOT)),
        "cases": len(cases), "shared_hard_controls": output["same_hard_eligibility_all"],
        "web": output["web_shared_snapshot"], "desktop": output["desktop_bridge_smoke"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
