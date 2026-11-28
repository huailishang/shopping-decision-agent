from pathlib import Path
import hashlib,json,subprocess,runpy
from datetime import datetime,timezone
E=Path(__file__).resolve().parent; T=E.parents[1]; ROOT=T.parents[2]
def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data=runpy.run_path(str(T/'VERIFY_SCOPE.py'))['snapshot']()
data['at']=datetime.now(timezone.utc).isoformat()
data['git_status']=git('status','--short').decode()
(E/'review-worktree.diff').write_bytes(git('diff','--binary'))
data['diff_sha256']=sha(E/'review-worktree.diff')
data['contract_sha256']=sha(T/'CONTRACT.md')
data['plan_sha256']=sha(T/'VALIDATION_PLAN.yaml')
data['report_sha256']=sha(T/'REPORT.md')
data['journeys_sha256']=sha(T/'evidence/executor/journeys.json')
data['journey_generator_sha256']=sha(T/'evidence/executor/generate_journeys.py')
(E/'review-snapshot.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in data.items() if k not in ('protected_files_sha256','product_sha256','git_status')},ensure_ascii=False))
