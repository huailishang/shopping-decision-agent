"""运行 H02 成对实验：本地数据、同程序、知识开关唯一差异。"""
from __future__ import annotations
import argparse
import json
from dataclasses import asdict, replace
from datetime import date
from hashlib import sha256
from pathlib import Path
from statistics import mean
from .contracts import PurchaseRequest, PriceObservation
from .decision import decide
from .independent_eval import Gold, judge
from .knowledge import load_cards

ROOT = Path(__file__).resolve().parent.parent

def run_split(name: str, *, today: date = date(2026, 10, 31)) -> dict:
    cases = json.loads((ROOT/"evaluation"/(name+".json")).read_text(encoding="utf-8"))["cases"]
    cards = load_cards()
    records = []
    for c in cases:
        req_data = {**c["request"], "requirements":tuple(c["request"].get("requirements",[]))}
        if isinstance(req_data.get("observed_price"), dict):
            req_data["observed_price"] = PriceObservation(**req_data["observed_price"])
        req = PurchaseRequest(**req_data)
        attack = c.get("attack","")
        effective_cards = cards
        if attack == "drop_relevant":
            effective_cards = tuple(x for x in cards if x.id not in ("CN-001","CN-003"))
        if attack == "promotion_only":
            effective_cards = tuple(replace(x,promotion=True) if x.id in ("CN-001","CN-003") else x for x in cards)
        gold = Gold(**c["gold"])
        for enabled in (False,True):
            record=decide(req,knowledge_enabled=enabled,cards=effective_cards,today=today)
            result=judge(record,gold,effective_cards,today=today)
            records.append({
                "case_id":c["id"],"scene":c["scene"],"risk":gold.risk,
                "knowledge_enabled":enabled,"request":asdict(req),
                "recommendation":asdict(record.recommendation),
                "source_refs":[{"id":i,"url":u} for i,u in record.cited_sources],
                "retrieved_card_ids":list(record.retrieved_card_ids),
                "rejected_evidence":result["rejected_evidence"],
                "rejected_inputs":result["rejected_inputs"],
                "calls":record.calls,"judgement":result
            })
    paired=[]
    for case in cases:
        before=next(x for x in records if x["case_id"]==case["id"] and not x["knowledge_enabled"])
        after=next(x for x in records if x["case_id"]==case["id"] and x["knowledge_enabled"])
        b,a=before["judgement"]["success"],after["judgement"]["success"]
        paired.append({"case_id":case["id"],"risk":case["gold"]["risk"],"before":b,"after":a,
                       "pair":"win" if a and not b else "loss" if b and not a else "tie"})
    n=len(cases)
    b=sum(x["judgement"]["success"] for x in records if not x["knowledge_enabled"])
    a=sum(x["judgement"]["success"] for x in records if x["knowledge_enabled"])
    neg={}
    for item in paired:
        if item["risk"]!="normal":
            neg.setdefault(item["risk"],[]).append(item)
    summary={"split":name,"cases":n,"knowledge_off_success":b,"knowledge_on_success":a,
             "knowledge_off_rate":round(b/n,4),"knowledge_on_rate":round(a/n,4),
             "difference_points":round(100*(a-b)/n,2),
             "wins":sum(x["pair"]=="win" for x in paired),
             "ties":sum(x["pair"]=="tie" for x in paired),
             "losses":sum(x["pair"]=="loss" for x in paired),
             "all_hard_gates_pass":all(x["judgement"]["hard_gates_pass"] for x in records),
             "content_gate_pass_count":sum(x["judgement"]["content_contract_ok"] for x in records),
             "evidence_gate_pass_count":sum(x["judgement"]["evidence_ok"] for x in records),
             "constraint_gate_pass_count":sum(x["judgement"]["constraints_ok"] for x in records),
             "price_gate_pass_count":sum(x["judgement"]["price_handling_ok"] for x in records),
             "effect_field_gate_pass_count":sum(x["judgement"]["tool_side_effects_ok"] for x in records),
             "transaction_runtime_tested":False,
             "negative_counts":{k:len(v) for k,v in sorted(neg.items())},
             "negative_knowledge_on_pass":{k:sum(i["after"] for i in v) for k,v in sorted(neg.items())},
             "avg_calls_off":mean(x["calls"] for x in records if not x["knowledge_enabled"]),
             "avg_calls_on":mean(x["calls"] for x in records if x["knowledge_enabled"])}
    fingerprints = {}
    for path in ("shopping_decision/decision.py", "shopping_decision/knowledge.py",
                 "shopping_decision/independent_eval.py", "knowledge/printer_cards.json",
                 "evaluation/"+name+".json"):
        fingerprints[path] = sha256((ROOT/path).read_bytes()).hexdigest()
    return {"summary":summary,"paired":paired,"records":records,
            "meta":{"diagnostic_only":True, "today":today.isoformat(),
                    "historical_holdout_exposed":name=="holdout_36",
                    "files_sha256":fingerprints}}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--split",choices=("development_12","holdout_36","all"),default="development_12")
    ap.add_argument("--output-dir",help="须显式指定新的报告目录。已有文件绝不覆盖。")
    args=ap.parse_args()
    for name in (("development_12","holdout_36") if args.split=="all" else (args.split,)):
        report=run_split(name)
        print(json.dumps(report["summary"],ensure_ascii=False,indent=2))
        if args.output_dir:
            out=Path(args.output_dir)/f"h05_diagnostic_{name}.json"
            out.parent.mkdir(parents=True,exist_ok=True)
            with out.open("x",encoding="utf-8") as f:
                json.dump(report,f,ensure_ascii=False,indent=2)
                f.write("\n")
            print("新诊断报告:",out)
        else:
            print("只在内存中执行；H02 既有报告保持不变。")

if __name__ == "__main__": main()
