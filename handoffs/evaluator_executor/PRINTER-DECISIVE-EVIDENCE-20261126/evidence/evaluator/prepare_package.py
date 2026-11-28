"""Evaluator preparation: execute real pretests, never implement product features."""
from pathlib import Path
import ast,hashlib,json,subprocess,sys
from datetime import datetime,timezone
E=Path(__file__).resolve().parent;TASK=E.parents[1];ROOT=TASK.parents[2]
out=TASK/'preparation';out.mkdir(exist_ok=True)
rows=[]
for name,args in [('action',['VERIFY_ACTION.py']),('uncertainty',['VERIFY_UNCERTAINTY.py']),('tests',['VERIFY_TESTS.py']),('java',['VERIFY_JAVA.py','--role','executor']),('delivery',['VERIFY_DELIVERY.py'])]:
    argv=[sys.executable,'-X','utf8',str(TASK/args[0]),*args[1:]];start=datetime.now(timezone.utc).isoformat()
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=180)
    (out/(name+'.stdout.txt')).write_bytes(p.stdout);(out/(name+'.stderr.txt')).write_bytes(p.stderr)
    rows.append({'id':name,'argv':argv,'start':start,'end':datetime.now(timezone.utc).isoformat(),'exit_code':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest(),'expected_preparation_exit_code':1,'meaning':'real observed missing/failing target, not completed implementation'})
for f in TASK.glob('VERIFY_*.py'):ast.parse(f.read_text(encoding='utf8'),filename=str(f))
summary={'task_id':TASK.name,'status':'EXPECTED_FAILURES_CONFIRMED' if all(r['exit_code']==1 for r in rows) else 'PREPARATION_MISMATCH','checks':rows,'product_changes':0,'real_external_calls':0}
(out/'preflight.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2));raise SystemExit(int(summary['status']!='EXPECTED_FAILURES_CONFIRMED'))
