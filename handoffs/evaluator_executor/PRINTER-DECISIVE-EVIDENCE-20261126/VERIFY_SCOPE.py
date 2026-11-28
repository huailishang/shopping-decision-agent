"""Freeze all pre-existing material except the exact implementation allowance."""
from pathlib import Path
import argparse,hashlib,json,subprocess
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];REL=TASK.relative_to(ROOT).as_posix()
HEAD='c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f'
PRODUCT=[*['shopping_decision/'+n+'.py' for n in ['chat_bridge','decision_worksheet','cost_scenario','decision_actions','context_builder','action_ranking','cognition_comparison','confirmed_comparison','claim_gate','evidence_snapshot','model_adapter','evidence_comparison','decision_uncertainty','decision_note']],*['desktop/'+n+'.java' for n in ['ShoppingDecisionDesktop','DesktopBridgeClient','DecisionWorksheetRegression','DecisionWorksheetSwingRegression','DecisionEvidenceRegression','DecisionEvidenceSwingRegression']],*['tests/'+n+'.py' for n in ['test_cost_scenario_binding','test_printer_decision_journey','test_session_decision_contract','test_action_ranking','test_decision_worksheet','test_worksheet_bridge','test_worksheet_persistence','test_worksheet_evidence','test_worksheet_journeys','test_history_audit_version_transition','test_decision_uncertainty','test_decisive_evidence_actions','test_uncertainty_bridge','test_uncertainty_persistence','test_decision_note']],'knowledge/printer_cognition_comparison_v1.json','scripts/audit_model_history_readonly.py']
WRITABLE={'CURRENT.md','README.md',*PRODUCT,*[REL+'/'+n for n in ['REPORT.md','COMPARISON.md','USAGE.md','REVIEW.md']]}
PREFIX=(REL+'/evidence/executor/',REL+'/evidence/evaluator/')
MANIFEST={REL+'/BASELINE.R1.json',REL+'/BASELINE.R1.sha256'}
def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def snapshot():
    paths={x for x in git('ls-files','-z','--cached','--others','--exclude-standard').decode('utf8').split('\0') if x}
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'handoffs').rglob('*.log') if p.is_file())
    return {'baseline_head':git('rev-parse','HEAD').decode().strip(),'index_diff_sha256':hashlib.sha256(git('diff','--cached','--binary')).hexdigest(),'product_sha256':{p:sha(ROOT/p) for p in PRODUCT},'protected_files_sha256':{p:sha(ROOT/p) for p in sorted(paths) if p not in WRITABLE|MANIFEST and not p.startswith(PREFIX)}}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',required=True,choices=['freeze','start','post']);phase=ap.parse_args().phase
    b=TASK/'BASELINE.R1.json';cs=TASK/'BASELINE.R1.sha256';a=snapshot()
    if phase=='freeze':
        if b.exists() or cs.exists() or a['baseline_head']!=HEAD or git('diff','--cached','--name-only','-z'):raise SystemExit('refuse refreeze, wrong HEAD or nonempty index')
        b.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf8');cs.write_text(sha(b)+'\n',encoding='ascii')
    old=json.loads(b.read_text(encoding='utf8'));before=old['protected_files_sha256'];after=a['protected_files_sha256']
    changed=sorted(p for p in before.keys()|after.keys() if before.get(p)!=after.get(p))
    pc=sorted(p for p in PRODUCT if old['product_sha256'][p]!=a['product_sha256'][p])
    checks={'head_matches':a['baseline_head']==old['baseline_head']==HEAD,'index_matches':a['index_diff_sha256']==old['index_diff_sha256'],'index_empty':not git('diff','--cached','--name-only','-z'),'manifest_matches':sha(b)==cs.read_text().strip(),'protected_unchanged':not changed}
    if phase in ('freeze','start'):checks['products_match_preflight']=not pc
    print(json.dumps({'phase':phase,'checks':checks,'protected_count':len(before),'changed_protected_paths':changed,'changed_product_paths':pc,'baseline_sha256':sha(b)},ensure_ascii=False,indent=2))
    return int(not all(checks.values()))
if __name__=='__main__':raise SystemExit(main())
