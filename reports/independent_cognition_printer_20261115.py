"""本轮独立反例；只读业务与原材料，合成扰动仅在内存，不改真实商品事实。"""
from __future__ import annotations
from copy import deepcopy
from datetime import date, datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from shopping_decision.selection_criteria import load_criteria, evaluate_selection
from shopping_decision.real_printer_case import compare_case_research
from shopping_decision.dialogue_flow import apply_turn, new_dialogue, compare_dialogue
from shopping_decision.haina_mcp_ingest import ingest_haina_mcp_bundle
from shopping_decision.h05_probes import run_negative_probes

ROOT = Path(__file__).resolve().parent.parent
TODAY = date(2026, 11, 15)
BASE = {"category": "printer", "usage": "家用", "needs_color": False,
        "accepts_outsourced_color": True, "monthly_pages_range": [0, 50],
        "budget_max_cny": 1000, "requirements": ["希望微信打印", "可靠耐用"]}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing_existing_output")
    checks = []
    config, _ = load_criteria()

    def record(identifier, passed, expected, actual, finding=None):
        checks.append({"id": identifier, "pass": bool(passed), "expected": expected,
                       "actual": actual, "finding": finding})

    def row(view, model):
        return next(x for x in view["criteria_comparison"]["models"] if x["model_id"] == model)

    def criterion(view, model, name):
        return next(x for x in row(view, model)["checks"] if x["criterion_id"] == name)

    def active(view):
        return view["model_comparison"]["active_conditional_decisions"]

    def altered(changed, values):
        # 仅在当前调用中替换合法配置的加载结果；实际算子/组合/解释代码不变。
        with patch("shopping_decision.real_printer_case.evaluate_selection",
                   side_effect=lambda v: evaluate_selection(v, config=changed, today=TODAY)):
            return compare_case_research(values)

    ordinary = compare_case_research(BASE)
    record("I01_original_safety", not ordinary["purchase_recommendation_approved"]
           and not ordinary["transactions_enabled"] and len(ordinary["criteria_comparison"]["models"]) == 2,
           "2 research models, no purchase/transaction", ordinary["criteria_comparison"]["research_eligible_models"])
    for name, change in (("I02_color_scan", {"requires_scan": True}),
                         ("I03_color_duplex", {"requires_auto_duplex": True})):
        result = compare_case_research({**BASE, "needs_color": True, **change})
        record(name, len(result["criteria_comparison"]["excluded_models"]) == 2
               and not any(x.get("model") in ("M232dw", "HL-L1238W") for x in active(result)),
               "both monochrome models excluded, no reactivation", {"excluded": result["criteria_comparison"]["excluded_models"], "active": active(result)})
    scan = compare_case_research({**BASE, "requires_scan": True})
    record("I04_scan_positive_control", row(scan, "M232dw")["eligibility"] == "model_spec_research_only"
           and row(scan, "HL-L1238W")["eligibility"] == "pending_hard_evidence",
           "HP scan supported, Brother scan unknown", {m["model_id"]: m["eligibility"] for m in scan["criteria_comparison"]["models"]})
    budget_rows = []
    for budget in (500, 1905, 1906, 1907, 3000, None):
        v = compare_case_research({**BASE, "budget_max_cny": budget})
        found = next((x for x in row(v, "HL-L1238W")["checks"] if x["criterion_id"] == "C-BUDGET"), None)
        expected = None if budget is None else ("above" if 1906 > budget else "at_or_below")
        budget_rows.append({"budget": budget, "relation": found["relation"] if found else None,
                            "expected": expected, "live_budget": row(v, "HL-L1238W")["regional_budget_verified"],
                            "reason_present": any(x["id"] == "CASE-06" for x in v["reasons"])})
    record("I05_budget_boundaries", all(x["relation"] == x["expected"] and not x["live_budget"]
           and x["reason_present"] == (x["budget"] is not None) for x in budget_rows),
           "MSRP relation correct; clear removes; no live-price qualification", budget_rows)
    volume_rows = []
    for bounds, expected in (([0, 50], "below"), ([200, 2000], "equal"), ([222, 333], "within"),
                             ([199, 2001], "contains"), ([199, 200], "overlap"), ([2000, 2001], "overlap"),
                             ([2001, 2010], "above")):
        v = compare_case_research({**BASE, "monthly_pages_range": bounds})
        volume_rows.append({"input": bounds, "actual": criterion(v, "M232dw", "C-VOLUME")["relation"],
                            "expected": expected, "hard_failed": row(v, "M232dw")["hard_failed"]})
    record("I06_interval_boundaries", all(x["actual"] == x["expected"] and "C-VOLUME" not in x["hard_failed"] for x in volume_rows),
           "relations including shared endpoints; manufacturer suggestion not a hard minimum", volume_rows)

    def bundle(items, count=1):
        skus = [{"sku_id": "synthetic-sku", "sku_axes": {"型号": "M232dw"}, "sku_products_count": len(items), "sku_products": items}] if count else []
        return {"schema_version": 1, "operation": "haina_mcp_synthetic_bundle", "source_mode": "synthetic_test",
                "calls": [{"tool": "product_sku_search", "query": "HP M232dw", "observed_at": "2026-11-15T00:00:00Z",
                           "payload": {"error_code": 0, "data": [{"entity_name": "HP M232dw",
                            "sku_result": {"spu_id": "synthetic-spu", "sku_count": count, "sku_list": skus}}]}}]}
    ingested = ingest_haina_mcp_bundle(bundle([{"title": "HP M232dw 打印机", "final_price": 10**400},
                                              {"title": "HP M232dw 打印机", "final_price": "909"}]),
                                     now=datetime(2026, 11, 15, 12, tzinfo=timezone.utc))
    hints = [l.get("supplier_price_hint") for e in ingested["entities"] for l in e["sale_leads"]]
    record("I07_bad_price_good_neighbor", ingested["entity_count"] == 1 and any("909" in str(x) for x in hints),
           "bad integer does not crash good neighbor; hints remain unverified", hints)
    empty = ingest_haina_mcp_bundle(bundle([], 0), now=datetime(2026, 11, 15, 12, tzinfo=timezone.utc))
    record("I08_empty_sku", all(e["sale_lead_count"] == 0 for e in empty["entities"]),
           "empty SKU list stays zero sales leads", [e["sale_lead_count"] for e in empty["entities"]])
    malformed = deepcopy(config)
    malformed["criteria"][0]["op"] = "eval"
    refused = False
    try:
        evaluate_selection(BASE, config=malformed)
    except ValueError:
        refused = True
    record("I09_unsupported_operator", refused, "reject unsupported executable operator", refused)
    conflict_color = compare_case_research({**BASE, "requirements": ["必须彩色打印"]})
    record("I10_color_text_conflict_control", not conflict_color["criteria_comparison"]["research_eligible_models"]
           and not active(conflict_color), "known color contradiction stays blocked", conflict_color["criteria_comparison"]["user_condition_conflicts"])

    raw_scan = {**BASE, "requires_scan": False, "requires_auto_duplex": False, "requirements": ["必须扫描"]}
    state = apply_turn(new_dialogue(), raw_scan, raw_text="独立合成：原话必须扫描，确认项不需要扫描")
    primary = compare_dialogue(state)
    research = compare_case_research(raw_scan)
    record("I11_raw_scan_conflict_propagation", primary["status"] == "condition_conflict"
           and not research["criteria_comparison"]["research_eligible_models"] and not active(research),
           "same input's primary condition conflict blocks research candidates",
           {"primary_status": primary["status"], "research_conflicts": research["criteria_comparison"]["user_condition_conflicts"],
            "eligible": research["criteria_comparison"]["research_eligible_models"], "active": active(research)}, "G1")
    unrecognized = {**BASE, "requires_scan": False, "requires_auto_duplex": False, "requirements": ["必须A3幅面"]}
    u = compare_case_research(unrecognized)
    record("I12_unrecognized_hard_requirement", not u["criteria_comparison"]["research_eligible_models"] and not active(u),
           "unresolved hard requirement stays pending; not an eligible model",
           {"eligible": u["criteria_comparison"]["research_eligible_models"], "questions": u["criteria_comparison"]["questions"], "active": active(u)}, "G1")

    changed = deepcopy(config)
    changed["models"][1]["facts"]["scan"]["status"] = "withdrawn"
    withdrawn_scan = altered(changed, {**BASE, "requires_scan": True})
    record("I13_withdrawn_fact_calculator_control", criterion(withdrawn_scan, "M232dw", "C-SCAN")["relation"] == "unknown"
           and row(withdrawn_scan, "M232dw")["eligibility"] == "pending_hard_evidence",
           "calculator detects withdrawn scan", criterion(withdrawn_scan, "M232dw", "C-SCAN"))
    record("I14_withdrawn_scan_explanation", not any(x["id"] == "DEC-01" for x in active(withdrawn_scan)),
           "withdrawn scan cannot still support active HP scan decision", active(withdrawn_scan), "G2")
    changed = deepcopy(config)
    changed["models"][0]["facts"]["manufacturer_suggested_retail_cny"]["valid_until"] = "2026-11-14"
    withdrawn_price = altered(changed, {**BASE, "requires_scan": False, "requires_auto_duplex": False})
    price_decision = next((x for x in active(withdrawn_price) if x["id"] == "DEC-02"), None)
    record("I15_expired_price_explanation", not price_decision or not any(x in price_decision["reason"] for x in ("1906元不高于", "1906元高于")),
           "unknown MSRP relation must not become a definite <= or > assertion",
           {"calculator": criterion(withdrawn_price, "HL-L1238W", "C-BUDGET"), "decision": price_decision}, "G2")
    changed = deepcopy(config)
    changed["models"][1]["facts"]["manufacturer_recommended_monthly_pages"]["status"] = "withdrawn"
    withdrawn_volume = altered(changed, BASE)
    volume_text = next(x["result"] for x in withdrawn_volume["model_comparison"]["comparisons"] if x["dimension"] == "low_volume_fit")
    record("I16_missing_fact_not_missing_user_answer", "本轮月印量未确认" not in volume_text,
           "provided user range remains confirmed even if manufacturer evidence withdrawn",
           {"user_range": BASE["monthly_pages_range"], "calculator": criterion(withdrawn_volume, "M232dw", "C-VOLUME"), "text": volume_text}, "G2")

    for identifier, deployment in (("I17_miniprogram_unknown_region", None), ("I18_miniprogram_overseas", "日本")):
        v = compare_case_research({**BASE, "wechat_required": True, "wechat_workflow": "miniprogram", "device_deployment_region": deployment})
        statuses = {m["model_id"]: {"eligibility": m["eligibility"],
                     "wechat": next(c["relation"] for c in m["checks"] if c["criterion_id"] == "C-WECHAT")} for m in v["criteria_comparison"]["models"]}
        record(identifier, all(x["wechat"] != "match" and x["eligibility"] == "pending_hard_evidence" for x in statuses.values()),
               "CN capability evidence does not establish required service in an unknown/overseas deployment",
               {"deployment": deployment, "models": statuses, "questions": v["criteria_comparison"]["questions"], "region_scope": v["model_comparison"]["deployment_region_scope"]}, "G3")
    cn = compare_case_research({**BASE, "wechat_required": True, "wechat_workflow": "miniprogram", "device_deployment_region": "中国大陆"})
    record("I19_miniprogram_CN_control", all(criterion(cn, m, "C-WECHAT")["relation"] == "match" for m in ("HL-L1238W", "M232dw"))
           and not cn["purchase_recommendation_approved"],
           "CN source can support CN capability research, never actual device/purchase approval", cn["criteria_comparison"]["research_eligible_models"])

    proc = subprocess.run([sys.executable, "-X", "utf8", "-m", "shopping_decision.dialogue_flow", "--real-printer-case"],
                          input=json.dumps({"text": "独立合成条件冲突CLI，不是真人新答复", "answers": raw_scan}, ensure_ascii=False)+"\n",
                          capture_output=True, encoding="utf-8", timeout=35, cwd=ROOT)
    cli = [json.loads(line) for line in proc.stdout.splitlines()] if proc.returncode == 0 else []
    cli_final = cli[-1] if len(cli) > 1 else {}
    cli_research = cli_final.get("real_printer_case_research", {})
    record("I20_normal_cli_conflict", cli_final.get("comparison", {}).get("status") == "condition_conflict"
           and not cli_research.get("criteria_comparison", {}).get("research_eligible_models", [])
           and not cli_research.get("model_comparison", {}).get("active_conditional_decisions", []),
           "normal CLI should not emit current candidates alongside a condition conflict",
           {"exit_code": proc.returncode, "primary_status": cli_final.get("comparison", {}).get("status"),
            "eligible": cli_research.get("criteria_comparison", {}).get("research_eligible_models"),
            "active": cli_research.get("model_comparison", {}).get("active_conditional_decisions")}, "G1")
    h05 = run_negative_probes(today=TODAY)
    record("I21_h05_current_date", h05["summary"]["passed"] == 8, "8 exposed offline safety diagnostics", h05["summary"])
    result = {"review_date": TODAY.isoformat(), "role": "independent_evaluator", "mode": "offline_known_regressions_and_new_synthetic_counterexamples",
              "not_recommendation_accuracy": True, "input": BASE, "checks": checks,
              "total": len(checks), "passed": sum(x["pass"] for x in checks),
              "failed_ids": [x["id"] for x in checks if not x["pass"]],
              "finding_groups": sorted({x["finding"] for x in checks if not x["pass"]}),
              "h05": h05, "cli_conflict_input": raw_scan, "cli_conflict_output": cli,
              "business_api_calls": 0, "credential_reads": 0, "real_haina_payloads_imported": 0,
              "platform_identity_verified": 0, "regional_quote_verified": 0,
              "purchase_approved": False, "transactions_enabled": False}
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: result[k] for k in ("total", "passed", "failed_ids", "finding_groups")}, ensure_ascii=False))
    return 0 if all(x["pass"] for x in checks) else 1

if __name__ == "__main__":
    raise SystemExit(main())

