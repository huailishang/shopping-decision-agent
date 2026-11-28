"""Freeze accepted dirty workspace once; do not alter historical baselines or Git index."""
import argparse,hashlib,json,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];REL=TASK.relative_to(ROOT).as_posix()
EXPECTED_HEAD='c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f'
PRODUCT=[
 'shopping_decision/'+x+'.py' for x in ['chat_bridge','cognition_comparison','cost_scenario','decision_actions','confirmed_comparison','claim_gate','evidence_snapshot','context_builder','action_ranking','model_adapter','evidence_comparison','decision_worksheet','worksheet_io']
]+['desktop/'+x+'.java' for x in ['ShoppingDecisionDesktop','DesktopBridgeClient','ChatBridgeRegression','ChatSwingRegression','ChatNativeAuditRegression','DecisionWorksheetRegression','DecisionWorksheetSwingRegression']]+[
 'knowledge/printer_cognition_comparison_v1.json',
 *['tests/'+x+'.py' for x in ['test_cost_scenario_binding','test_printer_decision_journey','test_model_receipt_boundaries','test_session_decision_contract','test_evidence_snapshot_lineage','test_action_ranking','test_decision_worksheet','test_worksheet_bridge','test_worksheet_persistence','test_worksheet_evidence','test_worksheet_journeys']]]
WRITABLE={'CURRENT.md','README.md',*PRODUCT,*[REL+'/'+x for x in ['REPORT.md','COMPARISON.md','USAGE.md','REVIEW.md']]}
MANIFEST={REL+'/BASELINE.json',REL+'/BASELINE.sha256'}
PREFIXES=(REL+'/evidence/executor/',REL+'/evidence/evaluator/')
def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def snapshot():
    paths={p for p in git('ls-files','-z','--cached','--others','--exclude-standard').decode('utf8').split('\0') if p}
    # Also protect ignored historical .log evidence, omitted by ordinary git inventories.
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'handoffs').rglob('*.log') if p.is_file())
    return {'baseline_head':git('rev-parse','HEAD').decode().strip(),'index_diff_sha256':hashlib.sha256(git('diff','--cached','--binary')).hexdigest(),
      'product_sha256':{p:sha(ROOT/p) for p in PRODUCT},'protected_files_sha256':{p:sha(ROOT/p) for p in sorted(paths) if p not in WRITABLE|MANIFEST and not p.startswith(PREFIXES)}}
def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',required=True,choices=['freeze','start','post']);phase=p.parse_args().phase
    actual=snapshot();baseline=TASK/'BASELINE.json';checksum=TASK/'BASELINE.sha256';empty=not git('diff','--cached','--name-only','-z')
    if phase=='freeze':
        if baseline.exists() or checksum.exists() or actual['baseline_head']!=EXPECTED_HEAD or not empty:raise SystemExit('拒绝重冻、HEAD不符或索引非空，不清理用户工作。')
        baseline.write_text(json.dumps(actual,ensure_ascii=False,indent=2)+'\n',encoding='utf8');checksum.write_text(sha(baseline)+'\n',encoding='ascii')
    expected=json.loads(baseline.read_text(encoding='utf8'));before=expected['protected_files_sha256'];after=actual['protected_files_sha256']
    changed=sorted(p for p in before.keys()|after.keys() if before.get(p)!=after.get(p))
    product=sorted(p for p in PRODUCT if expected['product_sha256'][p]!=actual['product_sha256'][p])
    checks={'head_matches':actual['baseline_head']==expected['baseline_head']==EXPECTED_HEAD,'index_empty':empty,'index_matches':actual['index_diff_sha256']==expected['index_diff_sha256'],'manifest_matches':sha(baseline)==checksum.read_text(encoding='ascii').strip(),'protected_unchanged':not changed}
    if phase in ('freeze','start'):checks['product_matches_preflight']=not product
    print(json.dumps({'phase':phase,'checks':checks,'baseline_sha256':sha(baseline),'protected_count':len(before),'changed_protected_paths':changed,'changed_product_paths':product},ensure_ascii=False,indent=2))
    return int(not all(checks.values()))
if __name__=='__main__':raise SystemExit(main())
