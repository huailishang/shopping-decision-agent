"""Capture pre-implementation failures before the new manifest is frozen."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
ROOT=TASK.parents[2]
rows=[]
for label,name in (('business-before','VERIFY_BUSINESS.py'),('delivery-before','VERIFY_DELIVERY.py')):
    command=['python3','-X','utf8',str(TASK/name)]
    started=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=180)
    (HERE/(label+'.stdout.txt')).write_bytes(result.stdout)
    (HERE/(label+'.stderr.txt')).write_bytes(result.stderr)
    rows.append(dict(id=label,command=command,started_at_utc=started,
        finished_at_utc=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode))
data={'status':'preimplementation_not_acceptance','commands':rows}
try:
    data['failed_business_checks']=json.loads((HERE/'business-before.stdout.txt').read_text(encoding='utf8'))['failed_checks']
except (ValueError,KeyError):
    data['failed_business_checks']=None
(HERE/'preflight.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(data,ensure_ascii=False,indent=2))
