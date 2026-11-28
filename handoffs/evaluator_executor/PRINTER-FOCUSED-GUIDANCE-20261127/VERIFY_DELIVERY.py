"""Frozen delivery/accounting integrity, separate from source truth and impact."""
import hashlib,json
from pathlib import Path
from datetime import datetime
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];EX=TASK/"evidence/executor";errors=[]
def need(x,msg):
    if not x:errors.append(msg)
def load(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def refs(items,label):
    need(isinstance(items,list) and bool(items),"missing raw "+label)
    for r in items or []:
        p=(ROOT/r["path"]).resolve();p.relative_to(ROOT.resolve())
        need(p.is_file() and sha(p)==r["sha256"],"bad raw "+label)
def at(x):
    value=datetime.fromisoformat(x.replace("Z","+00:00"))
    if value.tzinfo is None:raise ValueError("timezone required")
    return value
def ledger(p,terminal):
    starts={};ends={}
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():continue
        r=json.loads(line);t=at(r["at"]);ident=r["id"]
        if r["event"]=="start":
            need(ident not in starts,"duplicate ledger start");starts[ident]=(r,t)
        elif r["event"]==terminal:
            need(ident in starts and ident not in ends,"invalid terminal");ends[ident]=(r,t)
        else:need(False,"invalid ledger event")
    need(set(starts)==set(ends),"unpaired ledger")
    for ident in starts.keys()&ends.keys():need(ends[ident][1]>=starts[ident][1],"negative ledger interval")
    return starts,ends
def main():
    try:
        for name in ("REPORT.md","COMPARISON.md","USAGE.md"):need((TASK/name).is_file() and (TASK/name).stat().st_size>300,"missing meaningful "+name)
        data=load(EX/"journeys.json");cases=data["cases"];ids={f"F{i:02d}" for i in range(1,13)};core={f"F{i:02d}" for i in range(1,11)}
        need(len(cases)==12 and {r["id"] for r in cases}==ids,"F01-F12")
        complete=sum(r["completed"] is True for r in cases);native=sum(r["completed"] is True and r["route"]=="java_event" for r in cases)
        need(complete>=11 and native>=10,"journey threshold")
        for row in cases:
            need(row["core"]==(row["id"] in core),"core identity")
            if row["id"] in core:need(row["completed"] is True,"core incomplete")
            if row["id"] in ("F01","F06","F07","F08","F12"):need(row["route"]=="java_event" and row["completed"] is True,"required native")
            need(bool(row.get("before")) and bool(row.get("after")),"missing before/after")
            refs(row.get("raw_artifacts"),row["id"])
        summary=load(EX/"summary.json");need(summary["journeys_sha256"]==sha(EX/"journeys.json") and summary["generator_sha256"]==sha(EX/"generate_summary.py"),"summary lineage")
        need(summary["completed"]==complete and summary["native_completed"]==native and summary["safety_errors"]==0,"summary counts")
        materials=load(EX/"source-audit.json");need(len(materials["claims"])>=3,"source minimum")
        for c in materials["claims"]:
            need(all(k in c for k in ("id","type","source_ids","conditions","counter_evidence","limitations","status","review_ref")),"claim audit fields")
            refs(c.get("raw_artifacts"),"claim "+c["id"])
        refs(load(EX/"B1-shared-baseline.json").get("raw_artifacts"),"B1")
        starts,ends=ledger(EX/"active-sessions.jsonl","end")
        intervals=sorted((v[1],ends[k][1]) for k,v in starts.items() if k in ends)
        need(all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])),"overlapping activity")
        p=load(EX/"process.json");known=p["known_active_seconds"];unknown=p["unknown_upper_bound_seconds"];debit=p["budget_debit_seconds"]
        need(all(type(v) in (int,float) and v>=0 for v in (known,unknown,debit)),"invalid time numbers")
        need(debit>=known+unknown and debit<=240*3600,"budget cap or understatement")
        wall=sum((b-a).total_seconds() for a,b in intervals);need(known<=wall+0.01,"active time exceeds recorded intervals")
        need(p["inherited_prior_unknown"] is True,"lost inherited unknown")
        for item in p["unknown_segments"]:
            need(item.get("reason") and item.get("upper_bound_evidence") and type(item.get("upper_bound_seconds")) in (int,float) and item["upper_bound_seconds"]>=0,"unbounded unknown")
            refs(item.get("raw_artifacts"),"unknown upper bound")
        need(unknown>=sum(x["upper_bound_seconds"] for x in p["unknown_segments"]),"unknown budget omitted")
        need(len(p["repair_rounds"])<=8,"repair cap")
        for r in p["repair_rounds"]:need(at(r["end"])>=at(r["start"]) and r["reason"],"bad repair round")
        forbidden=p["forbidden_operations"];names=("model_api","model_cli","platform_api","account","device","transaction","install","external_write","git_commit","git_push","git_index")
        need(all(type(forbidden.get(k)) is int and forbidden[k]==0 for k in names),"forbidden operations missing or nonzero")
        ops,terminal=ledger(EX/"operations.jsonl","finish");reads=queries=0;failures={}
        for ident,(r,t) in ops.items():
            need(r["kind"] in ("public_read","public_query") and r.get("url") and r.get("purpose"),"bad public start")
            reads+=int(r["kind"]=="public_read");queries+=int(r["kind"]=="public_query")
            if ident in terminal:
                done=terminal[ident][0];refs([dict(path=done["artifact"],sha256=done["sha256"])],"operation")
                if done.get("failed") is True:
                    key=(r["url"],r.get("locator"));failures[key]=failures.get(key,0)+1
        need(reads<=24 and queries<=8 and all(v<=2 for v in failures.values()),"public quota")
    except (OSError,ValueError,KeyError,TypeError) as exc:errors.append(repr(exc))
    print(json.dumps(dict(errors=errors,limit="integrity and budgets only; independent semantic review still required"),ensure_ascii=False,indent=2))
    return int(bool(errors))
if __name__=="__main__":raise SystemExit(main())
