"""Capture actual pre-implementation failures before freezing this package."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
ROOT=TASK.parents[2]
rows=[]
for label,name in (('business-before','VERIFY_BUSINESS.py'),('delivery-before','VERIFY_DELIVERY.py')):
    cmd=['python3','-X','utf8',str(TASK/name)]
    start=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=180)
    (HERE/(label+'.stdout.txt')).write_bytes(result.stdout)
    (HERE/(label+'.stderr.txt')).write_bytes(result.stderr)
    rows.append({'id':label,'command':cmd,'started_at_utc':start,
                 'finished_at_utc':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode})
summary={'status':'preimplementation_expected_failures_not_product_acceptance','commands':rows}
try:
    summary['failed_business_checks']=json.loads((HERE/'business-before.stdout.txt').read_text(encoding='utf8'))['failed_checks']
except (ValueError,KeyError):
    summary['failed_business_checks']=None
(HERE/'preflight.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
