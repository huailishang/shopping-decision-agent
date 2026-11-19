"""G1-G3修后有限相邻变体；只读离线，失效/单位扰动仅在内存。"""
from __future__ import annotations
from copy import deepcopy
from datetime import date
import argparse,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch
from shopping_decision.real_printer_case import compare_case_research
from shopping_decision.selection_criteria import evaluate_selection,load_criteria

ROOT=Path(__file__).resolve().parent.parent
BASE={"category":"printer","needs_color":False,"accepts_outsourced_color":True,
      "monthly_pages_range":[0,50],"budget_max_cny":1000,
      "requires_scan":False,"requires_auto_duplex":False,"requirements":[]}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit("refusing_existing_output")
    checks=[]
    def record(name,passed,expected,actual,group=None):
        checks.append({"id":name,"pass":bool(passed),"expected":expected,"actual":actual,"finding_group":group})
    def summary(view):
        c=view["criteria_comparison"]
        return {"normalized_required":c.get("normalized_required"),"normalized_from_requirement_text":c.get("normalized_from_requirement_text"),
                "eligible":c["research_eligible_models"],"pending":c["pending_models"],"excluded":c["excluded_models"],
                "models":{m["model_id"]:{"eligibility":m["eligibility"],"hard_unknown":m["hard_unknown"],
                  "checks":{x["criterion_id"]:x["relation"] for x in m["checks"]}} for m in c["models"]},
                "active_models":[d["model"] for d in view["model_comparison"]["active_conditional_decisions"] if d["model"] in ("HL-L1238W","M232dw")],
                "purchase":view["purchase_recommendation_approved"],"transactions":view["transactions_enabled"]}
    def weave(raw,flag,flow,region=None):
        return compare_case_research({**BASE,"requirements":[raw],"wechat_required":flag,
            "wechat_workflow":flow,"device_deployment_region":region})
    a,b=summary(weave("必须微信打印",None,"unknown")),summary(weave("必须微信打印",True,"unknown"))
    record("V01_raw_and_explicit_wechat_unknown",a["normalized_required"]==b["normalized_required"] and
           len(a["pending"])==len(b["pending"])==2 and not a["eligible"] and not b["eligible"],
           "same parsed hard request gives pending regardless extra checkbox",{"raw":a,"explicit":b})
    a,b=summary(weave("必须微信小程序打印",None,"miniprogram","中国大陆")),summary(weave("必须微信小程序打印",True,"miniprogram","中国大陆"))
    record("V02_raw_and_explicit_miniprogram_CN",a["normalized_required"]==b["normalized_required"] and a["eligible"]==b["eligible"]
           and all("C-WECHAT" in m["checks"] for m in a["models"].values()) and not a["purchase"],
           "same CN capability study, no device/purchase approval",{"raw":a,"explicit":b})

    raw_app={**BASE,"requirements":["必须微信打印"],"wechat_required":None,"wechat_workflow":"transfer_to_app"}
    turns=[{"text":"独立合成：原话必须微信打印、允许转App、未额外勾选必须","answers":raw_app},
           {"text":"独立合成：相同需求再勾选微信必须","answers":{"wechat_required":True}},
           {"text":"独立合成：明确撤销微信硬要求并清除对应原话","answers":{"requirements":[],"wechat_required":False}}]
    proc=subprocess.run([sys.executable,"-X","utf8","-m","shopping_decision.dialogue_flow","--real-printer-case"],
        input="".join(json.dumps(t,ensure_ascii=False)+"\n" for t in turns),capture_output=True,encoding="utf-8",timeout=40,cwd=ROOT)
    cli=[json.loads(x) for x in proc.stdout.splitlines()] if proc.returncode==0 else []
    results=[summary(r["real_printer_case_research"]) for r in cli[1:]]
    first,second=(results[0],results[1]) if len(results)>=2 else ({},{})
    record("V03_raw_app_hard_requirement_normal_cli",proc.returncode==0 and
           first.get("normalized_required")==second.get("normalized_required") and
           not first.get("eligible") and len(first.get("pending",[]))==2 and
           all("C-WECHAT" in m["checks"] for m in first.get("models",{}).values()),
           "identical normalized transfer-to-App hard requirement must be checked and pending in both forms",
           {"exit_code":proc.returncode,"raw":first,"explicit":second},"G1-R1")
    third=results[2] if len(results)>2 else {}
    record("V04_explicit_revocation_recovers",len(third.get("eligible",[]))==2 and
           all("C-WECHAT" not in m["checks"] for m in third.get("models",{}).values()) and not third.get("purchase"),
           "explicit withdrawal clears only that hard requirement and never approves purchase",third)
    config,_=load_criteria()
    def altered(cfg,values):
        with patch("shopping_decision.real_printer_case.evaluate_selection",side_effect=lambda v:evaluate_selection(v,config=cfg,today=date(2026,11,15))):
            return compare_case_research(values)
    cfg=deepcopy(config)
    cfg["models"][1]["facts"]["scan"]["status"]="withdrawn"
    v=altered(cfg,{**BASE,"requires_scan":True,"requires_auto_duplex":True})
    s=summary(v)
    hp=s["models"]["M232dw"]
    record("V05_one_of_two_required_facts_withdrawn",hp["eligibility"]=="pending_hard_evidence"
           and hp["checks"]["C-SCAN"]=="unknown" and hp["checks"]["C-DUPLEX"]=="match" and not s["active_models"],
           "withdraw only scan; retain duplex but do not declare all hard requirements met",s)
    cfg=deepcopy(config)
    cfg["models"][0]["facts"]["manufacturer_suggested_retail_cny"]["unit"]="GBP"
    v=altered(cfg,BASE)
    snippets=[next(x["result"] for x in v["model_comparison"]["comparisons"] if x["dimension"]=="budget"),
              next(x["reason"] for x in v["reasons"] if x["id"]=="CASE-06"),
              next(x["reason"] for x in v["model_comparison"]["conditional_decisions"] if x["id"]=="DEC-02")]
    record("V06_incompatible_price_unit_explanation",all("兼容" in t and "1906元不高于" not in t and "1906元高于" not in t for t in snippets),
           "unit mismatch stays incomparable throughout current explanations",snippets)
    cfg=deepcopy(config)
    cfg["models"][1]["facts"]["manufacturer_recommended_monthly_pages"]["valid_until"]="2026-11-14"
    v=altered(cfg,{**BASE,"monthly_pages_range":[203,379]})
    text=next(x["result"] for x in v["model_comparison"]["comparisons"] if x["dimension"]=="low_volume_fit")
    record("V07_expired_fact_preserves_new_user_range","203—379" in text and "已确认" in text and "过期" in text and "本轮月印量未确认" not in text,
           "new confirmed user range is not erased by expired manufacturer evidence",text)
    states=[]
    for region in (None,"日本","Hong Kong","德国"):
        v=weave("必须微信小程序打印",True,"miniprogram",region)
        states.append({"region":region,**summary(v)})
    record("V08_deployment_scope_safe_unknowns",all(len(x["pending"])==2 and not x["eligible"] and not x["active_models"]
        and all(m["checks"].get("C-WECHAT")!="match" for m in x["models"].values()) for x in states),
        "unknown/unproven overseas deployment cannot satisfy required mini-program service",states)
    out={"review_date":"2026-11-15","role":"independent_evaluator","scope":"bounded_nearby_G123_variants_not_new_category_or_production_requirements",
         "not_recommendation_accuracy":True,"total":len(checks),"passed":sum(x["pass"] for x in checks),"checks":checks,
         "failed_ids":[x["id"] for x in checks if not x["pass"]],"finding_groups":sorted({x["finding_group"] for x in checks if not x["pass"]}),
         "cli_inputs":turns,"cli_outputs":cli,"business_api_calls":0,"credential_reads":0,"purchase_approved":False,"transactions_enabled":False}
    with args.output.open("x",encoding="utf-8") as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write("\n")
    print(json.dumps({k:out[k] for k in ("total","passed","failed_ids","finding_groups")},ensure_ascii=False))
    return 0 if all(x["pass"] for x in checks) else 1
if __name__=="__main__":raise SystemExit(main())

