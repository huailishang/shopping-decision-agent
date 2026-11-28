"""Recompute delivery counts, raw hashes and bounded operation/time ledgers."""
import hashlib,json,re
from datetime import datetime
from pathlib import Path
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];EX=TASK/'evidence/executor'
errors=[]
def need(ok,message):
    if not ok:errors.append(message)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def local(path):
    p=(ROOT/path).resolve();p.relative_to(ROOT.resolve());return p
def timestamp(text):
    value=datetime.fromisoformat(text.replace('Z','+00:00'))
    if value.tzinfo is None:raise ValueError('timezone_required')
    return value
def load(path):
    try:return json.loads(path.read_text(encoding='utf8'))
    except (OSError,ValueError,TypeError) as exc:errors.append(str(path.relative_to(ROOT))+':'+type(exc).__name__);return {}
for name in ['REPORT.md','COMPARISON.md','USAGE.md']:
    path=TASK/name;need(path.is_file() and path.stat().st_size>250,'missing meaningful '+name)
raw=EX/'journeys.json';data=load(raw);cases=data.get('cases',[]);core={'J%02d'%i for i in range(1,9)}
need(data.get('schema_version')==1 and bool(data.get('baseline_description')),'missing schema/baseline')
need(len(cases)==12 and {c.get('id') for c in cases}=={'J%02d'%i for i in range(1,13)},'require exactly J01-J12')
completed=sum(c.get('completed') is True for c in cases);core_completed=sum(c.get('completed') is True and c.get('id') in core for c in cases)
native=sum(c.get('completed') is True and c.get('route')=='java_event' for c in cases)
need(completed>=10 and core_completed==8 and native>=6,'completion/core/native threshold not met')
for case in cases:
    ident=case.get('id');need(bool(case.get('expected')) and bool(case.get('before')) and bool(case.get('after')),'missing expectations or actual before/after:'+str(ident))
    need(case.get('route') in ('java_event','bridge_process'),'invalid task route:'+str(ident))
    if ident in ('J02','J07'):need(case.get('route')=='java_event' and case.get('completed') is True,'cost flip/restore need native events')
    refs=case.get('raw_artifacts',[]);need(bool(refs),'missing raw artifacts:'+str(ident))
    for ref in refs:
        try:p=local(ref['path']);need(p.is_file() and sha(p)==ref['sha256'],'raw artifact missing/hash mismatch:'+ref['path'])
        except (KeyError,ValueError,OSError,TypeError) as exc:errors.append('bad artifact:'+str(exc))
summary=load(EX/'journey-summary.json');generator=EX/'generate_journeys.py'
need(raw.is_file() and summary.get('raw_sha256')==sha(raw),'journey raw digest mismatch')
need(generator.is_file() and summary.get('generator_sha256')==sha(generator),'generator digest mismatch')
for key,value in [('completed',completed),('core_completed',core_completed),('java_event_completed',native)]:need(summary.get(key)==value,'summary count mismatch:'+key)
ledger=EX/'operations.jsonl';starts={};finished=set();reads=queries=0
need(ledger.is_file(),'missing operations.jsonl including empty 0-call ledger')
if ledger.is_file():
    for no,line in enumerate(ledger.read_text(encoding='utf8').splitlines(),1):
        try:
            row=json.loads(line);ident=row['id'];at=timestamp(row['at'])
            if row['event']=='start':
                need(ident not in starts,'duplicate operation ID');need(row['kind'] in ('public_read','public_query'),'bad external operation kind')
                need(bool(row.get('url')) and bool(row.get('purpose')),'missing operation purpose/URL')
                starts[ident]=(row,at);reads+=row['kind']=='public_read';queries+=row['kind']=='public_query'
            elif row['event']=='finish':
                need(ident in starts and ident not in finished,'finish without unique start')
                if ident in starts:need(at>=starts[ident][1],'finish before start')
                need(bool(row.get('result')),'missing result including failures');p=local(row['artifact']);need(p.is_file() and sha(p)==row['sha256'],'external result hash mismatch');finished.add(ident)
            else:errors.append('unknown operation event')
        except (KeyError,ValueError,TypeError,OSError) as exc:errors.append('ledger line '+str(no)+':'+str(exc))
need(set(starts)==finished,'unfinished external attempts')
need(reads<=24 and queries<=10,'executor source quota exceeded')
active=load(EX/'active-time.json');segments=[];seconds=0
for segment in active.get('segments',[]):
    try:
        start,end=timestamp(segment['start']),timestamp(segment['end']);need(end>=start and bool(segment.get('label')),'invalid active segment');segments.append((start,end));seconds+=(end-start).total_seconds()
    except (KeyError,ValueError,TypeError) as exc:errors.append('active-time:'+str(exc))
need(bool(segments) and 0<seconds<=120*3600,'missing/over-budget active work')
segments.sort();need(all(a[1]<=b[0] for a,b in zip(segments,segments[1:])),'overlapping active segments')
rounds=active.get('repair_rounds');need(isinstance(rounds,list) and len(rounds)<=5,'repair round limit/missing record')
if isinstance(rounds,list):
    need(len({str(r.get('id')) for r in rounds})==len(rounds),'duplicate repair round IDs')
    for row in rounds:
        try:need(timestamp(row['end'])>=timestamp(row['start']) and bool(row.get('reason')),'invalid repair round')
        except (KeyError,ValueError,TypeError) as exc:errors.append('repair-time:'+str(exc))
print(json.dumps({'errors':errors,'counts':{'completed':completed,'core_completed':core_completed,'java_event_completed':native,'reads':reads,'queries':queries,'active_seconds':seconds}},ensure_ascii=False,indent=2))
raise SystemExit(int(bool(errors)))
