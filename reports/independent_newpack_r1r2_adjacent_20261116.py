"""R1/R2修后有限相邻覆盖；合成输入与真实效果分账。"""
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
from shopping_decision.research_snapshot import compare_research_snapshot, render_research_snapshot
from shopping_decision.selection_criteria import evaluate_selection, load_criteria
from shopping_decision.real_printer_case import compare_case_research
from shopping_decision.web import evaluate_input

TODAY = date(2026, 11, 16)
OUTPUT = ROOT / "reports/newpack_r1r2_independent_20261116_run01_adjacent.json"


def main():
    if OUTPUT.exists():
        raise RuntimeError("independent_output_exists_do_not_overwrite")
    os.environ["PYTHONUTF8"] = "1"
    config, _ = load_criteria()
    base = {"category": "printer", "needs_color": False,
            "accepts_outsourced_color": True, "monthly_pages_range": [0, 50],
            "budget_max_cny": 1000, "budget_scope": "device_delivered",
            "wechat_required": True, "wechat_workflow": "miniprogram"}
    records = []

    def record(identifier, expectation, passed, actual):
        records.append({"id": identifier, "expectation": expectation,
                        "passed": bool(passed), "actual": actual})

    inferred = compare_research_snapshot({}, config=config, today=TODAY)
    record("A01", "explicit material category is preserved for legacy caller without a category",
           inferred["category"] == "printer" and inferred["category_binding"] == "material_explicit",
           {"category": inferred["category"], "binding": inferred["category_binding"]})
    legacy = deepcopy(config)
    legacy.pop("category")
    unscoped = compare_research_snapshot({}, config=legacy, today=TODAY)
    record("A02", "old unscoped contract stays explicitly unscoped",
           unscoped["category"] is None and unscoped["category_binding"] == "legacy_unscoped",
           {"category": unscoped["category"], "binding": unscoped["category_binding"]})

    checks = evaluate_selection(base, config=config, today=TODAY)
    try:
        render_research_snapshot({"category": "kettle"}, checks)
    except ValueError as exc:
        record("A03", "render layer also rejects relabelling precomputed printer checks", True,
               {"error": str(exc)})
    else:
        record("A03", "render layer also rejects relabelling precomputed printer checks", False, {})

    checks = evaluate_selection(base, config=config, today=TODAY)
    question = next(x for x in checks["question_items"] if x["field"] == "device_deployment_region")
    old_text = question["text"]
    question["text"] = "请告知实际部署国家地区"
    checks["questions"] = [question["text"] if q == old_text else q for q in checks["questions"]]
    no_punctuation = render_research_snapshot(base, checks)
    record("A04", "typed user question survives wording without question marks",
           question["text"] in no_punctuation["necessary_user_questions"],
           {"questions": no_punctuation["necessary_user_questions"]})

    abroad = compare_research_snapshot({**base, "device_deployment_region": "日本"}, today=TODAY)
    record("A05", "confirmed overseas deployment asks for evidence instead of repeating region question",
           not abroad["necessary_user_questions"] and any(x["field"] == "regional_wechat_service"
                                                          and x["kind"] == "external_evidence"
                                                          for x in abroad["question_items"]),
           {"questions": abroad["necessary_user_questions"], "next_action": abroad["next_action"]})

    withdrawn = deepcopy(config)
    for model in withdrawn["models"]:
        for fact in model["facts"].values():
            fact["status"] = "withdrawn"
    missing_product = compare_research_snapshot({"category": "printer", "requires_scan": True},
                                               config=withdrawn, today=TODAY)
    record("A06", "withdrawn product evidence does not become an unnecessary user question",
           not missing_product["necessary_user_questions"] and not missing_product["judgments"]
           and missing_product["next_action"] == "verify_missing_hard_model_evidence",
           {"questions": missing_product["necessary_user_questions"], "next_action": missing_product["next_action"]})

    conflicted = compare_case_research({**base, "requirements": ["必须在家打印彩色"]})["shared_research_snapshot"]
    restored = compare_case_research({**base, "requirements": [],
                                     "device_deployment_region": "日本"})["shared_research_snapshot"]
    record("A07", "cleared conflict does not leave a stale conflict question/action",
           conflicted["next_action"] == "resolve_user_condition_conflict"
           and bool(conflicted["necessary_user_questions"])
           and restored["next_action"] != "resolve_user_condition_conflict"
           and not any(x["kind"] == "user_conflict" for x in restored["question_items"]),
           {"before": conflicted["next_action"], "after": restored["next_action"]})

    for identifier, value in [("A08", "未知"), ("A09", "待确认"), ("A10", "   ")]:
        snapshot = compare_research_snapshot({**base, "device_deployment_region": value}, today=TODAY)
        record(identifier, "explicit missing/unknown region representation remains a user-input question",
               any(x["field"] == "device_deployment_region" and x["kind"] == "user_input"
                   for x in snapshot["question_items"])
               and snapshot["next_action"] == "clarify_user_conditions",
               {"region": value, "questions": snapshot["necessary_user_questions"],
                "next_action": snapshot["next_action"],
                "wechat_relations": [x["relation"] for m in snapshot["all_candidates"]
                                     for x in m["checks"] if x["criterion_id"] == "C-WECHAT"]})

    data = {**base, "description": "必须微信小程序直接打印，家中黑白", "confirmed": True,
            "requirements": ["必须微信小程序直接打印"], "device_deployment_region": "未知"}
    web = evaluate_input(data)["real_printer_case_research"]["shared_research_snapshot"]
    fields = [data["description"], "0–50", "1000", "", "false", "true", "", "",
              data["requirements"][0], "true", "miniprogram", "", "", "device_delivered", "未知"]
    proc = subprocess.run([sys.executable, "-X", "utf8", "-m", "shopping_decision.desktop_bridge",
                           *(base64.b64encode(x.encode("utf-8")).decode("ascii") for x in fields)],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30, check=True)
    raw = {k: base64.b64decode(v).decode("utf-8") for line in proc.stdout.splitlines()
           if "\t" in line for k, v in [line.split("\t", 1)]}
    desktop = json.loads(raw["report_json"])["real_printer_case_research"]["shared_research_snapshot"]
    record("A11", "normal Web and desktop Python subprocess preserve unknown-marker user region question",
           all(any(x["field"] == "device_deployment_region" and x["kind"] == "user_input"
                   for x in snapshot["question_items"]) for snapshot in (web, desktop)),
           {"web_questions": web["necessary_user_questions"], "desktop_questions": desktop["necessary_user_questions"],
            "web_next_action": web["next_action"], "desktop_next_action": desktop["next_action"],
            "purchase_approved": desktop["purchase_recommendation_approved"],
            "transactions_enabled": desktop["transactions_enabled"]})

    workflow = compare_research_snapshot({**base, "device_deployment_region": "日本",
                                          "wechat_workflow": "unknown"}, today=TODAY)
    record("A12", "known region with unconfirmed workflow asks only for missing workflow",
           any(x["field"] == "wechat_workflow" and x["kind"] == "user_input" for x in workflow["question_items"])
           and not any(x["field"] == "device_deployment_region" and x["kind"] == "user_input"
                       for x in workflow["question_items"]),
           {"questions": workflow["necessary_user_questions"], "next_action": workflow["next_action"]})

    output = {"date": TODAY.isoformat(), "role": "independent_reviewer",
              "diagnostic_not_recommendation_accuracy": True, "records": records,
              "total": len(records), "passed": sum(r["passed"] for r in records),
              "failed_ids": [r["id"] for r in records if not r["passed"]],
              "remaining_root_cause": "R2 incomplete normalization of missing deployment region representations",
              "new_external_sources": 0, "formal_holdout_run": False}
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": OUTPUT.relative_to(ROOT).as_posix(), "total": output["total"],
                      "passed": output["passed"], "failed_ids": output["failed_ids"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
