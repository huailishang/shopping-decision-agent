"""集中独立复核：只读原材料/源码，新增反例另存，不访问业务API或凭证。"""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from shopping_decision.h05_probes import run_negative_probes
from shopping_decision.haina_mcp_ingest import ingest_haina_mcp_bundle, load_haina_mcp_report, SYNTHETIC_FIXTURE_PATH
from shopping_decision.real_printer_case import compare_case_research

ROOT = Path(__file__).resolve().parent.parent
NOW = datetime(2026, 11, 15, 23, 59, tzinfo=timezone.utc)
BASE = {"category": "printer", "usage": "家用", "needs_color": False,
        "accepts_outsourced_color": True, "monthly_pages_range": [0, 50],
        "budget_max_cny": 1000, "requirements": ["希望微信打印", "可靠耐用"]}


def main():
    if len(sys.argv) != 3 or sys.argv[1] != "--output":
        raise SystemExit("usage: python -m reports.independent_haina_longpack_20261115 --output NEW_FILE.json")
    out = Path(sys.argv[2])
    if out.exists():
        raise SystemExit("output_exists_no_overwrite")
    validation = json.loads((ROOT / "reports/haina_longpack_validation_20261115.json").read_text(encoding="utf-8"))
    checks = []

    def check(name, passed, actual, expectation, finding=None):
        checks.append({"id": name, "pass": bool(passed), "actual": actual,
                       "expected": expectation, "finding": finding})

    def view(**changes):
        return compare_case_research({**BASE, **changes})

    def active(result):
        return [x["id"] for x in result["model_comparison"]["active_conditional_decisions"]]

    fixture = load_haina_mcp_report(SYNTHETIC_FIXTURE_PATH, now=NOW)
    check("I01_pinned_fixture_remains_synthetic", fixture["entity_count"] == 2
          and fixture["source_mode"] == "synthetic_test" and not fixture["purchase_recommendation_approved"]
          and fixture["platform_identity_verified_count"] == 0,
          {k: fixture[k] for k in ("source_mode", "entity_count", "platform_identity_verified_count")},
          "2 synthetic entities; no platform identity or purchase")
    with TemporaryDirectory() as d:
        path = Path(d) / "copied-fixture.json"
        path.write_bytes(SYNTHETIC_FIXTURE_PATH.read_bytes())
        copied = load_haina_mcp_report(path, now=NOW)
    check("I02_identical_external_copy_blocked", copied["status"] == "blocked_non_fixture_report",
          copied["status"], "byte-identical copied fixture cannot enter normal loader")
    blocked = ingest_haina_mcp_bundle({"source_mode": "real_response", "calls": object()}, now=NOW)
    check("I03_real_mode_rejected_before_parse", blocked["entity_count"] == 0
          and blocked["status"] == "blocked_real_data_use_not_approved", blocked["status"], "real mode blocked")

    mono_scan = view(requires_scan=True)
    color = view(needs_color=True)
    check("I04_monochrome_scan_positive_control", "DEC-01" in active(mono_scan), active(mono_scan),
          "scan evidence may prioritize HP for monochrome research")
    check("I05_color_alone_removes_monochrome_route", "CASE-01" not in {r["id"] for r in color["reasons"]}
          and "CASE-09" in {r["id"] for r in color["reasons"]},
          [r["id"] for r in color["reasons"]], "color exclusion replaces mono route")
    for name, changes in (("I06_color_plus_scan", {"requires_scan": True}),
                          ("I07_color_plus_duplex", {"requires_auto_duplex": True})):
        result = view(needs_color=True, **changes)
        check(name, "DEC-01" not in active(result),
              {"active_decisions": active(result), "reasons": [r["id"] for r in result["reasons"]]},
              "excluded monochrome model must not be an active candidate under a color hard requirement", "F1")
    budget_low = next(r["reason"] for r in view(budget_max_cny=500)["reasons"] if r["id"] == "CASE-06")
    budget_high = next(r["reason"] for r in view(budget_max_cny=3000)["reasons"] if r["id"] == "CASE-06")
    check("I08_lower_budget_comparison_control", "高于预算" in budget_low, budget_low, "1906 > 500")
    check("I09_higher_budget_comparison", "高于预算" not in budget_high, budget_high,
          "1906 < 3000; still no verified transaction quote", "F2")
    check("I10_budget_clearing_removes_reason", "CASE-06" not in {r["id"] for r in view(budget_max_cny=None)["reasons"]},
          [r["id"] for r in view(budget_max_cny=None)["reasons"]], "cleared budget removes its reason")
    low_volume = next(r["reason"] for r in view()["reasons"] if r["id"] == "CASE-03")
    check("I11_volume_direction", "低于原案区间" not in low_volume, low_volume,
          "user 0-50 is below manufacturer suggested 200-2000, not the reverse", "F3")
    check("I12_shipping_does_not_imply_deployment", view(delivery_region="上海")["model_comparison"]["deployment_region_scope"] == "unknown",
          view(delivery_region="上海")["model_comparison"]["deployment_region_scope"], "shipping does not establish deployment region")

    def sku_bundle(sku_list, count):
        return {"schema_version": 1, "operation": "haina_mcp_synthetic_bundle", "source_mode": "synthetic_test",
                "calls": [{"tool": "product_sku_search", "query": "HP M232dw", "observed_at": "2026-11-15T00:00:00Z",
                           "payload": {"error_code": 0, "data": [{"entity_name": "HP M232dw",
                                        "sku_result": {"spu_id": "synthetic-spu", "sku_count": count, "sku_list": sku_list}}]}}]}

    huge = sku_bundle([{"sku_id": "synthetic-sku", "sku_axes": {"型号": "M232dw"}, "sku_products_count": 2,
                        "sku_products": [{"title": "HP M232dw 打印机", "final_price": 10 ** 400},
                                         {"title": "HP M232dw 打印机", "final_price": "999"}]}], 1)
    try:
        result = ingest_haina_mcp_bundle(huge, now=NOW)
        check("I13_huge_price_neighbor_isolation", result["entity_count"] >= 1,
              {"status": result["status"]}, "invalid numeric hint cannot crash good neighbor", "F4")
    except Exception as exc:
        check("I13_huge_price_neighbor_isolation", False,
              {"exception": type(exc).__name__, "message": str(exc)}, "invalid numeric hint cannot crash good neighbor", "F4")
    empty = ingest_haina_mcp_bundle(sku_bundle([], 0), now=NOW)
    count = empty["entities"][0]["sale_lead_count"]
    check("I14_empty_sku_count", count == 0, {"reported_sku_count": 0, "sale_lead_count": count},
          "empty SKU list produces no sale product lead", "F5")

    turns = [{"text": "独立合成原案回放，不是真人新答复", "answers": BASE},
             {"text": "模拟新增扫描", "answers": {"requires_scan": True}},
             {"text": "模拟新增必须在家彩印，保留扫描", "answers": {"needs_color": True}},
             {"text": "模拟提高预算到3000", "answers": {"budget_max_cny": 3000}},
             {"text": "模拟撤销扫描并恢复黑白", "answers": {"requires_scan": None, "needs_color": False}}]
    proc = subprocess.run([sys.executable, "-X", "utf8", "-m", "shopping_decision.dialogue_flow", "--real-printer-case"],
                          input="".join(json.dumps(t, ensure_ascii=False) + "\n" for t in turns),
                          capture_output=True, encoding="utf-8", timeout=30, cwd=ROOT)
    rows = [json.loads(line) for line in proc.stdout.splitlines()] if proc.returncode == 0 else []
    check("I15_cli_five_turns_safe", len(rows) == 6 and all(
          not r["real_printer_case_research"]["purchase_recommendation_approved"]
          and not r["real_printer_case_research"]["transactions_enabled"] for r in rows[1:]),
          {"returncode": proc.returncode, "rows": len(rows)}, "ready+5 turns; no purchase/transaction")
    cli_color = rows[3]["real_printer_case_research"] if len(rows) == 6 else None
    check("I16_cli_conflict_reproduction", cli_color is not None and "DEC-01" not in active(cli_color),
          active(cli_color) if cli_color else proc.stderr, "normal CLI also removes excluded candidate", "F1")

    gui_path = ROOT / validation["gui"]["saved_record"]
    saved = gui_path.read_text(encoding="utf-8")
    gui, _ = json.JSONDecoder().raw_decode(saved[saved.index("{"):])
    gui_research = gui["real_printer_case_research"]
    check("I17_gui_saved_audit_exists_and_matches_input", gui["request"]["budget_max_cny"] == 3000
          and gui["request"]["needs_color"] is True and gui["request"]["requires_scan"] is True,
          {"bytes": gui_path.stat().st_size, "sha256": hashlib.sha256(gui_path.read_bytes()).hexdigest()},
          "independent UI save/readback retains actual test conditions")
    check("I18_gui_audit_conflict_reproduction", "DEC-01" not in active(gui_research),
          {"active_decisions": active(gui_research), "reason_ids": [r["id"] for r in gui_research["reasons"]]},
          "desktop audit also removes excluded candidate", "F1")

    negatives = run_negative_probes(today=date(2026, 11, 15))
    delivery = json.loads((ROOT / "reports/haina_printer_delivery_20261115_offline_closure.json").read_text(encoding="utf-8"))
    index_hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in delivery["file_sha256"].items()}
    protected = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
                 for p, h in validation["baseline_input_sha256"].items()}
    result = {"role": "independent_evaluator", "review_date": "2026-11-15",
              "scope": "synthetic_new_counterexamples_and_public_research_cli_gui_not_real_supplier_integration",
              "checks": checks, "total": len(checks), "passed": sum(c["pass"] for c in checks),
              "failed_ids": [c["id"] for c in checks if not c["pass"]],
              "failed_finding_groups": sorted({c["finding"] for c in checks if not c["pass"]}),
              "cli_replay": {"input": turns, "output": rows}, "h05_existing_negative": negatives,
              "executor_index_hash_matches": index_hashes, "protected_inputs_unchanged": protected,
              "validation_log": "reports/haina_longpack_validation_20261115.json",
              "real_supplier_payloads_imported": 0, "platform_identity_verified": 0,
              "regional_quote_verified": 0, "business_api_calls": 0, "credential_reads": 0,
              "purchase_approved": False, "transactions_enabled": False}
    with out.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: result[k] for k in ("total", "passed", "failed_ids", "failed_finding_groups")}, ensure_ascii=False))
    print(json.dumps({"h05": negatives["summary"], "executor_index_hashes_all_match": all(index_hashes.values()),
                      "protected_inputs_all_unchanged": all(protected.values()), "output": str(out)}, ensure_ascii=False))
    raise SystemExit(0 if all(c["pass"] for c in checks) else 1)


if __name__ == "__main__":
    main()
