"""Record protected inputs before preparing the experiment; no product writes."""
from pathlib import Path
import hashlib, json, subprocess, time, sys
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
UP=ROOT.parent/'intent-demand-lab'
OUT=HERE/'evidence'/'executor'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args, cwd=ROOT):
    return subprocess.check_output(['git',*args],cwd=cwd)
def inventory():
    from concurrent.futures import ThreadPoolExecutor
    jobs=[]
    for repo, prefix in [(ROOT,'shopping'),(UP,'upstream')]:
        raw=git('ls-files','-z','--cached','--others','--exclude-standard',cwd=repo)
        for item in sorted(set(raw.decode('utf-8').split('\0'))-{''}):
            p=repo/item
            if repo==ROOT and p.is_relative_to(HERE):
                if item.split('/')[-1] not in {'CONTRACT.md','START_HERE.md','VALIDATION_PLAN.yaml','REVIEW_PREDECESSOR.md','INDEPENDENT_PROBE.py'} and '/evidence/evaluator/' not in item: continue
            jobs.append((prefix+'/'+item,p))
    def one(job):
        key,p=job
        if p.is_symlink(): return key,'symlink:'+str(p.readlink())
        if not p.is_file(): return key,'missing'
        return key,sha(p)
    with ThreadPoolExecutor(max_workers=12) as pool:
        return dict(pool.map(one,jobs))
def now(): return datetime.now(timezone.utc).isoformat()
if __name__=='__main__':
    start=now(); tick=time.monotonic()
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'baseline.json'
    if target.exists(): raise SystemExit('baseline already exists')
    d={'started':start,'head':git('rev-parse','HEAD').decode().strip(),'index':hashlib.sha256(git('ls-files','--stage','-z')).hexdigest(),'files':inventory(),'status':git('status','--porcelain=v1','-z').decode(),'runtime':sys.executable}
    d.update(ended=now(),elapsed_seconds=time.monotonic()-tick)
    target.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    print('BASELINE',len(d['files']),d['head'],d['elapsed_seconds'])
