"""认知效果开发交付独立诊断；不是36条正式保留集或推荐准确率。"""
from __future__ import annotations
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import date
import base64
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

from shopping_decision import real_printer_case as research
from shopping_decision import desktop_bridge
from shopping_decision.h05_probes import run_negative_probes
from shopping_decision.printer_effect_probe import derive_printer_decision_effects, pair_development_views
from shopping_decision.selection_criteria import load_criteria, evaluate_selection
from shopping_decision.web import evaluate_input

ROOT = Path(__file__).resolve().parent.parent
PREFIX = "printer_effect_independent_20261116_run01"
TODAY = date(2026, 11, 16)
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
BASE = {"category": "printer", "needs_color": False, "accepts_outsourced_color": True,
        "monthly_pages_range": [17,43], "budget_max_cny": 1000,
        "requirements": ["希望微信打印", "重视可靠耐用"]}


def write_new(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def summarize(view):
    c = view["criteria_comparison"]
    return {"eligible": c["research_eligible_models"], "conflicts": c["user_condition_conflicts"],
            "models": [{"id": m["model_id"], "eligibility": m["eligibility"],
                        "checks": m["checks"]} for m in c["models"]],
            "effects": view["decision_effects"],
            "purchase": view["purchase_recommendation_approved"], "transactions": view["transactions_enabled"]}


def main():
    output = ROOT / "reports" / (PREFIX+"_validation.json")
    if output.exists(): raise SystemExit("refusing_existing_output")
    checks = []
    def record(identifier, passed, expectation, actual, finding=None):
        checks.append({"id": identifier, "pass": bool(passed), "expected": expectation,
                       "actual": actual, "finding": finding})
    def effect(view, key):
        return next((j for j in view["decision_effects"]["judgments"] if j["id"]==key), None)

    original = research.compare_case_research(BASE)
    record("P01_original_supported_context", original["decision_effects"]["supported_context_count"]==2
           and not original["purchase_recommendation_approved"] and not original["transactions_enabled"],
           "two bounded reused-source contexts, no purchase or transaction", summarize(original))

    # 合成扰动只在内存；同步改测试事实和对应测试源摘要，不冒称厂商资料已变。
    cfg,_ = load_criteria(); cfg=deepcopy(cfg)
    cfg["models"][1]["facts"]["manufacturer_recommended_monthly_pages"]["value"]=[120,980]
    cfg["source_registry"]["R11"]["limit"]="synthetic current interval 120-980; not a real manufacturer update"
    comparison = research._load_model_comparison(research.COMPARISON_PATH)
    altered_comparison = deepcopy(comparison)
    for source in altered_comparison["sources"]:
        if source["id"]=="R11":
            source["claim"]="明确合成诊断：本轮测试建议月印量120—980页，不是真实HP变更。"
            source["counter"]="合成字段变更只检验解释与当前计算一致，不作商品事实。"
            source["fact_audit"]="synthetic_memory_only_not_manufacturer_fact"
    with patch("shopping_decision.real_printer_case.evaluate_selection",
               side_effect=lambda values:evaluate_selection(values,config=cfg,today=TODAY)), \
         patch("shopping_decision.real_printer_case._load_model_comparison",return_value=altered_comparison):
        changed = research.compare_case_research(BASE)
    judgment=effect(changed,"E-VOLUME-NOT-MINIMUM")
    record("P02_changed_current_interval", not judgment or ("200—2000" not in judgment["claim"]
           and "120" in judgment["claim"] and "980" in judgment["claim"]),
           "current validated interval and current synthetic source must drive the extra text, or downgrade it",
           summarize(changed),"E1_current_value_not_propagated")

    # 撤回控制：原已实现的事实状态必须继续降级。
    revoked=deepcopy(cfg)
    revoked["models"][1]["facts"]["manufacturer_recommended_monthly_pages"]["status"]="withdrawn"
    with patch("shopping_decision.real_printer_case.evaluate_selection",
               side_effect=lambda values:evaluate_selection(values,config=revoked,today=TODAY)):
        withdrawn=research.compare_case_research(BASE)
    record("P03_volume_withdrawal_control", effect(withdrawn,"E-VOLUME-NOT-MINIMUM") is None,
           "withdrawn volume fact suppresses the extra volume claim",summarize(withdrawn))

    # 来源状态契约诊断：显式失效元数据应拒绝或降级，不能静默丢弃后宣称有据。
    raw=json.loads(research.COMPARISON_PATH.read_text(encoding="utf-8"))
    for source in raw["sources"]:
        if source["id"] in ("R7","R10"):
            source["status"]="withdrawn"
            source["valid_until"]="2026-11-15"
            source["fact_audit"]="explicitly_withdrawn_for_synthetic_contract_probe"
    source_result=None
    rejection=None
    with tempfile.TemporaryDirectory(prefix="printer_effect_source_probe_") as folder:
        p=Path(folder)/"synthetic_comparison.json"
        p.write_text(json.dumps(raw,ensure_ascii=False),encoding="utf-8")
        try:
            source_result=research.compare_case_research(BASE,comparison_path=p)
        except ValueError as exc:
            rejection=str(exc)
    source_claim=effect(source_result,"E-WECHAT-SETUP") if source_result else None
    record("P04_explicit_source_withdrawal_contract", bool(rejection) or source_claim is None
           or not source_claim.get("status","").startswith("source_supported"),
           "unsupported withdrawal metadata is safely rejected or preserved to downgrade current source support",
           {"input_source_ids":["R7","R10"],"input_status":"withdrawn","valid_until":"2026-11-15",
            "rejection":rejection,"output":summarize(source_result) if source_result else None},
           "E1_source_validity_not_propagated")

    missing=deepcopy(comparison)
    missing["sources"]=[s for s in missing["sources"] if s["id"]!="R7"]
    missing_out=derive_printer_decision_effects(values=BASE,criteria=original["criteria_comparison"],
                  model_comparison=missing,wechat_preferred=True)
    record("P05_missing_setup_source_control", not any(j["id"]=="E-WECHAT-SETUP" for j in missing_out["judgments"]),
           "deleting a required setup source suppresses the combined setup assertion",missing_out)

    conflict_values={**BASE,"requirements":["必须在家彩印","希望微信打印"]}
    conflict=research.compare_case_research(conflict_values)
    outsource=effect(conflict,"E-DEFER-OR-OUTSOURCE")
    conflicting_route=next((r for r in conflict["decision_effects"]["routes"] if r["route"]=="non_purchase_alternative"),None)
    record("P06_color_conflict_extra_route", bool(conflict["criteria_comparison"]["user_condition_conflicts"])
           and (not outsource or "已确认家中黑白" not in outsource["claim"])
           and (not conflicting_route or conflicting_route["eligibility"]=="blocked_by_user_condition_conflict"),
           "known color conflict must not become a confirmed black-and-white premise for an unblocked outsource route",
           summarize(conflict),"E1_conflict_not_propagated")

    paired=pair_development_views(original)
    record("P07_pair_diagnostic_not_effect", paired["same_hard_eligibility"] and paired["success_score"] is None
           and not paired["incremental_decision_effect_proven"],
           "shared computed eligibility is a consistency diagnostic, no measured task-success difference",paired)

    ui_input={"description":"独立合成：必须在家彩印，希望微信打印","confirmed":True,
              "monthly_pages_range":[17,43],"budget_max_cny":1000,"needs_color":False,
              "accepts_outsourced_color":True,"requirements":[]}
    web=evaluate_input(ui_input)
    web_effect=effect(web["real_printer_case_research"],"E-DEFER-OR-OUTSOURCE")
    record("P08_normal_web_conflict", web_effect is None or "已确认家中黑白" not in web_effect["claim"],
           "normal web evaluation observes the same color-conflict guard in the new extra section",
           {"input":ui_input,"research":summarize(web["real_printer_case_research"])},"E1_conflict_not_propagated")

    args=[ui_input["description"],"17-43","1000","","false","true","","","","","unknown","","","unknown",""]
    command=[sys.executable,"-X","utf8","-m","shopping_decision.desktop_bridge",
             *[base64.b64encode(x.encode("utf-8")).decode("ascii") for x in args]]
    proc=subprocess.run(command,cwd=ROOT,env=ENV,capture_output=True,encoding="utf-8",timeout=35)
    bridge={k:base64.b64decode(v).decode("utf-8") for k,v in
            (line.split("\t",1) for line in proc.stdout.splitlines() if "\t" in line)}
    visible=bridge.get("reasons","")
    record("P09_desktop_bridge_visible_conflict", proc.returncode==0 and "error" not in bridge
           and "E-DEFER-OR-OUTSOURCE：已确认家中黑白" not in visible,
           "normal desktop text must not present a confirmed-black-and-white outsource judgment during color conflict",
           {"exit_code":proc.returncode,"stderr":proc.stderr,"visible_reasons":visible,
            "audit":json.loads(bridge["report_json"]) if "report_json" in bridge else bridge},
           "E1_conflict_not_propagated")

    known_clear=research.compare_case_research({**BASE,"wechat_required":False,"requirements":[],
                                              "monthly_pages_range":[315,487]})
    record("P10_clear_preference_and_raise_volume", effect(known_clear,"E-WECHAT-SETUP") is None
           and effect(known_clear,"E-VOLUME-NOT-MINIMUM") is None,
           "cleared WeChat preference and no-longer-low volume remove their old extra claims",summarize(known_clear))
    h05=run_negative_probes(today=TODAY)
    record("P11_h05_actual_date", h05["summary"]["passed"]==8,
           "existing eight safety probes use actual 2026-11-16 date",h05["summary"])
    runtime=[]
    for label,command,timeout in [
        ("development_replay",[sys.executable,"-X","utf8","-m","scripts.run_printer_effect_development",
                               "--output","reports/"+PREFIX+"_dev.json"],60),
        ("full_suite",[sys.executable,"-X","utf8","-m","unittest","discover","-s","tests","-q"],180),
    ]:
        start=time.monotonic()
        p=subprocess.run(command,cwd=ROOT,env=ENV,capture_output=True,encoding="utf-8",errors="replace",timeout=timeout)
        runtime.append({"id":label,"command":command,"exit_code":p.returncode,
                        "elapsed_seconds":round(time.monotonic()-start,3),"stdout":p.stdout,"stderr":p.stderr})
        print(json.dumps({"check":label,"exit_code":p.returncode,"stderr_tail":p.stderr[-400:]},ensure_ascii=False),flush=True)
    result={"date":TODAY.isoformat(),"role":"independent_evaluator","mode":"bounded_development_acceptance_not_holdout",
            "checks":checks,"diagnostic_total":len(checks),"diagnostic_passed":sum(c["pass"] for c in checks),
            "failed_ids":[c["id"] for c in checks if not c["pass"]],"runtime":runtime,
            "h05":h05,"formal_holdout_started":False,"independent_holdout_denominator":0,
            "primary_task_success_rate":None,"incremental_effect":None,
            "external_business_api_calls":0,"credential_reads":0,"platform_identities":0,"regional_quotes":0,
            "purchase_approved":False,"transactions_enabled":False}
    write_new(output,result)
    print(json.dumps({"total":result["diagnostic_total"],"passed":result["diagnostic_passed"],
                      "failed":result["failed_ids"],"runtime_ok":all(r["exit_code"]==0 for r in runtime),
                      "formal_holdout_started":False},ensure_ascii=False),flush=True)
    return 0 if all(c["pass"] for c in checks) and all(r["exit_code"]==0 for r in runtime) else 1


if __name__=="__main__":
    raise SystemExit(main())
