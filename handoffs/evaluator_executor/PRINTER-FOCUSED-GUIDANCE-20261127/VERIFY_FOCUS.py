"""Frozen product-entry expectations, independent from executor test assertions."""
import base64,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from shopping_decision.dialogue_flow import new_dialogue
from shopping_decision.chat_bridge import submit_message,render_chat
def call(s):
    req=dict(schema_version=1,action="guide",state=s,worksheet=None,payload={})
    p=subprocess.run([sys.executable,"-X","utf8","-m","shopping_decision.chat_bridge","--worksheet-stdin"],cwd=ROOT,input=json.dumps(req,ensure_ascii=False).encode(),capture_output=True,timeout=30)
    assert p.returncode==0,p.stderr.decode(errors="replace")
    return {k:base64.b64decode(v).decode() for k,v in (line.split("\t",1) for line in p.stdout.decode().splitlines())}
def check(s):
    v=call(s);normal=render_chat(s)
    assert json.loads(v["state_json"])==s,"guide mutated state"
    f=json.loads(v["guidance_focus_json"]);g=json.loads(v["cognition_guide_json"]);c=json.loads(v["cognition_context_json"])
    assert f==json.loads(normal["guidance_focus_json"])==c["guidance_focus"],"focus consumers disagree"
    assert f["schema_version"]==1 and type(f["schema_version"]) is int
    assert f["guide_version"]==g["version"] and f["state_version"]==s["version"]
    assert f["status"] in ("ask","research","wait","unsupported")
    assert all(f[k] is False for k in ("purchase_recommendation_approved","transactions_enabled"))
    assert f["basis_kind"] in ("user_choice","logical_constraint","supported_claim","unknown")
    assert all(isinstance(f[k],str) and f[k].strip() for k in ("question","explanation","if_unknown","next_step"))
    if f["status"]=="ask":
        assert f["field"]==v["prompt_field"] and f["question"]==v["prompt"]
        assert f["field"] not in c["user_confirmed"],"reasks confirmed field"
    else:assert f["field"] is None and v["prompt_field"]==""
    if f["basis_kind"]=="supported_claim":
        supported={x["id"]:x for x in g["claims"] if x["evidence_status"]=="supported"}
        assert f["claim_ids"] and set(f["claim_ids"])<=set(supported)
        assert f["source_ids"] and set(f["source_ids"])<={sid for cid in f["claim_ids"] for sid in supported[cid]["source_ids"]}
    return f
def main():
    results=[];explanations=[]
    for text in ("主要打印孩子黑白作业，不知道怎么买","想在家打印彩色照片，不懂参数","主要想把纸质资料扫描存档，也偶尔打印"):
        try:
            s=submit_message(submit_message(new_dialogue(),"category","打印机"),"usage",text);f=check(s)
            explanations.append(f["explanation"]);results.append(dict(case=text,passed=True,focus=f))
        except Exception as exc:results.append(dict(case=text,passed=False,error=repr(exc)))
    results.append(dict(case="coarse usage changes guidance explanation",passed=len(set(explanations))>=2))
    try:
        s=submit_message(submit_message(submit_message(new_dialogue(),"category","打印机"),"usage","家庭打印"),"needs_color","是")
        s=submit_message(s,"requires_scan","是");check(s);results.append(dict(case="confirmed requirements retained",passed=True))
    except Exception as exc:results.append(dict(case="confirmed requirements retained",passed=False,error=repr(exc)))
    print(json.dumps(dict(cases=results,passed=sum(r["passed"] for r in results),total=len(results)),ensure_ascii=False,indent=2))
    return int(not all(r["passed"] for r in results))
if __name__=="__main__":raise SystemExit(main())
