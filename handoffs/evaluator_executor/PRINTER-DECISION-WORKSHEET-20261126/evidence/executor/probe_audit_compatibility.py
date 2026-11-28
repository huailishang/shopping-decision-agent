"""Executor-only isolated audit compatibility experiment. Never modifies the auditor.
The patch must be independently reviewed and explicitly re-frozen before production use.
"""
from pathlib import Path
import hashlib, json, subprocess, sys, types, difflib
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
AUDITOR=ROOT/'scripts/audit_model_history_readonly.py'
TASK=ROOT/'handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118'
BASE='c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f'
def sha(x):return hashlib.sha256(x).hexdigest()
def read(p):return p.read_bytes()
original=read(AUDITOR)
manifest=json.loads(read(TASK/'FROZEN_INPUTS.json'))
baseline=json.loads(read(HERE.parents[1]/'BASELINE.json'))
expected={
    'desktop/DesktopBridgeClient.java':'ba0a8c8aa5a5d1309721d0b79f09eba472a9cee000e656c00f3d579b9c2f8ff3',
    'desktop/ShoppingDecisionDesktop.java':'054c127c30b542f4b47c7b1a9fccce949303f532b68b0b19bdb62aeefd3a36ac',
}
assert baseline['baseline_head']==BASE
for name,now in expected.items():
    old=manifest['files'][name]
    assert baseline['product_sha256'][name]==old
    assert sha(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))==old
    assert sha(read(ROOT/name))==now
code=original.decode('utf8')
needle='CURRENT_TASK_ALLOWED_DRIFT = {"shopping_decision/chat_bridge.py"}'
addition='''

# Proposed worksheet transition: historical bytes must still match the
# original manifest at the pinned pre-task commit, while current bytes
# must match precisely the independently reviewed implementation.
# No wildcard or caller-supplied exception; no historical file is rewritten.
WORKSHEET_PRE_TASK_COMMIT = "'''+BASE+'''"
WORKSHEET_REVIEWED_SOURCE_SHA256 = {
'''+''.join('    '+repr(n)+': '+repr(h)+',\n' for n,h in expected.items())+'''}
'''
assert code.count(needle)==1
code=code.replace(needle,needle+addition)
needle='''            check(filename in CURRENT_TASK_ALLOWED_DRIFT or
                  filename in REVIEWED_R1_TEST_SHA256,
                  "unapproved_historical_file_drift:" + filename)'''
replacement='''            if filename in WORKSHEET_REVIEWED_SOURCE_SHA256:
                check(p.is_file() and sha(p.read_bytes()) == WORKSHEET_REVIEWED_SOURCE_SHA256[filename],
                      "worksheet_current_source_sha_mismatch:" + filename)
                historical = subprocess.check_output(
                    ["git", "show", WORKSHEET_PRE_TASK_COMMIT + ":" + filename],
                    cwd=ROOT)
                check(sha(historical) == expected,
                      "worksheet_historical_source_sha_mismatch:" + filename)
            else:
                check(filename in CURRENT_TASK_ALLOWED_DRIFT or
                      filename in REVIEWED_R1_TEST_SHA256,
                      "unapproved_historical_file_drift:" + filename)'''
assert code.count(needle)==1
code=code.replace(needle,replacement)
# Preserve exact original file; compile isolated candidate with same __file__ so
# it reads the actual historical evidence from the actual repository.
diff=''.join(difflib.unified_diff(original.decode().splitlines(True),code.splitlines(True),
    fromfile='a/scripts/audit_model_history_readonly.py',tofile='b/scripts/audit_model_history_readonly.py'))
(HERE/'audit-compatibility-proposal.diff').write_text(diff,encoding='utf8')
module=types.ModuleType('scripts.audit_model_history_readonly')
module.__file__=str(AUDITOR)
exec(compile(code,str(AUDITOR),'exec'),module.__dict__)
import scripts.audit_model_history_readonly as actual
rows=[]
def negative(name,fn,reason):
    try:fn()
    except (ValueError,OSError,subprocess.CalledProcessError) as exc:
        assert reason in str(exc),(name,reason,str(exc))
        rows.append({'test':name,'result':'PASS','error':str(exc)})
    else:raise AssertionError(name+' incorrectly accepted')
