"""本轮有限独立复核；只新增评审证据，不覆盖原执行/失败记录。"""
from contextlib import redirect_stdout
from datetime import date
from hashlib import sha256
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PREFIX = ROOT / "reports/next_execution_review_20261116_run01"
TODAY = date(2026, 11, 16)


def save(suffix, value):
    path = Path(str(PREFIX) + suffix)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def snapshot():
    result = {}
    for directory in ("shopping_decision", "tests", "knowledge", "evaluation",
                      "desktop", "reports", "handoffs", "docs"):
        for path in (ROOT / directory).rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".json", ".md", ".java", ".bat", ".txt", ".jpg", ".png"}:
                result[path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
    for name in ("CURRENT.md", "README.md", "AGENTS.md"):
        result[name] = sha256((ROOT / name).read_bytes()).hexdigest()
    return result


def replay(filename, suffix):
    spec = importlib.util.spec_from_file_location("bounded_review_" + suffix, ROOT / "reports" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUTPUT = Path(str(PREFIX) + suffix + ".json")
    with redirect_stdout(io.StringIO()):
        module.main()
    return json.loads(module.OUTPUT.read_text(encoding="utf-8"))


def main():
    if list(PREFIX.parent.glob(PREFIX.name + "*")):
        raise RuntimeError("review_outputs_exist_do_not_overwrite")
    start = time.monotonic()
    os.environ["PYTHONUTF8"] = "1"
    before = snapshot()
    save("_baseline.json", before)
    delivery = json.loads((ROOT / "reports/newpack_r2_unknown_executor_20261116_run01_validation.json").read_text(encoding="utf-8"))
    integrity = {name: before.get(name) == digest for name, digest in delivery["file_sha256"].items()}
    if not all(integrity.values()):
        save("_integrity_failure.json", integrity)
        raise RuntimeError("delivery_changed_review_scope_requires_reassessment")

    known = replay("independent_newpack_review_20261116.py", "_known12")
    adjacent = replay("independent_newpack_r1r2_adjacent_20261116.py", "_adjacent12")
    # The historical script's remaining_root_cause is a fixed historical label;
    # only its recorded observations and pass flags are used in this review.
    from shopping_decision.research_snapshot import compare_research_snapshot
    base = {"category": "printer", "needs_color": False, "accepts_outsourced_color": True,
            "monthly_pages_range": [0, 50], "budget_max_cny": 1000,
            "budget_scope": "device_delivered", "wechat_required": True,
            "wechat_workflow": "miniprogram"}
    records = []
    cases = [(None, True), ("", True), ("\u3000\t", True), (" ＵＮＫＮＯＷＮ ", True),
             ("日本", False), ("悉尼", False), ("Copenhagen", False), ("中国大陆", False)]
    for region, missing in cases:
        view = compare_research_snapshot({**base, "device_deployment_region": region}, today=TODAY)
        region_question = any(q["kind"] == "user_input" and q["field"] == "device_deployment_region"
                              for q in view["question_items"])
        passed = region_question == missing and (not missing or view["next_action"] == "clarify_user_conditions")
        if region in ("日本", "悉尼", "Copenhagen"):
            passed = passed and view["next_action"] == "verify_missing_hard_model_evidence"
        records.append({"region": region, "expected_missing_user_input": missing,
                        "actual_region_user_question": region_question, "next_action": view["next_action"],
                        "passed": passed and not view["purchase_recommendation_approved"] and not view["transactions_enabled"]})
    save("_semantic8.json", {"role": "independent_reviewer", "diagnostic_not_effect": True,
                              "records": records, "total": len(records),
                              "passed": sum(x["passed"] for x in records)})
    from shopping_decision.h05_probes import run_negative_probes
    h05 = run_negative_probes(today=TODAY)
    save("_h05.json", h05)
    run_start = time.monotonic()
    proc = subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-q"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=150)
    log = proc.stdout + proc.stderr
    with Path(str(PREFIX) + "_unittest.txt").open("x", encoding="utf-8") as stream:
        stream.write(log)
    count = re.search(r"Ran (\d+) tests?", log)
    after = snapshot()
    changed = [name for name, digest in before.items() if after.get(name) != digest]
    development_unchanged = all(all(v for k, v in item.items() if k != "case_id")
                                for item in known["development_replay"])
    passed = (known["passed"] == known["total"] and adjacent["passed"] == adjacent["total"]
              and all(x["passed"] for x in records) and h05["summary"]["passed"] == h05["summary"]["total"]
              and proc.returncode == 0 and not changed and development_unchanged)
    result = {"date": TODAY.isoformat(), "role": "independent_reviewer_and_planner",
              "delivery_sha_matches": integrity, "original_files_count": len(before), "original_files_changed": changed,
              "known12": {k: known[k] for k in ("total", "passed", "failed_ids")},
              "adjacent12": {k: adjacent[k] for k in ("total", "passed", "failed_ids")},
              "semantic8": {"total": 8, "passed": sum(x["passed"] for x in records)},
              "six_development_pairs_unchanged": development_unchanged,
              "h05": h05["summary"], "python_full": {"returncode": proc.returncode,
              "total": int(count.group(1)) if count else None, "elapsed_seconds": round(time.monotonic() - run_start, 3)},
              "R2_limited_review_passed": passed, "engineering_B_limited_passed": passed,
              "not_recommendation_accuracy": True, "native_GUI_new_run": False,
              "standalone_java_or_P04_run": False, "formal36_run": False, "new_user_feedback": 0,
              "H1": "BLOCKED", "H2_identity": "0/2", "old20": "0/20", "H3_regional_prices": 0,
              "purchase_approved": False, "transactions_enabled": False, "overall": "NOT_PASS",
              "new_external_actions": 0, "secrets_read": False, "git_commit_or_push": False,
              "wall_seconds": round(time.monotonic() - start, 3), "effective_human_hours": "unknown_not_inferred_from_wall_time"}
    save("_validation.json", result)
    print(json.dumps(result, ensure_ascii=False))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
