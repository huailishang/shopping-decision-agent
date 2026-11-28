"""One-time package freeze with independent start receipt; no product changes."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
TASK=HERE.parents[1]
ROOT=TASK.parents[2]
rows=[]
for phase in ('freeze','start'):
    command=['python3','-X','utf8',str(TASK/'VERIFY_SCOPE.py'),'--phase',phase]
    started=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=120)
    (HERE/(phase+'.stdout.txt')).write_bytes(result.stdout)
    (HERE/(phase+'.stderr.txt')).write_bytes(result.stderr)
    rows.append(dict(phase=phase,command=command,started_at_utc=started,
        finished_at_utc=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode))
    print(result.stdout.decode('utf8'),flush=True)
    if result.returncode:
        print(result.stderr.decode('utf8'),flush=True)
        break
(HERE/'freeze-receipts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
raise SystemExit(int(any(r['exit_code'] for r in rows)))
