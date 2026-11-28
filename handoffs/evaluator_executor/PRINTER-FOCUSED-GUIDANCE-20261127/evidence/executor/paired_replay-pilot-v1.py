"""Shared actual-prompt replayer. Pilot subsets are not the final 24-case gate."""
import argparse,base64,copy,hashlib,importlib.util,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
EX=Path(__file__).resolve().parent;TASK=EX.parents[1];ROOT=TASK.parents[2]
REF=EX/"replay-reference-v2.json";ZIP=EX/"runtime-b1-shared.zip"
sys.path.insert(0,str(ROOT))
from shopping_decision.chat_bridge import submit_message
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding="utf8");return ref(p)
def load(p):return json.loads(p.read_text(encoding="utf8"))
def source_hash(base):
    files=sorted((base/"knowledge").glob("*.json"))
    return hashlib.sha256(json.dumps([(p.name,sha(p)) for p in files],ensure_ascii=False).encode()).hexdigest()
def basis(base,limits):
    return dict(as_of="2026-11-27",source_set_sha256=source_hash(base),reference_sha256=sha(REF),limits=copy.deepcopy(limits))
def comparable(a,b):
    return a==b and set(a)=={"as_of","source_set_sha256","reference_sha256","limits"}
def machine_target(v,r):
    c=json.loads(v["cognition_context_json"]);report=json.loads(v["report_json"]);t=r["target"];u=c["user_confirmed"]
    return (all(u.get(k)==value for k,value in t.get("confirmed",{}).items())
        and all(f in report["deferred_fields"] for f in t.get("deferred",[]))
        and all(f in report["withdrawn_fields"] for f in t.get("withdrawn",[]))
        and (not t.get("route") or any(x["id"]==t["route"]["id"] and x["status"]==t["route"]["status"] for x in c["route_basis"]))
        and (not t.get("next_step_contains") or t["next_step_contains"] in v["prompt"]))
def semantic(v,r):
    c=json.loads(v["cognition_context_json"]);report=json.loads(v["report_json"]);u=c["user_confirmed"]
    public=(report.get("cognition_comparison") or {}).get("public") or report.get("public_decision") or {}
    checks={}
    for i,t in enumerate(r["semantic_checks"]):
        k=t["kind"]
        if k in ("route","route_exclusion"):ok=any(x["id"]==t["id"] and x["status"]==t.get("status","not_fit") for x in c["route_basis"])
        elif k=="candidate_dimension":
            dim=t["dimension"];claims={x["candidate_id"]:x["status"] for x in public.get("claims",[]) if x["dimension"]==dim}
            reqs=[x for x in public.get("decision_binding",{}).get("requirements",[]) if x["dimension"]==dim]
            ok=len(claims)==2 and bool(reqs) and all((x["importance"]=="hard")==t["hard"] for x in reqs)
            if t.get("expected"):ok=ok and claims==t["expected"]
        elif k=="usage_research":
            task=c["usage_research"];ok=task["status"]==t["status"] and bool(task["question"])
            if t.get("source_pending"):ok=ok and not task["source_ids"]
        elif k=="no_inferred_idle":ok="idle_weeks_pattern" not in u and u.get("monthly_pages_range")==t["pages"]
        elif k=="budget_scope":ok=u.get("budget_scope")==t["value"]
        elif k=="color_unknown":ok="needs_color" not in u and "needs_color" in report["deferred_fields"]
        elif k=="source_pending":
            claims=[x for x in c["cognition_claims"] if t["source"] in x["source_ids"]];ok=bool(claims) and all(x["evidence_status"]=="pending" for x in claims)
        elif k=="region_confirmed":ok=u.get("device_deployment_region")==t["value"]
        else:ok=False
        checks[str(i)+":"+k]=bool(ok)
    checks["authorization_false"]=all(report[k] is False for k in ("purchase_recommendation_approved","transactions_enabled","live_price_verified"))
    # Compound worksheet setup/terminal evidence still needs a real end-to-end audit.
    if r["case_id"] in ("T20","T23","T24"):checks["compound_terminal_setup_preserved"]=False
    return checks
