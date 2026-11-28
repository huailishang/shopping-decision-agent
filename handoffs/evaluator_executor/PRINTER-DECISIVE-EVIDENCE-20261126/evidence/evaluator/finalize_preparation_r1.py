from pathlib import Path
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
E=Path(__file__).resolve().parent;TASK=E.parents[1];ROOT=TASK.parents[2]
skill=Path('C:/Users/HuailiShang/.codex/skills/evaluator-executor-workflow')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,argv):
    r=subprocess.run(argv,cwd=ROOT,capture_output=True)
    (E/(name+'.stdout.txt')).write_bytes(r.stdout);(E/(name+'.stderr.txt')).write_bytes(r.stderr)
    if r.returncode:print(r.stdout.decode('utf8',errors='replace'));raise SystemExit(name+' failed')
    return r
# Validate the corrected map/contract before the final freeze.
run('workflow-r1-before',[sys.executable,'-X','utf8',str(skill/'scripts/validate_workflow.py'),'--repo',str(ROOT),'--current','CURRENT.md'])
run('freeze-r1',[sys.executable,'-X','utf8',str(TASK/'VERIFY_SCOPE.py'),'--phase','freeze'])
digest=sha(TASK/'BASELINE.R1.json');old=sha(TASK/'BASELINE.json')
current=(ROOT/'CURRENT.md').read_text(encoding='utf8')
current=current.replace('/BASELINE.json','/BASELINE.R1.json').replace('baseline_sha256: '+old,'baseline_sha256: '+digest)
current=current.replace('先记录活动session start、核新BASELINE再开工','先读AMENDMENT_PREPARATION_R1并记录活动session start、核BASELINE.R1再开工')
(ROOT/'CURRENT.md').write_text(current,encoding='utf8')
run('start-r1',[sys.executable,'-X','utf8',str(TASK/'VERIFY_SCOPE.py'),'--phase','start'])
run('workflow-r1-final',[sys.executable,'-X','utf8',str(skill/'scripts/validate_workflow.py'),'--repo',str(ROOT),'--current','CURRENT.md'])
oldtask=ROOT/'handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126'
snap=json.loads((oldtask/'evidence/evaluator/review-snapshot.json').read_text(encoding='utf8'))
unchanged=all((sha(ROOT/p) if (ROOT/p).is_file() else None)==h for p,h in snap['product_sha256'].items())
assert unchanged
receipt={'at':datetime.now(timezone.utc).isoformat(),'formal_baseline':'BASELINE.R1.json','baseline_sha256':digest,'initial_failed_preparation_baseline_preserved_sha256':old,'protected_count':len(json.loads((TASK/'BASELINE.R1.json').read_text())['protected_files_sha256']),'scope_start_exit_code':0,'workflow_exit_code':0,'product_bytes_unchanged_by_evaluator':unchanged,'preparation':'EXPECTED_FAILURES_CONFIRMED','plan_checks':12,'state':'CONTRACT_FROZEN / Executor','current_sha256':sha(ROOT/'CURRENT.md')}
(E/'freeze-r1-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt,ensure_ascii=False,indent=2))
