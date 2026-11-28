import json,hashlib
from pathlib import Path
E=Path(__file__).resolve().parent;ROOT=E.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=E/'journeys.json';cases=json.loads(p.read_text(encoding='utf8'))['cases']
for case in cases:
    for r in case['raw_artifacts']:
        f=(ROOT/r['path']).resolve();f.relative_to(ROOT.resolve());assert sha(f)==r['sha256'],r['path']
out=dict(raw_sha256=sha(p),generator_sha256=sha(Path(__file__)),completed=sum(c['completed'] is True for c in cases),
    core_completed=sum(c['completed'] is True and c['core'] is True for c in cases),
    java_event_completed=sum(c['completed'] is True and c['route']=='java_event' for c in cases),
    safety_errors=sum(len(c['safety_violations']) for c in cases),
    caveat='执行者按已运行的具体断言汇总，不等同于评估者语义验收。')
(E/'summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(out,ensure_ascii=False))
