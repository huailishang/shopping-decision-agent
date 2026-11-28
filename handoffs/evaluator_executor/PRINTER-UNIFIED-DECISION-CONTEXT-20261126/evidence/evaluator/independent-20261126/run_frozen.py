"""Independent execution of the seven frozen commands; no product mutation."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

OUT=Path(__file__).resolve().parent
TASK=OUT.parents[2]
ROOT=TASK.parents[2]
REL=TASK.relative_to(ROOT).as_posix()
commands=[
    ['python3','-X','utf8',REL+'/VERIFY_BUSINESS.py'],
    ['python3','-X','utf8',REL+'/VERIFY_DELIVERY.py'],
    ['python3','-X','utf8','handoffs/evaluator_executor/PRINTER-CANDIDATE-TRADEOFF-20261125/VERIFY_CANDIDATES.py'],
    ['python3','-X','utf8','handoffs/evaluator_executor/PRINTER-COGNITION-TO-COMPARISON-20261124/REPLAY_CASES.py'],
    ['python3','-X','utf8','-m','unittest','discover','-s','tests','-q'],
    ['python3','-X','utf8','scripts/audit_model_history_readonly.py','--task','handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118'],
    ['python3','-X','utf8',REL+'/VERIFY_SCOPE.py','--phase','post'],
]
results=[]
for i,command in enumerate(commands,1):
    label='VP-%02d'%i
    start=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=240)
    (OUT/(label+'.stdout.txt')).write_bytes(result.stdout)
    (OUT/(label+'.stderr.txt')).write_bytes(result.stderr)
    row=dict(id=label,command=command,started_at_utc=start,
             finished_at_utc=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode)
    results.append(row)
    print(json.dumps(row),flush=True)
(OUT/'frozen-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
sys.exit(int(any(r['exit_code'] for r in results)))
