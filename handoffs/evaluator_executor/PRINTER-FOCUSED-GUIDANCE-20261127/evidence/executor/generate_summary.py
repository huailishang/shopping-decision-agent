"""Recompute journey evidence integrity and safety from actual stored outputs."""
from pathlib import Path
import json,hashlib
EX=Path(__file__).resolve().parent;ROOT=EX.parents[4]
def load(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {"path":p.relative_to(ROOT).as_posix(),"sha256":sha(p)}
def checked(r):
    p=(ROOT/r["path"]).resolve();p.relative_to(ROOT.resolve())
    assert p.is_file() and sha(p)==r["sha256"],r
    return p
def native_report(p):
    return json.JSONDecoder().raw_decode(p.read_text(encoding="utf8").split("REPORT=",1)[1])[0]
def safe(r):return all(r.get(k) is False for k in ("purchase_recommendation_approved","transactions_enabled","live_price_verified"))
def main():
    # Pin the completed second run; never select the best-looking outcome.
    native=EX/"java-native-20261127T134725314158"
    summary=load(native/"summary.json")
    mark=native/"FocusGuidanceSwingRegression.stdout.txt"
    stdout=mark.read_text(encoding="utf8")
    native_ok=summary["passed"] and "FOCUS_GUIDANCE_NATIVE_PASS" in stdout
    rows=[];errors=[]
    for i in [1,2,3,4,5,6,7,8,11,12]:
        cid=f"F{i:02d}";before=native/(cid+"-before.txt");after=native/(cid+"-after.txt")
        a,b=native_report(before),native_report(after)
        ok=native_ok and f"PASS {cid} native event chain" in stdout
        for label,r in [("before",a),("after",b)]:
            if not safe(r):errors.append(f"{cid}:{label}")
        raw=[ref(p) for p in sorted(native.glob(cid+"-*")) if p.is_file()]+[ref(mark),ref(native/"summary.json")]
        rows.append(dict(id=cid,core=i<=10,completed=bool(ok),route="java_event",before=ref(before),after=ref(after),raw_artifacts=raw))
    remaining=load(EX/"remaining-journeys-v1/results.json")
    for row in remaining["cases"]:
        for x in row["raw_artifacts"]:
            p=checked(x)
            if p.name.endswith("-response.json") or p.name in ("fixture-rule.json","fixture-accepted.json","fixture-stale.json"):
                data=load(p)
                if "report_json" in data and not safe(json.loads(data["report_json"])):errors.append(str(p.relative_to(ROOT)))
        assert row["completed"]==all(row["checks"].values())
        rows.append(row)
    rows.sort(key=lambda r:r["id"])
    j=EX/"journeys.json"
    j.write_text(json.dumps(dict(cases=rows,limit="executor assertions on stored native/real stdin and controlled transport; independent semantic review pending"),ensure_ascii=False,indent=2),encoding="utf8")
    comparison=load(EX/"comparisons.json")
    for p in comparison["pairs"]:
        for arm in ("a","b"):
            trace=load(checked(p[arm]["replay"]))
            for e in trace["events"]:
                if e["type"]!="response":continue
                d=load(checked(e["response_artifact"]))
                if "report_json" not in d or not safe(json.loads(d["report_json"])):errors.append(f"{p['case_id']}:{arm}")
    result=dict(journeys_sha256=sha(j),generator_sha256=sha(Path(__file__)),completed=sum(r["completed"] is True for r in rows),native_completed=sum(r["completed"] is True and r["route"]=="java_event" for r in rows),safety_errors=len(errors),safety_error_details=errors,upstream=[ref(EX/n) for n in ("comparisons.json","measurement-24-audit.json","source-audit.json","challenge-results.json","B1-shared-baseline.json","remaining-journeys-v1/results.json")]+[ref(native/"summary.json"),ref(mark)],limit="offline only")
    (EX/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print(result["completed"],result["native_completed"],result["safety_errors"])
    return int(bool(errors) or result["completed"]<11 or result["native_completed"]<10)
if __name__=="__main__":raise SystemExit(main())
