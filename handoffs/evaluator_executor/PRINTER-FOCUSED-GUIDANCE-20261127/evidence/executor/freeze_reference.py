"""Freeze independent synthetic answers/terminal semantics before product edits."""
import hashlib,json,sys
from pathlib import Path
EX=Path(__file__).resolve().parent;TASK=EX.parents[1];ROOT=TASK.parents[2]
sys.path.insert(0,str(ROOT))
from shopping_decision.chat_bridge import submit_message
def ref(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
    path=EX/"replay-reference-v1.json"
    if path.exists():raise SystemExit("Refuse to overwrite frozen reference")
    draft=json.loads((EX/"replay-reference-draft-v0.json").read_text(encoding="utf8"))
    setup=json.loads((EX/"compound-setup-b0-results.json").read_text(encoding="utf8"))
    assert all(x["passed"] for x in setup["cases"])
    setups={x["case_id"]:x for x in setup["cases"]}
    # Explicit independent targets: no render_chat outputs used to choose reference.
    qualifications={"T03":"scan","T07":"scan","T08":"auto_duplex","T09":"auto_duplex","T15":"scan","T16":"wechat_miniprogram","T17":"initial_setup_without_app_or_scan"}
    for r in draft["cases"]:
        cid=r["case_id"]
        if cid in qualifications:
            # Local model evidence requires a stated route, region and workload.
            # Ordinary user only supplies these if asked; expert explicitly supplies region.
            for f,a,value in (("needs_color","否",False),("device_deployment_region","河南","河南"),("monthly_pages_range","0-50",[0,50])):
                if f not in r["initial_state"]["answers"]:
                    if cid=="T15":
                        r["initial_state"]=submit_message(r["initial_state"],f,a)
                    else:
                        r["answer_table"][f]=[a]
                        if f not in r["relevant_fields"]:r["relevant_fields"].append(f)
                    r["target"].setdefault("confirmed",{})[f]=value
            r["semantic_checks"]=[dict(kind="candidate_dimension",dimension=qualifications[cid],hard=cid not in ("T07","T09"),expected={"HP M232dw":"met","Brother HL-L1238W":"failed"} if cid in ("T03","T08","T15") else None)]
            if cid in ("T07","T09"):r["semantic_checks"][0]["expected"]=None
        elif cid in ("T10","T11","T12","T20","T21"):
            expected="research_required" if cid in ("T10","T11","T21") else "unknown"
            r["semantic_checks"]=[dict(kind="usage_research",status=expected,source_pending=cid=="T21")]
        elif cid in ("T13","T14"):
            r["semantic_checks"]=[dict(kind="no_inferred_idle",pages=[0,0] if cid=="T13" else [0,50])]
        elif cid in ("T18","T19"):
            r["semantic_checks"]=[dict(kind="budget_scope",value="hardware_only" if cid=="T18" else None)]
        elif cid=="T06":
            r["semantic_checks"]=[dict(kind="color_unknown")]
        elif cid=="T22":
            r["semantic_checks"]=[dict(kind="source_pending",source="hp-cn-home")]
        elif cid=="T23":
            r["semantic_checks"]=[dict(kind="region_confirmed",value="河南")]
        elif cid=="T24":
            r["semantic_checks"]=[dict(kind="route_exclusion",id="mono_laser")]
        else:
            r["semantic_checks"]=[dict(kind="route",**r["target"]["route"])]
        if cid in setups:r["setup_artifacts"]=setups[cid]["raw_artifacts"]
        r.pop("pending_review",None)
    out=dict(schema_version=1,status="FROZEN_EXECUTOR_REFERENCE",cases=draft["cases"],source_refs=[ref(TASK/"TASK_CASES.json"),ref(TASK/"SOURCE_PLAN.md"),ref(EX/"replay-reference-draft-v0.json"),ref(EX/"compound-setup-b0-results.json")],limitations=["Machine trace targets and additional semantic targets are separate; semantic failure must not be claimed as completed business task.","T20/T24 worksheet inputs require symmetric real setup and separate terminal evidence; precondition success alone does not pass the compound task.","Synthetic preferences fixed equally for both arms; not human comprehension."])
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf8")
    print("FROZEN",len(out["cases"]),ref(path))
if __name__=="__main__":main()
