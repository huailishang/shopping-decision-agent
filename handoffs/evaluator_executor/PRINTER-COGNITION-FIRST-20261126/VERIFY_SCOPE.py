"""Frozen allowlist and immutable predecessor evidence; no wildcard product changes."""
from pathlib import Path
import argparse,hashlib,json,subprocess
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];REL=TASK.relative_to(ROOT).as_posix()
HEAD='c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f'
PRODUCT=[*['shopping_decision/'+x+'.py' for x in ['chat_bridge','dialogue_flow','research_router','knowledge','selection_criteria','cognition_comparison','confirmed_comparison','claim_gate','evidence_comparison','decision_actions','decision_worksheet','cost_scenario','context_builder','action_ranking','model_adapter','evidence_snapshot','printer_effect_probe','cognition_guide','guide_binding','decision_note']],*['knowledge/'+x+'.json' for x in ['printer_selection_criteria','printer_cognition_comparison_v1','source_directory','printer_cognition_guide_v1']],*['desktop/'+x+'.java' for x in ['ShoppingDecisionDesktop','DesktopBridgeClient','DecisionWorksheetRegression','DecisionWorksheetSwingRegression','CognitionGuideRegression','CognitionGuideSwingRegression']],*['tests/'+x+'.py' for x in ['test_cost_scenario_binding','test_printer_decision_journey','test_session_decision_contract','test_action_ranking','test_context_builder','test_decision_worksheet','test_worksheet_bridge','test_worksheet_persistence','test_worksheet_evidence','test_worksheet_journeys','test_history_audit_version_transition','test_dialogue_flow','test_research_router','test_selection_criteria','test_cognition_comparison','test_cognition_guide','test_guided_requirements','test_cognition_guide_bridge','test_cognition_context_lineage','test_cognition_guide_persistence']],'scripts/audit_model_history_readonly.py']
WRITABLE={'CURRENT.md','README.md',*PRODUCT,*[REL+'/'+x for x in ['REPORT.md','COMPARISON.md','USAGE.md','REVIEW.md']]}
PREFIX=(REL+'/evidence/executor/',REL+'/evidence/evaluator/')
MANIFEST={REL+'/BASELINE.json',REL+'/BASELINE.sha256'}
def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def snapshot():
    paths={x for x in git('ls-files','-z','--cached','--others','--exclude-standard').decode('utf8').split('\0') if x}
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'handoffs').rglob('*.log') if p.is_file())
    return {'baseline_head':git('rev-parse','HEAD').decode().strip(),'index_diff_sha256':hashlib.sha256(git('diff','--cached','--binary')).hexdigest(),'product_sha256':{p:sha(ROOT/p) for p in PRODUCT},'protected_files_sha256':{p:sha(ROOT/p) for p in sorted(paths) if p not in WRITABLE|MANIFEST and not p.startswith(PREFIX)}}
def main():
    a=argparse.ArgumentParser();a.add_argument('--phase',required=True,choices=['freeze','start','post']);phase=a.parse_args().phase
    now=snapshot();bp=TASK/'BASELINE.json';cp=TASK/'BASELINE.sha256'
    if phase=='freeze':
        if bp.exists() or cp.exists() or now['baseline_head']!=HEAD or git('diff','--cached','--name-only','-z'):raise SystemExit('refuse refreeze, wrong HEAD or nonempty index')
        bp.write_text(json.dumps(now,ensure_ascii=False,indent=2)+'\n',encoding='utf8');cp.write_text(sha(bp)+'\n',encoding='ascii')
    old=json.loads(bp.read_text(encoding='utf8'));before=old['protected_files_sha256'];after=now['protected_files_sha256']
    changed=sorted(p for p in before.keys()|after.keys() if before.get(p)!=after.get(p))
    pc=sorted(p for p in PRODUCT if old['product_sha256'][p]!=now['product_sha256'][p])
    checks={'head_matches':now['baseline_head']==old['baseline_head']==HEAD,'index_empty':not git('diff','--cached','--name-only','-z'),'index_matches':now['index_diff_sha256']==old['index_diff_sha256'],'manifest_matches':sha(bp)==cp.read_text().strip(),'protected_unchanged':not changed}
    if phase in ('freeze','start'):checks['products_match_preflight']=not pc
    print(json.dumps({'phase':phase,'checks':checks,'protected_count':len(before),'changed_protected_paths':changed,'changed_product_paths':pc,'baseline_sha256':sha(bp)},ensure_ascii=False,indent=2))
    return int(not all(checks.values()))
if __name__=='__main__':raise SystemExit(main())
