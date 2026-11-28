"""Frozen trace auditor: recompute answer discipline, task targets and common bases."""
import base64,hashlib,json,sys
from pathlib import Path
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];EX=TASK/"evidence/executor"
sys.path.insert(0,str(ROOT))
from shopping_decision.chat_bridge import submit_message
errors=[]
def need(ok,why):
    if not ok:errors.append(why)
def load(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def ref(r):
    p=(ROOT/r["path"]).resolve();p.relative_to(ROOT.resolve())
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=r["sha256"]:raise ValueError("bad artifact "+str(p))
    return p
def inspect(arm,reference):
    raw=load(ref(arm["replay"]));expected=reference["initial_state"];last=None;answers=0;reads=0;calls=0;duplicates=0;asked=set()
    need(raw["case_id"]==reference["case_id"],"case identity")
    need(raw["basis"]==arm["basis"],"raw basis mismatch")
    for event in raw["events"]:
        kind=event["type"]
        if kind=="response":
            calls+=1
            view=load(ref(event["response_artifact"]))
            stdout=ref(event["stdout_artifact"]).read_text(encoding="utf8")
            decoded={k:base64.b64decode(v).decode() for k,v in (line.split("\t",1) for line in stdout.splitlines())}
            need(view==decoded,"stdout/decoded mismatch")
            need(event["exit_code"]==0,"product command failed")
            need(event["request"]["state"]==expected,"hidden answer/state injection")
            need(json.loads(view["state_json"])==expected,"unexpected read mutation")
            last=view
        elif kind=="answer":
            need(last is not None,"answer without displayed question")
            if last is None:continue
            field=event["field"];need(field==last.get("prompt_field") and bool(field),"not answering current question")
            allowed=reference["answer_table"].get(field,[])
            need(event["answer"] in allowed,"answer differs from frozen semantics")
            duplicates+=int(field in asked);asked.add(field);answers+=1
            expected=submit_message(expected,field,event["answer"])
            last=None
        elif kind=="read":reads+=1
        elif kind=="stop":pass
        else:need(False,"unknown replay event")
    need(answers<=12 and reads<=4 and calls<=30,"replay resources exceeded")
    need(last is not None,"terminal without current product response")
    if last is None:return dict(completed=False,answers=answers,reads=reads,duplicates=duplicates)
    report=json.loads(last["report_json"]);ctx=json.loads(last["cognition_context_json"]);confirmed=ctx["user_confirmed"]
    need(all(report[k] is False for k in ("purchase_recommendation_approved","transactions_enabled","live_price_verified")),"unsafe terminal")
    target=reference["target"];complete=True
    for field,value in target.get("confirmed",{}).items():complete=complete and confirmed.get(field)==value
    for field in target.get("deferred",[]):complete=complete and field in report["deferred_fields"]
    for field in target.get("withdrawn",[]):complete=complete and field in report["withdrawn_fields"]
    if target.get("route"):
        actual=next((r for r in ctx["route_basis"] if r["id"]==target["route"]["id"]),{})
        complete=complete and actual.get("status")==target["route"]["status"]
    if target.get("next_step_contains"):complete=complete and target["next_step_contains"] in last["prompt"]
    need(bool(target),"empty target")
    need(raw["terminal"] in ("completed","stalled","incomplete"),"bad terminal")
    need((raw["terminal"]=="completed")==complete,"false completion claim")
    relevant=set(reference["relevant_fields"]);irrelevant=len(asked-relevant)
    return dict(completed=bool(complete),answers=answers,reads=reads,duplicates=duplicates,irrelevant=irrelevant)
def main():
    computed=[]
    try:
        data=load(EX/"comparisons.json");reference_path=ref(data["reference_artifact"]);reference=load(reference_path)
        refs={c["case_id"]:c for c in reference["cases"]}
        frozen=load(TASK/"TASK_CASES.json");ids={c["case_id"] for c in frozen["cases"]}
        need(set(refs)==ids,"reference case universe")
        need(len(data["pairs"])==24 and {p["case_id"] for p in data["pairs"]}==ids,"exact 24 pairs")
        for p in data["pairs"]:
            r=refs[p["case_id"]];basis=p["basis"]
            spec=next(c for c in frozen["cases"] if c["case_id"]==p["case_id"])
            need(set(spec["critical_fields"])<=set(r["relevant_fields"]),"critical factor removed from reference")
            for field,answer in spec["anchor_answers"].items():need(answer in r["answer_table"].get(field,[]),"frozen anchor answer removed")
            if spec["expected_route"]:need(r["target"].get("route")==spec["expected_route"],"route target weakened")
            need(all(k in basis for k in ("as_of","source_set_sha256","reference_sha256","limits")),"missing common basis")
            need(basis.get("reference_sha256")==hashlib.sha256(reference_path.read_bytes()).hexdigest(),"reference hash drift")
            need(basis["limits"]==frozen["limits"],"resource basis differs")
            need(all(p[a]["basis"]==basis for a in ("a","b")),"unfair arms")
            for item in p.get("reference_artifacts",[]):ref(item)
            a=inspect(p["a"],r);b=inspect(p["b"],r);computed.append(dict(case_id=p["case_id"],a=a,b=b))
        ch=load(EX/"challenge-results.json")
        need({r["id"] for r in ch["cases"]}=={"CH01","CH02","CH03","CH04"},"four sensitivity challenges")
        for row in ch["cases"]:
            need(row["detected"] is True and row.get("expected") and row.get("observed"),"challenge not detected")
            need(bool(row.get("raw_artifacts")),"missing challenge raw")
            for item in row.get("raw_artifacts",[]):ref(item)
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as exc:errors.append(repr(exc))
    print(json.dumps(dict(errors=errors,recomputed=computed,limit="trace discipline and finite frozen targets; not human learning or source truth"),ensure_ascii=False,indent=2))
    return int(bool(errors))
if __name__=="__main__":raise SystemExit(main())
