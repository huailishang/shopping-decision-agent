"""Stage B pilot, NOT the frozen 24-case measurement. Real B0 process traces."""
import base64,copy,hashlib,importlib.util,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
EX=Path(__file__).resolve().parent; TASK=EX.parents[1]; ROOT=TASK.parents[2]
ZIP=TASK/"evidence/evaluator/runtime-baseline.zip"
sys.path.insert(0,str(ROOT))
from shopping_decision.dialogue_flow import new_dialogue
from shopping_decision.chat_bridge import submit_message
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding="utf8")
    return ref(p)
def ref(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load_checker():
    spec=importlib.util.spec_from_file_location("frozen_measurement",TASK/"VERIFY_MEASUREMENT.py")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def target(v):
    c=json.loads(v["cognition_context_json"])
    return c["user_confirmed"].get("needs_color") is True and any(r["id"]=="mono_laser" and r["status"]=="not_fit" for r in c["route_basis"])
def trace(folder,base,basis,reference,hidden=False):
    s=copy.deepcopy(reference["initial_state"])
    if hidden:s=submit_message(s,"needs_color","是")
    ev=[]
    argv=[sys.executable,"-X","utf8","-m","shopping_decision.chat_bridge","--worksheet-stdin"]
    for i in range(3):
        req=dict(schema_version=1,action="guide",state=s,worksheet=None,payload={})
        q=folder/f"{i}-stdin.json";save(q,req)
        p=subprocess.run(argv,input=q.read_bytes(),capture_output=True,cwd=base,timeout=30)
        out=folder/f"{i}-stdout.txt";out.write_bytes(p.stdout)
        (folder/f"{i}-stderr.txt").write_bytes(p.stderr)
        assert p.returncode==0,p.stderr
        v={k:base64.b64decode(x).decode() for k,x in (line.split("\t",1) for line in p.stdout.decode().splitlines())}
        response=save(folder/f"{i}-response.json",v)
        ev.append(dict(type="response",request=req,argv=argv,exit_code=p.returncode,stdout_artifact=ref(out),response_artifact=response,stdin_artifact=ref(q)))
        if target(v):terminal="completed";break
        field=v.get("prompt_field")
        if not field or field not in reference["answer_table"] or i==2:terminal="stalled";break
        answer=reference["answer_table"][field][0]
        ev.append(dict(type="answer",field=field,answer=answer))
        s=submit_message(s,field,answer)
    ev.append(dict(type="stop",reason=terminal))
    raw=save(folder/"replay.json",dict(case_id="T02",basis=basis,events=ev,terminal=terminal))
    return dict(basis=basis,replay=raw)
def main():
    folder=EX/"measurement-pilot";folder.mkdir(exist_ok=True)
    # Reference chosen from frozen T02 scenario, not product output.
    s=submit_message(submit_message(new_dialogue(),"category","打印机"),"usage","想在家打印彩色照片，不懂参数")
    reference=dict(case_id="T02",initial_state=s,answer_table={"needs_color":["是"],"budget_max_cny":["1000"]},relevant_fields=["needs_color"],target={"confirmed":{"needs_color":True},"route":{"id":"mono_laser","status":"not_fit"}},reason="本人必须在家彩印，黑白路线逻辑上不适用；预算不是此路线判断的必要答复")
    rr=save(folder/"pilot-reference.json",reference)
    basis=dict(as_of="2026-11-27",source_set_sha256=ref(ZIP)["sha256"],reference_sha256=rr["sha256"],limits=json.loads((TASK/"TASK_CASES.json").read_text(encoding="utf8"))["limits"])
    checker=load_checker()
    def inspect(arm):
        checker.errors.clear(); result=checker.inspect(arm,reference)
        return dict(metrics=result,errors=checker.errors[:])
    cases=[]
    with tempfile.TemporaryDirectory(prefix="focus-pilot-") as temp:
        base=Path(temp)/"base";base.mkdir()
        with zipfile.ZipFile(ZIP) as z:z.extractall(base)
        a=trace(folder/"aa1",base,basis,reference)
        b=trace(folder/"aa2",base,basis,reference)
        aa,bb=inspect(a),inspect(b)
        cases.append(dict(id="CH01",expected="same metrics and no trace errors",observed=[aa,bb],detected=aa==bb and not aa["errors"] and aa["metrics"]["completed"],raw_artifacts=[a["replay"],b["replay"],rr]))
        hidden=trace(folder/"hidden",base,basis,reference,hidden=True)
        h=inspect(hidden)
        cases.append(dict(id="CH03",expected="hidden state injection detected",observed=h,detected="hidden answer/state injection" in h["errors"],raw_artifacts=[hidden["replay"],rr]))
        # Deliberately replace the selected question in an isolated copy only.
        bridge=base/"shopping_decision/chat_bridge.py"
        old=bridge.read_text(encoding="utf8")
        needle='    editable = "\\n".join'
        assert old.count(needle)==1
        injected='    if v.get("category") == "printer" and "needs_color" not in v:\n        active = "" if "budget_max_cny" in v else "budget_max_cny"\n        prompt = QUESTION["budget_max_cny"] if active else "测试：故意阻断彩色问题"\n        choices = REFS["budget_max_cny"] if active else []\n'
        bridge.write_text(old.replace(needle,injected+needle),encoding="utf8")
        bad=trace(folder/"wrong-question",base,basis,reference)
        m=inspect(bad)
        patch=save(folder/"isolated-mutation.json",dict(file="shopping_decision/chat_bridge.py",before_sha256=hashlib.sha256(old.encode()).hexdigest(),after_sha256=hashlib.sha256(bridge.read_bytes()).hexdigest(),injected=injected))
        cases.append(dict(id="CH02",expected="wrong question yields irrelevant answer and incomplete route",observed=m,detected=not m["metrics"]["completed"] and m["metrics"]["irrelevant"]>=1,raw_artifacts=[bad["replay"],patch,rr]))
        other=copy.deepcopy(basis);other["limits"]["max_answer_turns"]=11
        compare=save(folder/"different-basis.json",dict(a=basis,b=other))
        cases.append(dict(id="CH04",expected="resource basis mismatch is incomparable",observed={"equal":basis==other,"result":"incomparable" if basis!=other else "comparable"},detected=basis!=other,raw_artifacts=[compare,a["replay"],rr],limitation="pilot comparison of actual declared resource limits; final auditor over 24 pairs still required"))
    save(EX/"measurement-pilot-results.json",dict(cases=cases,limit="single T02 challenge pilot; not final challenge-results.json"))
    for row in cases:print(row["id"],row["detected"],json.dumps(row["observed"],ensure_ascii=False))
if __name__=="__main__":main()
