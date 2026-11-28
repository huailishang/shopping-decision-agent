"""Frozen exact scope; dirty product baseline is independent from HEAD."""
import argparse, hashlib, json, subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
REL=TASK.relative_to(ROOT).as_posix()
PY=["chat_bridge","dialogue_flow","research_router","cognition_guide","guide_binding","cognition_comparison","confirmed_comparison","context_builder","action_ranking","decision_actions","decision_worksheet","decision_note","focus_guidance"]
TEST=["test_cognition_guide","test_guided_requirements","test_cognition_guide_bridge","test_cognition_context_lineage","test_cognition_guide_persistence","test_dialogue_flow","test_research_router","test_context_builder","test_action_ranking","test_decision_worksheet","test_worksheet_bridge","test_worksheet_persistence","test_worksheet_journeys","test_cognition_comparison","test_history_audit_version_transition","test_focus_guidance","test_focus_guidance_bridge","test_focus_guidance_lineage","test_guidance_replay"]
JAVA=["ShoppingDecisionDesktop","DesktopBridgeClient","CognitionGuideRegression","CognitionGuideSwingRegression","FocusGuidanceRegression","FocusGuidanceSwingRegression"]
PRODUCT=["shopping_decision/"+x+".py" for x in PY]+["tests/"+x+".py" for x in TEST]+["desktop/"+x+".java" for x in JAVA]+["knowledge/"+x+".json" for x in ["printer_cognition_guide_v1","printer_cognition_comparison_v1","printer_selection_criteria","source_directory","printer_guidance_sources_v1"]]+["scripts/audit_model_history_readonly.py"]
WRITABLE=set(PRODUCT+["CURRENT.md","README.md"]+[REL+"/"+x for x in ["REPORT.md","COMPARISON.md","USAGE.md","REVIEW.md"]])
PREFIX=(REL+"/evidence/executor/",REL+"/evidence/evaluator/")
MANIFEST={REL+"/BASELINE.json",REL+"/BASELINE.sha256"}
def git(*args):return subprocess.check_output(["git","--no-optional-locks",*args],cwd=ROOT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def snapshot():
    paths={p for p in git("ls-files","-z","--cached","--others","--exclude-standard").decode().split("\0") if p}
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/"handoffs").rglob("*.log") if p.is_file())
    return dict(baseline_head=git("rev-parse","HEAD").decode().strip(),index_sha256=hashlib.sha256(git("diff","--cached","--binary")).hexdigest(),product_sha256={p:sha(ROOT/p) for p in PRODUCT},protected_sha256={p:sha(ROOT/p) for p in sorted(paths) if p not in WRITABLE|MANIFEST and (not p.startswith(PREFIX) or p in {REL+"/evidence/evaluator/runtime-baseline.zip",REL+"/evidence/evaluator/runtime-baseline-manifest.json"})})
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--phase",choices=["freeze","start","post"],required=True);phase=ap.parse_args().phase
    bp=TASK/"BASELINE.json";sp=TASK/"BASELINE.sha256";now=snapshot()
    if phase=="freeze":
        if bp.exists() or sp.exists() or git("diff","--cached","--name-only"):raise SystemExit("refuse refreeze or nonempty index")
        bp.write_text(json.dumps(now,ensure_ascii=False,indent=2)+"\n",encoding="utf8");sp.write_text(sha(bp)+"\n",encoding="ascii")
    old=json.loads(bp.read_text(encoding="utf8"));changed=sorted(k for k in old["protected_sha256"].keys()|now["protected_sha256"].keys() if old["protected_sha256"].get(k)!=now["protected_sha256"].get(k))
    product=sorted(k for k in PRODUCT if old["product_sha256"].get(k)!=now["product_sha256"].get(k))
    checks=dict(manifest=sha(bp)==sp.read_text().strip(),head=now["baseline_head"]==old["baseline_head"],index=now["index_sha256"]==old["index_sha256"] and not git("diff","--cached","--name-only"),protected=not changed)
    if phase in ("start","freeze"):checks["products_unchanged"]=not product
    print(json.dumps(dict(phase=phase,checks=checks,protected_count=len(old["protected_sha256"]),changed_protected=changed,changed_product=product),ensure_ascii=False,indent=2))
    return int(not all(checks.values()))
if __name__=="__main__":raise SystemExit(main())
