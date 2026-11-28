"""Reproduce B0 from frozen ZIP; answer only the displayed question."""
import base64, hashlib, json, subprocess, sys, tempfile, zipfile
from pathlib import Path
EX=Path(__file__).resolve().parent
TASK=EX.parents[1]
ROOT=TASK.parents[2]
ZIP=TASK/"evidence/evaluator/runtime-baseline.zip"
def save(p,v):
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding="utf8")
def ref(p):
    return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
CASES=[
    ("coarse_mono","主要打印孩子黑白作业，不知道怎么买",[],{"needs_color":"否"}),
    ("coarse_color","想在家打印彩色照片，不懂参数",[],{"needs_color":"是"}),
    ("coarse_scan","主要想把纸质资料扫描存档，也偶尔打印",[],{"needs_color":"暂不确定","requires_scan":"是"}),
    ("expert","家庭打印", [("needs_color","否"),("requires_scan","是"),("requires_auto_duplex","否"),("wechat_required","否")],{})
]
def main():
    results=[]
    with tempfile.TemporaryDirectory(prefix="printer-b0-") as d:
        with zipfile.ZipFile(ZIP) as z:z.extractall(d)
        sys.path.insert(0,d)
        from shopping_decision.dialogue_flow import new_dialogue
        from shopping_decision.chat_bridge import submit_message
        argv=[sys.executable,"-X","utf8","-m","shopping_decision.chat_bridge","--worksheet-stdin"]
        for case,usage,explicit,answers in CASES:
            s=submit_message(submit_message(new_dialogue(),"category","打印机"),"usage",usage)
            for field,value in explicit:s=submit_message(s,field,value)
            events=[]
            folder=EX/"baseline-prototype"/case
            folder.mkdir(parents=True,exist_ok=True)
            for i in range(3):
                req=dict(schema_version=1,action="guide",state=s,worksheet=None,payload={})
                raw=json.dumps(req,ensure_ascii=False).encode("utf8")
                q=folder/f"{i}-stdin.json"; q.write_bytes(raw)
                p=subprocess.run(argv,cwd=d,input=raw,capture_output=True,timeout=30)
                out=folder/f"{i}-stdout.txt";out.write_bytes(p.stdout)
                err=folder/f"{i}-stderr.txt";err.write_bytes(p.stderr)
                row=dict(request=req,argv=argv,exit_code=p.returncode,raw_artifacts=[ref(q),ref(out),ref(err)])
                if p.returncode:events.append(row);break
                v={k:base64.b64decode(x).decode() for k,x in (line.split("\t",1) for line in p.stdout.decode().splitlines())}
                dec=folder/f"{i}-response.json";save(dec,v)
                row["raw_artifacts"].append(ref(dec))
                row["prompt_field"]=v.get("prompt_field");row["prompt"]=v.get("prompt")
                ctx=json.loads(v["cognition_context_json"]);row["route_basis"]=ctx.get("route_basis")
                row["state_unchanged"]=json.loads(v["state_json"])==s
                events.append(row)
                field=v.get("prompt_field")
                if field not in answers:break
                answer=answers[field]
                events.append(dict(type="answer",field=field,answer=answer))
                s=submit_message(s,field,answer)
            results.append(dict(case=case,events=events))
    save(EX/"baseline-prototype.json",dict(zip=ref(ZIP),cases=results,limit="B0 prototype only; not 24 paired tasks or impact evidence"))
    for c in results:print(c["case"],[(e.get("prompt_field"),e.get("prompt")) for e in c["events"] if "prompt_field" in e])
if __name__=="__main__":main()
