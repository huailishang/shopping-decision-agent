"""G1-R1有限独立复核：原件只读，新证据独占创建，无网络或凭证读取。"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
PREFIX = "cognition_g1r1_independent_20261115_run01"
BUILD = ROOT / ".h08-build" / "g1r1-independent-20261115-run01"
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def write_new(path, data):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def run(command, timeout=90):
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env=ENV, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
    out = {"command": command, "exit_code": result.returncode,
           "elapsed_seconds": round(time.monotonic()-started, 3),
           "stdout": result.stdout, "stderr": result.stderr}
    print(json.dumps({"command": command, "exit_code": result.returncode,
                      "elapsed_seconds": out["elapsed_seconds"],
                      "stdout_tail": result.stdout[-400:],
                      "stderr_tail": result.stderr[-350:]}, ensure_ascii=False), flush=True)
    return out


def main():
    output = ROOT / "reports" / (PREFIX + "_validation.json")
    baseline_path = ROOT / "reports" / (PREFIX + "_baseline.json")
    variants_path = ROOT / "reports" / (PREFIX + "_variants.json")
    if any(p.exists() for p in (output, baseline_path, variants_path)):
        raise SystemExit("refusing_existing_output")
    tracked = subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT).decode("utf-8").split("\0")
    allowed = {"shopping_decision", "tests", "scripts", "desktop", "knowledge", "reports", "handoffs", "docs", "evaluation"}
    hashes = {}
    for name in tracked:
        p = ROOT / name
        if (not name or not p.is_file() or (len(Path(name).parts)>1 and Path(name).parts[0] not in allowed)
                or p.suffix.lower() not in {".py", ".java", ".json", ".md", ".txt", ".bat", ".toml"}
                or any(x in p.parts for x in ("__pycache__", "raw"))):
            continue
        hashes[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    write_new(baseline_path, {"role": "independent_evaluator", "date": "2026-11-15",
                              "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                              "files": hashes, "file_count": len(hashes)})
    results = {}
    results["nearby8"] = run([sys.executable, "-X", "utf8", "-m", "reports.independent_cognition_g123_recheck_20261115",
                              "--output", "reports/" + PREFIX + "_nearby8.json"])
    results["known21"] = run([sys.executable, "-X", "utf8", "-m", "reports.independent_cognition_printer_20261115",
                              "--output", "reports/" + PREFIX + "_known21.json"])
    results["cli11"] = run([sys.executable, "-X", "utf8", "-m", "scripts.cognition_case_replay",
                            "--output", "reports/" + PREFIX + "_cli11.json"])

    base = {"category": "printer", "usage": "独立合成复核", "needs_color": False,
            "accepts_outsourced_color": True, "monthly_pages_range": [203, 379],
            "budget_max_cny": 1907, "requires_scan": True, "requires_auto_duplex": True,
            "requirements": ["必须微信打印"], "wechat_workflow": "transfer_to_app",
            "device_deployment_region": "中国大陆"}
    changes = [base, {"wechat_required": True}, {"wechat_required": False},
               {"requirements": []}, {"requirements": ["必须微信小程序打印"], "wechat_required": None,
                                      "wechat_workflow": "miniprogram", "device_deployment_region": "日本"},
               {"requirements": [], "wechat_required": False, "requires_scan": None, "requires_auto_duplex": None}]
    turns = [{"text": "独立合成同会话组合N"+str(i+1), "answers": values} for i, values in enumerate(changes)]
    proc = subprocess.run([sys.executable, "-X", "utf8", "-m", "shopping_decision.dialogue_flow", "--real-printer-case"],
                          input="".join(json.dumps(t, ensure_ascii=False)+"\n" for t in turns),
                          cwd=ROOT, env=ENV, capture_output=True, encoding="utf-8", timeout=50)
    rows = [json.loads(line) for line in proc.stdout.splitlines()][1:] if proc.returncode == 0 else []
    checks = []
    views = []
    for row in rows:
        view = row["real_printer_case_research"]
        c = view["criteria_comparison"]
        views.append({"eligible": c["research_eligible_models"], "pending": c["pending_models"],
                      "conflicts": c["user_condition_conflicts"], "normalized_required": c["normalized_required"],
                      "models": {m["model_id"]: {"eligibility": m["eligibility"],
                                  "checks": {x["criterion_id"]: x["relation"] for x in m["checks"]}}
                                 for m in c["models"]},
                      "active_models": [d["model"] for d in view["model_comparison"]["active_conditional_decisions"]
                                        if d["model"] in ("M232dw", "HL-L1238W")],
                      "purchase": view["purchase_recommendation_approved"], "transactions": view["transactions_enabled"]})
    if len(views) == 6:
        checks = [
            ("N01_raw_app_with_scan_duplex", not views[0]["eligible"] and len(views[0]["pending"])==2
             and not views[0]["active_models"] and views[0]["models"]["M232dw"]["checks"].get("C-WECHAT")=="other_workflow_unverified"
             and views[0]["models"]["M232dw"]["checks"].get("C-SCAN")=="match"
             and views[0]["models"]["M232dw"]["checks"].get("C-DUPLEX")=="match"),
            ("N02_extra_confirmation_equivalent", views[0]==views[1]),
            ("N03_explicit_denial_is_conflict", bool(views[2]["conflicts"]) and not views[2]["eligible"] and not views[2]["active_models"]),
            ("N04_withdraw_wechat_preserves_other_hard_conditions", views[3]["eligible"]==["M232dw"]
             and views[3]["models"]["HL-L1238W"]["eligibility"]=="pending_hard_evidence"
             and all("C-WECHAT" not in m["checks"] for m in views[3]["models"].values())),
            ("N05_switch_to_miniprogram_Japan_stays_pending", not views[4]["eligible"] and len(views[4]["pending"])==2
             and not views[4]["active_models"] and all(m["checks"].get("C-WECHAT")=="deployment_outside_verified_scope" for m in views[4]["models"].values())),
            ("N06_clear_all_hard_conditions_restores_research", len(views[5]["eligible"])==2 and not views[5]["pending"]
             and all(not any(k in m["checks"] for k in ("C-WECHAT", "C-SCAN", "C-DUPLEX")) for m in views[5]["models"].values())),
        ]
    variants = {"role": "independent_evaluator", "scope": "six_bounded_same_session_synthetic_combinations_not_accuracy",
                "inputs": turns, "cli_exit_code": proc.returncode, "stderr": proc.stderr,
                "checks": [{"id": k, "pass": bool(v)} for k,v in checks], "summaries": views,
                "total": 6, "passed": sum(bool(v) for _,v in checks),
                "all_rounds_purchase_and_transactions_false": len(views)==6 and all(not v["purchase"] and not v["transactions"] for v in views)}
    write_new(variants_path, variants)
    print(json.dumps({"new_combinations": variants["passed"], "total": 6}, ensure_ascii=False), flush=True)

    BUILD.mkdir(parents=True, exist_ok=False)
    results["javac17_target"] = run(["javac", "--release", "17", "-encoding", "UTF-8", "-d", str(BUILD),
                                    *["desktop/"+name for name in ("DesktopBridgeClient.java", "ShoppingDecisionDesktop.java", "P04MarketplaceRegression.java")]])
    if results["javac17_target"]["exit_code"] == 0:
        results["p04"] = run(["java", "-cp", str(BUILD), "P04MarketplaceRegression", sys.executable])
    results["full_suite"] = run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-q"], timeout=180)
    changed = [name for name, sha in hashes.items() if not (ROOT/name).is_file()
               or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha]
    result = {"role": "independent_evaluator", "date": "2026-11-15", "results": results,
              "baseline": str(baseline_path.relative_to(ROOT)), "protected_file_count": len(hashes),
              "changed_original_files": changed, "new_combinations": str(variants_path.relative_to(ROOT)),
              "core_checks_passed": all(x["exit_code"]==0 for x in results.values()) and not changed
                                    and variants["passed"]==6 and variants["all_rounds_purchase_and_transactions_false"],
              "business_api_calls": 0, "credential_reads": 0, "new_real_haina_inputs": 0,
              "verified_platform_identities": 0, "regional_live_quotes": 0,
              "purchase_approved": False, "transactions_enabled": False,
              "gui": {"status": "pending_independent_window_check"}}
    write_new(output, result)
    print(json.dumps({"core_checks_passed": result["core_checks_passed"], "protected_file_count": len(hashes),
                      "changed_original_files": changed, "validation": str(output.relative_to(ROOT))}, ensure_ascii=False), flush=True)
    return 0 if result["core_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
