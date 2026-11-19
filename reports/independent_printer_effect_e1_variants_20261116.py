"""E1修后有限邻接检查，不是效果保留集；改值/元数据只在内存或新临时文件。"""
from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
from shopping_decision import real_printer_case as research
from shopping_decision.printer_effect_probe import derive_printer_decision_effects
from shopping_decision.selection_criteria import load_criteria,evaluate_selection

ROOT=Path(__file__).resolve().parent.parent
OUTPUT=ROOT/"reports/printer_effect_e1_independent_20261116_run01_variants.json"
BASE={"category":"printer","needs_color":False,"accepts_outsourced_color":True,
      "monthly_pages_range":[9,37],"budget_max_cny":1000,"requirements":["希望微信打印"]}


def main():
    if OUTPUT.exists():raise SystemExit("refusing_existing_output")
    checks=[]
    def rec(i,ok,expected,actual):checks.append({"id":i,"pass":bool(ok),"expected":expected,"actual":actual})
    def item(view,key):return next((j for j in view["decision_effects"]["judgments"] if j["id"]==key),None)
    cfg,_=load_criteria();cfg=deepcopy(cfg)
    cfg["models"][1]["facts"]["manufacturer_recommended_monthly_pages"]["value"]=[91,913]
    compare=research._load_model_comparison(research.COMPARISON_PATH)
    for source in compare["sources"]:
        if source["id"]=="R11":source.update(claim="合成验证91—913页/月，不是真实厂商变更",counter="synthetic memory only")
    with patch.object(research,"evaluate_selection",side_effect=lambda v:evaluate_selection(v,config=cfg,today=date(2026,11,16))), \
         patch.object(research,"_load_model_comparison",return_value=compare):
        v=research.compare_case_research(BASE)
    e=item(v,"E-VOLUME-NOT-MINIMUM")
    rec("V1_other_interval",e and "91—913页/月" in e["claim"] and e["current_check"]["product_value"]==[91,913],
        "a second valid synthetic interval propagates without the old fixed number",e)
    results=[]
    for kind in ("missing","unit_mismatch"):
        c=deepcopy(v["criteria_comparison"])
        check=next(x for x in c["models"][1]["checks"] if x["criterion_id"]=="C-VOLUME")
        check.update({"product_value":None} if kind=="missing" else {"product_unit":"pages_per_week"})
        out=derive_printer_decision_effects(values=BASE,criteria=c,model_comparison=compare)
        results.append({"kind":kind,"present":any(j["id"]=="E-VOLUME-NOT-MINIMUM" for j in out["judgments"])})
    rec("V2_missing_or_wrong_unit",not any(r["present"] for r in results),"invalid current values do not generate a fallback volume assertion",results)
    raw=json.loads(research.COMPARISON_PATH.read_text(encoding="utf-8"))
    next(s for s in raw["sources"] if s["id"]=="R11")["valid_until"]="2026-12-16"
    rejected=None
    with tempfile.TemporaryDirectory(prefix="e1_source_contract_") as directory:
        p=Path(directory)/"synthetic.json";p.write_text(json.dumps(raw),encoding="utf-8")
        try:research.compare_case_research(BASE,comparison_path=p)
        except ValueError as exc:rejected=str(exc)
    rec("V3_future_source_validity_rejected",rejected=="unsupported_model_comparison_source_validity:R11",
        "the declared unsupported validity contract is rejected even for a future date",rejected)
    turns=[{"text":"独立合成彩印冲突","answers":{**BASE,"requirements":["必须在家彩印"]}},
           {"text":"独立合成仅撤销彩印原话","answers":{"requirements":["希望微信打印"]}}]
    p=subprocess.run([sys.executable,"-X","utf8","-m","shopping_decision.dialogue_flow","--real-printer-case"],
                     input="".join(json.dumps(t,ensure_ascii=False)+"\n" for t in turns),capture_output=True,
                     encoding="utf-8",cwd=ROOT,env={**os.environ,"PYTHONUTF8":"1","PYTHONIOENCODING":"utf-8"},timeout=40)
    rows=[json.loads(s) for s in p.stdout.splitlines()][1:] if p.returncode==0 else []
    effects=[item(r["real_printer_case_research"],"E-DEFER-OR-OUTSOURCE") for r in rows]
    rec("V4_normal_cli_clear_conflict",len(effects)==2 and effects[0]["status"]=="blocked_by_user_condition_conflict"
        and effects[1]["status"]=="user_condition_only_not_product_fact" and "已确认家中黑白" in effects[1]["claim"],
        "normal CLI conflict blocks related premise then clears without stale blocking",{"exit":p.returncode,"inputs":turns,"effects":effects})
    scan=research.compare_case_research({**BASE,"requires_scan":False,"requirements":["必须扫描"]})
    rec("V5_unrelated_scan_conflict",item(scan,"E-DEFER-OR-OUTSOURCE")["status"]=="user_condition_only_not_product_fact"
        and bool(scan["criteria_comparison"]["user_condition_conflicts"]),
        "unrelated scan conflict does not erase an independently confirmed color/outsource background",item(scan,"E-DEFER-OR-OUTSOURCE"))
    wechat=research.compare_case_research({**BASE,"wechat_required":None,"wechat_workflow":"transfer_to_app", "requirements":["必须微信小程序打印"]})
    e=item(wechat,"E-WECHAT-SETUP"); qs=wechat["decision_effects"]["questions"]
    rec("V6_wechat_conflict_not_reasked",bool(wechat["criteria_comparison"]["user_condition_conflicts"])
        and e and e["status"]=="source_supported_with_user_condition_conflict"
        and any("冲突" in q for q in qs) and not any("必须还是加分" in q for q in qs),
        "known WeChat workflow conflict generates conflict resolution, not a new intensity question",{"effect":e,"questions":qs})
    result={"role":"independent_evaluator","date":"2026-11-16","scope":"six_bounded_e1_neighbors_not_accuracy_or_holdout",
            "checks":checks,"total":len(checks),"passed":sum(x["pass"] for x in checks),
            "formal_holdout_started":False,"business_calls":0,"credential_reads":0}
    with OUTPUT.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
    print(json.dumps({"total":len(checks),"passed":result["passed"],"failed":[x["id"] for x in checks if not x["pass"]]}))
    return 0 if result["passed"]==len(checks) else 1


if __name__=="__main__":raise SystemExit(main())
