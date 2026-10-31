"""H05 专用负向真实输入诊断：与已暴露的 H02 样本隔离，禁止写历史报告。"""
from __future__ import annotations
import json
from dataclasses import asdict, replace
from datetime import date
from hashlib import sha256
from pathlib import Path
from .contracts import PurchaseRequest, PriceObservation
from .decision import decide
from .independent_eval import Gold, judge
from .knowledge import load_cards

ROOT=Path(__file__).resolve().parent.parent

def run_negative_probes(*, today: date = date(2026,10,31)) -> dict:
    input_file=ROOT/"evaluation/h05_adversarial_inputs.json"
    raw=json.loads(input_file.read_text(encoding="utf-8"))
    all_cards=load_cards()
    records=[]
    for item in raw["cases"]:
        req_fields={**item["request"],"requirements":tuple(item["request"].get("requirements",()))}
        if isinstance(req_fields.get("observed_price"),dict):
            req_fields["observed_price"]=PriceObservation(**req_fields["observed_price"])
        req=PurchaseRequest(**req_fields)
        cards=all_cards
        override=item.get("source_overrides")
        if override:
            replacements={k:v for k,v in override.items() if k!="id"}
            cards=tuple(replace(c,**replacements) if c.id==override["id"] else c for c in cards)
        result=decide(req,cards=cards,today=today)
        judgement=judge(result,Gold((item["expected_status"],),()),cards,today=today)
        accepted_status=result.recommendation.status==item["expected_status"]
        accepted_input=all(x in result.rejected_inputs for x in item.get("expected_input_rejections",()))
        source_reasons={reason for _,rs in result.rejected_evidence for reason in rs}
        accepted_source=all(x in source_reasons for x in item.get("expected_source_rejections",()))
        no_product_effect=not (result.recommendation.live_quotes or result.recommendation.product_skus
                               or result.recommendation.authorized_side_effects)
        records.append({
          "id":item["id"],"risk":item["risk"],"description":item["description"],
          "request":asdict(req), "status":result.recommendation.status,
          "rejected_input_reasons":list(result.rejected_inputs),
          "rejected_source_reasons":[{"id":i,"reasons":list(rs)} for i,rs in result.rejected_evidence],
          "status_ok":accepted_status, "input_rejection_ok":accepted_input,
          "source_rejection_ok":accepted_source, "no_unverified_product_or_effect":no_product_effect,
          "gate_result":judgement, "probe_pass":all((accepted_status,accepted_input,accepted_source,
                                                     no_product_effect,judgement["hard_gates_pass"]))
        })
    return {"metadata":{"date":today.isoformat(),"diagnostic_not_independent":True,
                "negative_input_sha256":sha256(input_file.read_bytes()).hexdigest(),
                "evidence_cards_sha256":sha256((ROOT/"knowledge/printer_cards.json").read_bytes()).hexdigest(),
                "transaction_runtime_tested":False},
            "summary":{"total":len(records),"passed":sum(x["probe_pass"] for x in records),
                      "failed_ids":[x["id"] for x in records if not x["probe_pass"]]},
            "records":records}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--output",help="只能写尚不存在的新报告文件")
    args=p.parse_args()
    result=run_negative_probes()
    print(json.dumps(result["summary"],ensure_ascii=False,indent=2))
    if args.output:
        out=Path(args.output)
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=False,indent=2)
            f.write("\n")
        print("输出:",out)
    else:
        print("仅内存执行；不触碰 H02 报告。")

if __name__=="__main__":
    main()