negative('unmodified production audit still rejects current source',lambda:actual.audit_history(TASK),'unapproved_historical_file_drift:desktop/DesktopBridgeClient.java')
result=module.audit_history(TASK)
assert result['scheduled']==result['completed']==6
assert result['accepted_model_outputs']==0
assert result['not_attempted_cases']==['C05','C06','C07']
assert result['parent_vp04_status']=='REJECTED_not_retroactively_repaired'
assert not result['old_evidence_modified']
rows.append({'test':'candidate accepts only known transition while preserving historical verdict','result':'PASS','audit':result})
ledger=TASK/'evidence/live/attempts.jsonl'
negative('historical ledger append rejected',lambda:module.audit_history(TASK,ledger_bytes_override=read(ledger)+b'\n'),'historical_ledger_sha_mismatch')
old_read=Path.read_bytes
def tamper_path(name,reason):
    target=(ROOT/name).resolve()
    def changed(p):
        data=old_read(p)
        return data+b'\n# simulated tamper' if p.resolve()==target else data
    with patch.object(Path,'read_bytes',changed):
        negative('simulated tamper '+name,lambda:module.audit_history(TASK),reason)
for name in expected:tamper_path(name,'worksheet_current_source_sha_mismatch:'+name)
tamper_path(str((TASK/'FROZEN_INPUTS.json').relative_to(ROOT)),'historical_frozen_manifest_sha_mismatch')
tamper_path('tests/test_minimal_research_flow.py','approved_r1_test_sha_mismatch:')
for name in expected:
    original_is_file=Path.is_file
    with patch.object(Path,'is_file',lambda p:False if p.resolve()==(ROOT/name).resolve() else original_is_file(p)):
        negative('missing current source '+name,lambda:module.audit_history(TASK),'worksheet_current_source_sha_mismatch:'+name)
    original_check_output=subprocess.check_output
    def corrupted(*args,**kw):
        argv=args[0]
        if argv[:2]==['git','show'] and argv[2]==BASE+':'+name:return b'corrupted historical snapshot'
        return original_check_output(*args,**kw)
    with patch.object(subprocess,'check_output',corrupted):
        negative('mismatched historical snapshot '+name,lambda:module.audit_history(TASK),'worksheet_historical_source_sha_mismatch:'+name)
# Find a frozen path that is not already protected and is not previously allowed.
protected=json.loads(read(module.PIN/'BASELINE.json'))['immutable_files_sha256']
other=next(n for n in manifest['files'] if n not in protected and n not in expected and n not in module.CURRENT_TASK_ALLOWED_DRIFT and n not in module.REVIEWED_R1_TEST_SHA256)
tamper_path(other,'unapproved_historical_file_drift:'+other)
assert read(AUDITOR)==original
report={'mode':'isolated_candidate_in_memory_not_production','candidate_source_sha256':sha(code.encode()),'original_auditor_sha256':sha(original),'original_auditor_unchanged':True,'baseline_commit':BASE,'approved_hashes_proposed_not_yet_reviewed':expected,'checks':rows,'passed':len(rows),'total':len(rows)}
(HERE/'audit-compatibility-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
# Optional full suite: run the exact repository suite with ONLY the proposed
# auditor substituted in memory, so no protected path is edited.
if '--full-suite' in sys.argv:
    import unittest
    sys.modules['scripts.audit_model_history_readonly']=module
    import scripts
    scripts.audit_model_history_readonly=module
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    outcome=unittest.TextTestRunner(verbosity=0).run(suite)
    print(json.dumps({'mode':'candidate_only_not_formal_gate','tests':outcome.testsRun,'errors':len(outcome.errors),'failures':len(outcome.failures),'skipped':len(outcome.skipped)}))
    assert read(AUDITOR)==original
    raise SystemExit(not outcome.wasSuccessful())
