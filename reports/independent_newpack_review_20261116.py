"""独立相邻探针；只读业务代码，另存本轮证据，不覆盖执行者交付。"""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shopping_decision.research_snapshot import compare_research_snapshot
from shopping_decision.real_printer_case import compare_case_research
from shopping_decision.selection_criteria import load_criteria
from shopping_decision.web import evaluate_input

TODAY = date(2026, 11, 16)
OUTPUT = ROOT / "reports/newpack_independent_20261116_run01_probes.json"


def main() -> None:
    if OUTPUT.exists():
        raise RuntimeError("independent_output_exists_do_not_overwrite")
    os.environ["PYTHONUTF8"] = "1"
    config, _ = load_criteria()
    values = {"category": "printer", "needs_color": False,
              "accepts_outsourced_color": True, "monthly_pages_range": [0, 50],
              "budget_max_cny": 1000, "budget_scope": "device_delivered",
              "wechat_required": True, "wechat_workflow": "miniprogram",
              "device_deployment_region": None}
    records = []

    def record(identifier, expectation, passed, actual):
        records.append({"id": identifier, "expectation": expectation,
                        "passed": bool(passed), "actual": actual})

    regular = compare_research_snapshot({**values, "device_deployment_region": "中国大陆"},
                                       today=TODAY)
    record("V01", "matched printer context preserves both anchors and read-only state",
           len(regular["all_candidates"]) == 2 and not regular["transactions_enabled"]
           and not regular["purchase_recommendation_approved"],
           {"category": regular["category"], "models": [m["model_id"] for m in regular["all_candidates"]]})

    try:
        wrong = compare_research_snapshot({**values, "category": "kettle"}, today=TODAY)
    except ValueError as exc:
        record("V02", "reject request category inconsistent with loaded printer material", True,
               {"error": str(exc)})
    else:
        record("V02", "reject request category inconsistent with loaded printer material", False,
               {"category": wrong["category"], "models": [m["model_id"] for m in wrong["all_candidates"]]})

    neutral = deepcopy(config)
    neutral["category"] = "kettle"
    neutral["criteria"] = [{**config["criteria"][0], "id": "LID", "user_field": "needs_lid",
                            "product_field": "lid", "why": "synthetic lid property"}]
    neutral["models"] = [{"model_id": "SYNTHETIC-NEUTRAL", "facts": {
        "lid": {"value": True, "source_ids": [next(iter(neutral["source_registry"]))]}}}]
    try:
        wrong = compare_research_snapshot({"category": "printer", "needs_lid": True},
                                          config=neutral, today=TODAY)
    except ValueError as exc:
        record("V03", "reject inverse mismatch with explicitly neutral injected config", True,
               {"error": str(exc)})
    else:
        record("V03", "reject inverse mismatch with explicitly neutral injected config", False,
               {"category": wrong["category"], "models": [m["model_id"] for m in wrong["all_candidates"]]})

    okay = compare_research_snapshot({"category": "kettle", "needs_lid": True},
                                     config=neutral, today=TODAY)
    record("V04", "matched neutral contract works without wechat_setup placeholder",
           okay["all_candidates"][0]["eligibility"] == "model_spec_research_only"
           and "微信" not in json.dumps(okay["judgments"], ensure_ascii=False),
           {"category": okay["category"], "eligibility": okay["all_candidates"][0]["eligibility"]})

    renamed = deepcopy(config)
    rename = {key: "INDEPENDENT-" + key for key in renamed["source_registry"]}
    renamed["source_registry"] = {rename[key]: val for key, val in renamed["source_registry"].items()}
    for rule in renamed["criteria"]:
        rule["source_ids"] = [rename[key] for key in rule["source_ids"]]
    for model in renamed["models"]:
        model["model_id"] = "DIAG-" + model["model_id"]
        model["source_ids"] = [rename[key] for key in model.get("source_ids", [])]
        for fact in model["facts"].values():
            fact["source_ids"] = [rename[key] for key in fact["source_ids"]]
    changed = compare_research_snapshot({**values, "device_deployment_region": "中国大陆"},
                                        config=renamed, today=TODAY)
    record("V05", "renaming all candidate and source identities preserves relation semantics",
           [[c["relation"] for c in m["checks"]] for m in changed["all_candidates"]]
           == [[c["relation"] for c in m["checks"]] for m in regular["all_candidates"]],
           {"models": [m["model_id"] for m in changed["all_candidates"]]})

    expanded = deepcopy(neutral)
    expanded["models"] = [{**deepcopy(neutral["models"][0]), "model_id": "DIAG-" + str(i)}
                          for i in (4, 2, 7, 1)]
    many = compare_research_snapshot({"category": "kettle", "needs_lid": True},
                                     config=expanded, today=TODAY)
    record("V06", "all four reordered/added candidates computed, only three displayed",
           len(many["all_candidates"]) == 4 and len(many["displayed_candidates"]) == 3
           and many["hidden_candidates"][0]["model_id"] == "DIAG-1",
           {"total": many["total_candidate_count"], "hidden": many["hidden_candidates"]})

    withdrawn = deepcopy(neutral)
    withdrawn["models"][0]["facts"]["lid"]["status"] = "withdrawn"
    unavailable = compare_research_snapshot({"category": "kettle", "needs_lid": True},
                                            config=withdrawn, today=TODAY)
    record("V07", "withdrawn fact cannot produce attributed applicable judgment",
           not unavailable["judgments"] and unavailable["all_candidates"][0]["hard_unknown"] == ["LID"],
           {"judgments": unavailable["judgments"], "unknown": unavailable["all_candidates"][0]["hard_unknown"]})

    expired = deepcopy(neutral)
    expired["models"][0]["facts"]["lid"]["valid_until"] = "2026-11-15"
    unavailable = compare_research_snapshot({"category": "kettle", "needs_lid": True},
                                            config=expired, today=TODAY)
    record("V08", "expired fact cannot produce applicable judgment",
           not unavailable["judgments"], {"judgments": unavailable["judgments"]})

    bad = deepcopy(neutral)
    bad["models"][0]["facts"]["lid"]["source_ids"] = ["UNMAPPED"]
    try:
        compare_research_snapshot({"category": "kettle", "needs_lid": True}, config=bad, today=TODAY)
    except ValueError as exc:
        record("V09", "unmapped source rejected", True, {"error": str(exc)})
    else:
        record("V09", "unmapped source rejected", False, {})

    missing = compare_research_snapshot(values, today=TODAY)
    record("V10", "missing user deployment region remains a user question, not solely missing product evidence",
           any("部署" in q for q in missing["necessary_user_questions"])
           and missing["next_action"] != "verify_missing_hard_model_evidence",
           {"questions": missing["necessary_user_questions"], "limitations": missing["evidence_limitations"],
            "next_action": missing["next_action"]})

    conflict = compare_case_research({**values, "requirements": ["必须在家打印彩色"]})
    snap = conflict["shared_research_snapshot"]
    record("V11", "condition conflict generates a necessary user resolution question",
           snap["next_action"] == "resolve_user_condition_conflict" and bool(snap["necessary_user_questions"]),
           {"questions": snap["necessary_user_questions"], "limitations": snap["evidence_limitations"],
            "next_action": snap["next_action"], "eligibilities": [x["eligibility"] for x in snap["all_candidates"]]})

    normal = {**values, "description": "必须微信小程序直接打印，家中黑白", "confirmed": True,
              "requirements": ["必须微信小程序直接打印"]}
    web = evaluate_input(normal)["real_printer_case_research"]["shared_research_snapshot"]
    payload = [normal["description"], "0–50", "1000", "", "false", "true", "", "",
               "必须微信小程序直接打印", "true", "miniprogram", "", "", "device_delivered", ""]
    proc = subprocess.run([sys.executable, "-X", "utf8", "-m", "shopping_decision.desktop_bridge",
                           *(base64.b64encode(v.encode("utf-8")).decode("ascii") for v in payload)],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30, check=True)
    fields = {k: base64.b64decode(v).decode("utf-8") for line in proc.stdout.splitlines()
              if "\t" in line for k, v in [line.split("\t", 1)]}
    desktop = json.loads(fields["report_json"])["real_printer_case_research"]["shared_research_snapshot"]
    record("V12", "normal Web and real Python desktop subprocess both preserve the user region question",
           all(any("部署" in q for q in s["necessary_user_questions"]) for s in (web, desktop)),
           {"web_questions": web["necessary_user_questions"], "desktop_questions": desktop["necessary_user_questions"],
            "web_next_action": web["next_action"], "desktop_next_action": desktop["next_action"],
            "desktop_protocol_status": fields["status"]})

    old = json.loads((ROOT / "reports/printer_effect_e1_independent_20261116_run01_dev.json").read_text(encoding="utf-8"))
    delivered = json.loads((ROOT / "reports/newpack_research_development_20261116_run01.json").read_text(encoding="utf-8"))
    replay = []
    for case in delivered["cases"]:
        previous = next(x for x in old["cases"] if x["id"] == case["case_id"])
        from shopping_decision.printer_effect_probe import pair_development_views
        actual = pair_development_views(compare_case_research(case["normalized_input"]))
        replay.append({"case_id": case["case_id"],
                       "baseline_matches_delivered": actual["direct_parameter_screen"]["task_output"] == case["baseline_task_output"],
                       "cognition_matches_delivered": actual["cognition_augmented"]["task_output"] == case["cognition_task_output"],
                       "baseline_matches_prior_review": case["baseline_task_output"] == previous["baseline"]["task_output"],
                       "cognition_matches_prior_review": case["cognition_task_output"] == previous["cognition"]["task_output"]})
    result = {"date": TODAY.isoformat(), "role": "independent_reviewer",
              "diagnostic_not_recommendation_accuracy": True,
              "records": records, "total": len(records),
              "passed": sum(r["passed"] for r in records),
              "failed_ids": [r["id"] for r in records if not r["passed"]],
              "development_replay": replay, "formal_holdout_run": False}
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": OUTPUT.relative_to(ROOT).as_posix(), "total": result["total"],
                      "passed": result["passed"], "failed_ids": result["failed_ids"],
                      "six_cases_replayed_and_unchanged": all(all(v for k, v in x.items() if k != "case_id") for x in replay)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
