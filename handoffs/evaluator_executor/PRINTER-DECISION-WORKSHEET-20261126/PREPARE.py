"""Evaluator-only preflight: preserve actual expected failures before freezing baseline."""
import subprocess,sys,json,hashlib
from datetime import datetime,timezone
from pathlib import Path
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];out=TASK/'preparation'
out.mkdir(exist_ok=True)
if (out/'preflight.json').exists():raise SystemExit('前测已留存，拒绝覆盖。')
rows=[]
for label,name,extra in [('business','VERIFY_BUSINESS.py',[]),('new-test-groups','VERIFY_TESTS.py',[]),('native-entry','VERIFY_JAVA.py',['--role','evaluator']),('delivery','VERIFY_DELIVERY.py',[])]:
    argv=[sys.executable,'-X','utf8',str(TASK/name),*extra];start=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=90)
    prefix=out/label
    prefix.with_suffix('.stdout.txt').write_bytes(result.stdout);prefix.with_suffix('.stderr.txt').write_bytes(result.stderr)
    row={'label':label,'argv':argv,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode,'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()}
    prefix.with_suffix('.meta.json').write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf8');rows.append(row)
summary={'status':'EXPECTED_FAILURES_CONFIRMED' if all(x['exit_code']==1 for x in rows) else 'INSPECT_ACTUAL_RESULTS','commands':rows,'meaning':'前测，不是已修复/实现；不跑无新改动的全量。'}
(out/'preflight.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False))
