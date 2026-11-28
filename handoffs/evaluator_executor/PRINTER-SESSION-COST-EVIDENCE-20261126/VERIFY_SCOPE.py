"""Freeze this package; historical contracts and earlier evidence remain immutable."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
TASK_PATH=TASK.relative_to(ROOT).as_posix()
EXPECTED_HEAD='c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f'
BASELINE=TASK/'BASELINE.json'
CHECKSUM=TASK/'BASELINE.sha256'
PRODUCT=(
    'shopping_decision/chat_bridge.py','shopping_decision/cognition_comparison.py',
    'shopping_decision/decision_actions.py','shopping_decision/claim_gate.py',
    'shopping_decision/confirmed_comparison.py','shopping_decision/context_builder.py',
    'shopping_decision/model_adapter.py','shopping_decision/action_ranking.py',
    'shopping_decision/evidence_comparison.py','knowledge/printer_cognition_comparison_v1.json',
    'shopping_decision/decision_session.py','shopping_decision/cost_scenario.py','shopping_decision/evidence_snapshot.py',
    'tests/test_action_ranking.py','tests/test_context_builder.py','tests/test_model_adapter.py',
    'tests/test_printer_lifecycle.py','tests/test_unified_decision_actions.py',
    'tests/test_cognition_comparison.py','tests/test_candidate_tradeoff.py',
    'tests/test_chat_context_admission.py','tests/test_chat_claim_binding.py',
    'tests/test_session_decision_contract.py','tests/test_cost_scenario_binding.py',
    'tests/test_model_receipt_boundaries.py','tests/test_evidence_snapshot_lineage.py',
    'tests/test_printer_decision_journey.py',
)
WRITABLE={'CURRENT.md',*PRODUCT,*(TASK_PATH+'/'+n for n in ('REPORT.md','COMPARISON.md','REVIEW.md'))}
MANIFESTS={TASK_PATH+'/BASELINE.json',TASK_PATH+'/BASELINE.sha256'}
EVIDENCE=(TASK_PATH+'/evidence/executor/',TASK_PATH+'/evidence/evaluator/')

def git(*args):
    return subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT)

def digest(path):
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def snapshot():
    paths=set(git('ls-files','-z','--cached','--others','--exclude-standard').decode('utf8').split('\0'))
    return {'baseline_head':git('rev-parse','HEAD').decode().strip(),
        'index_diff_sha256':sha256(git('diff','--cached','--binary')).hexdigest(),
        'product_sha256':{p:digest(ROOT/p) for p in PRODUCT},
        'protected_files_sha256':{p:digest(ROOT/p) for p in sorted(paths)
            if p and p not in WRITABLE|MANIFESTS and not p.startswith(EVIDENCE)}}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',required=True,choices=('freeze','start','post'))
    phase=parser.parse_args().phase
    actual=snapshot()
    index_empty=not git('diff','--cached','--name-only','-z')
    if phase=='freeze':
        if BASELINE.exists() or CHECKSUM.exists() or actual['baseline_head']!=EXPECTED_HEAD or not index_empty:
            raise SystemExit('拒绝重冻、HEAD不符或索引非空；不清理用户工作。')
        BASELINE.write_text(json.dumps(actual,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        CHECKSUM.write_text(digest(BASELINE)+'\n',encoding='ascii')
    expected=json.loads(BASELINE.read_text(encoding='utf8'))
    before,after=expected['protected_files_sha256'],actual['protected_files_sha256']
    changed=sorted(p for p in before.keys()|after.keys() if before.get(p)!=after.get(p))
    product_changes=sorted(p for p in PRODUCT if expected['product_sha256'][p]!=actual['product_sha256'][p])
    checks={'head_matches':actual['baseline_head']==expected['baseline_head']==EXPECTED_HEAD,
        'index_empty':index_empty,'index_matches':actual['index_diff_sha256']==expected['index_diff_sha256'],
        'manifest_matches':digest(BASELINE)==CHECKSUM.read_text(encoding='ascii').strip(),
        'protected_unchanged':not changed}
    if phase in ('freeze','start'):
        checks['product_matches_preflight']=not product_changes
    print(json.dumps({'phase':phase,'checks':checks,'head':actual['baseline_head'],
        'baseline_sha256':digest(BASELINE),'protected_count':len(before),
        'changed_protected_paths':changed,'changed_product_paths':product_changes},ensure_ascii=False,indent=2))
    return int(not all(checks.values()))

if __name__=='__main__':
    raise SystemExit(main())