def checker():
    spec=importlib.util.spec_from_file_location("frozen_auditor",TASK/"VERIFY_MEASUREMENT.py")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def replay(base,folder,r,b):
    s=copy.deepcopy(r["initial_state"]);events=[];terminal="stalled";last=None
    folder.mkdir(parents=True,exist_ok=False)
    argv=[sys.executable,"-X","utf8","-m","shopping_decision.chat_bridge","--worksheet-stdin"]
    for i in range(b["limits"]["max_answer_turns"]+1):
        req=dict(schema_version=1,action="guide",state=s,worksheet=None,payload={})
        q=folder/f"{i}-stdin.json";save(q,req)
        p=subprocess.run(argv,cwd=base,input=q.read_bytes(),capture_output=True,timeout=30)
        stdout=folder/f"{i}-stdout.txt";stdout.write_bytes(p.stdout)
        stderr=folder/f"{i}-stderr.txt";stderr.write_bytes(p.stderr)
        try:v={k:base64.b64decode(x).decode() for k,x in (l.split("\t",1) for l in p.stdout.decode().splitlines())}
        except Exception:v={"error":"cannot decode stdout"}
        vr=save(folder/f"{i}-response.json",v)
        events.append(dict(type="response",request=req,argv=argv,exit_code=p.returncode,stdout_artifact=ref(stdout),response_artifact=vr,stdin_artifact=ref(q),stderr_artifact=ref(stderr)))
        if p.returncode or "error" in v:terminal="incomplete";last=None;break
        last=v
        if machine_target(v,r):terminal="completed";break
        f=v.get("prompt_field")
        if not f or f not in r["answer_table"]:break
        if i==b["limits"]["max_answer_turns"]:terminal="incomplete";break
        a=r["answer_table"][f][0];events.append(dict(type="answer",field=f,answer=a));s=submit_message(s,f,a)
    events.append(dict(type="stop",reason=terminal))
    raw=save(folder/"replay.json",dict(case_id=r["case_id"],basis=b,events=events,terminal=terminal))
    arm=dict(basis=b,replay=raw)
    auditor=checker()
    try:
        metrics=auditor.inspect(arm,r);errors=auditor.errors[:]
    except Exception as exc:metrics={};errors=[repr(exc)]
    checks=semantic(last,r) if last else {}
    result=dict(arm=arm,metrics=metrics,trace_errors=errors,semantic_checks=checks,semantic_completed=bool(metrics.get("completed") and checks and all(checks.values()) and not errors),terminal=terminal)
    save(folder/"assessment.json",result)
    return result
def populate(base,variant):
    with zipfile.ZipFile(ZIP) as z:z.extractall(base)
    if variant=="focus":
        for name in ("chat_bridge.py","focus_guidance.py","decision_note.py","cognition_guide.py","cognition_comparison.py","context_builder.py"):
            p=ROOT/"shopping_decision"/name
            if p.exists():(base/"shopping_decision"/name).write_bytes(p.read_bytes())
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run",required=True);ap.add_argument("--cases",nargs="+",required=True);ap.add_argument("--b",choices=("baseline","focus"),default="focus");args=ap.parse_args()
    output=EX/args.run;output.mkdir(exist_ok=False)
    refs={r["case_id"]:r for r in load(REF)["cases"]};limits=load(TASK/"TASK_CASES.json")["limits"]
    pairs=[]
    for cid in args.cases:
        r=refs[cid]
        with tempfile.TemporaryDirectory(prefix="guidance-pair-") as d:
            a=Path(d)/"a";b=Path(d)/"b";a.mkdir();b.mkdir()
            populate(a,"baseline");populate(b,args.b)
            if r["setup_plan"].get("kind")=="isolated_source_lifecycle":
                for base in (a,b):
                    p=base/"knowledge/printer_cognition_guide_v1.json";data=load(p);spec=r["setup_plan"];data["sources"][spec["source"]]={"revision":spec["revision"],"status":spec["status"]};p.write_text(json.dumps(data,ensure_ascii=False),encoding="utf8")
            ba,bb=basis(a,limits),basis(b,limits);assert comparable(ba,bb)
            x=replay(a,output/cid/"a",r,ba);y=replay(b,output/cid/"b",r,bb)
            pairs.append(dict(case_id=cid,basis=ba,a=x,b=y,comparable=True))
            print(cid,"A",x["metrics"],x["trace_errors"],"B",y["metrics"],y["trace_errors"],"semantic",x["semantic_completed"],y["semantic_completed"],flush=True)
    save(output/"pilot-pairs.json",dict(reference_artifact=ref(REF),pairs=pairs,limit="pilot subset; not final comparisons.json"))
if __name__=="__main__":main()
