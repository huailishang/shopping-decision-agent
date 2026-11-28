"""Verify denominators, hashes, bounded ledgers and declared completeness."""
import hashlib,json
from pathlib import Path
from datetime import datetime
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];EX=TASK/'evidence/executor'
errors=[]
def need(x,m):
    if not x:errors.append(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(x):p=(ROOT/x).resolve();p.relative_to(ROOT.resolve());return p
def load(p):
    try:return json.loads(p.read_text(encoding='utf8'))
    except (OSError,ValueError,TypeError) as exc:errors.append(str(p.relative_to(ROOT))+':'+str(exc));return {}
def at(x):
    t=datetime.fromisoformat(x.replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('timezone required')
    return t
for name in ['REPORT.md','COMPARISON.md','USAGE.md']:need((TASK/name).is_file() and (TASK/name).stat().st_size>250,'missing meaningful '+name)
expect=load(EX/'expectations.json');need(len(expect.get('cases',[]))==16,'missing preregistered 16 expectations')
raw=EX/'journeys.json';data=load(raw);cases=data.get('cases',[]);ids={f'S{i:02d}' for i in range(1,17)};core={f'S{i:02d}' for i in range(1,13)}
need(data.get('schema_version')==1 and len(cases)==16 and {x.get('id') for x in cases}==ids,'require S01-S16 exactly')
completed=sum(x.get('completed') is True for x in cases);cc=sum(x.get('completed') is True and x.get('id') in core for x in cases);native=sum(x.get('completed') is True and x.get('route')=='java_event' for x in cases)
need(completed>=14 and cc==12 and native>=8,'completion/core/native threshold')
for row in cases:
    ident=row.get('id');need(row.get('core')==(ident in core),'core flag mismatch '+str(ident))
    need(row.get('route') in ('java_event','bridge_process'),'bad route '+str(ident))
    need(bool(row.get('expected')) and bool(row.get('before')) and bool(row.get('after')),'missing task trace '+str(ident))
    if ident in ('S02','S03','S08','S09'):need(row.get('completed') is True and row.get('route')=='java_event','must be native '+str(ident))
    need(bool(row.get('raw_artifacts')),'missing raw artifacts '+str(ident))
    for ref in row.get('raw_artifacts',[]):
        try:p=local(ref['path']);need(p.is_file() and sha(p)==ref['sha256'],'raw SHA mismatch '+str(ref))
        except (ValueError,KeyError,TypeError,OSError) as exc:errors.append(str(exc))
summary=load(EX/'summary.json');gen=EX/'generate_summary.py'
need(raw.is_file() and summary.get('raw_sha256')==sha(raw),'journey SHA mismatch')
need(gen.is_file() and summary.get('generator_sha256')==sha(gen),'generator SHA mismatch')
for k,v in [('completed',completed),('core_completed',cc),('java_event_completed',native),('safety_errors',0)]:need(type(summary.get(k)) is int and summary.get(k)==v,'summary mismatch '+k)
def pairs(path,kinds=None):
    starts={};ends={};need(path.is_file(),'missing ledger '+path.name)
    if not path.is_file():return starts,ends
    for n,line in enumerate(path.read_text(encoding='utf8').splitlines(),1):
        if not line.strip():continue
        try:
            r=json.loads(line);ident=r['id'];time=at(r['at'])
            if r['event']=='start':
                need(ident not in starts,'duplicate start '+str(ident));starts[ident]=(r,time)
                if kinds:need(r.get('kind') in kinds and bool(r.get('url')) and bool(r.get('purpose')),'invalid external start')
                else:need(bool(r.get('label')),'missing active session label')
            elif r['event'] in (('finish',) if kinds else ('end',)):
                need(ident in starts and ident not in ends,'bad terminal '+str(ident));ends[ident]=(r,time)
                if kinds:
                    p=local(r['artifact']);need(p.is_file() and sha(p)==r['sha256'] and bool(r.get('result')),'invalid external terminal')
            else:errors.append('bad event '+str(r))
        except (ValueError,KeyError,TypeError,OSError) as exc:errors.append(path.name+':'+str(n)+':'+str(exc))
    need(set(starts)==set(ends),'unpaired ledger '+path.name)
    for k in starts.keys()&ends.keys():need(ends[k][1]>=starts[k][1],'time reversal')
    return starts,ends
sessions,ends=pairs(EX/'active-sessions.jsonl')
intervals=sorted((r[1],ends[k][1]) for k,r in sessions.items() if k in ends)
seconds=sum((b-a).total_seconds() for a,b in intervals)
need(0<seconds<=180*3600,'active time missing/over budget');need(all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])),'overlapping active sessions')
process=load(EX/'process.json');need(process.get('time_accounting_complete') is True and process.get('unrecorded_segments')==[],'current time accounting incomplete')
rounds=process.get('repair_rounds');need(isinstance(rounds,list) and len(rounds)<=6,'repair limit/record')
if isinstance(rounds,list):
    need(len({r.get('id') for r in rounds})==len(rounds),'duplicate repair id')
    for r in rounds:
        try:need(at(r['end'])>=at(r['start']) and bool(r['reason']),'invalid repair round')
        except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
ops,finished=pairs(EX/'operations.jsonl',{'public_query','public_read'})
reads=sum(r[0].get('kind')=='public_read' for r in ops.values());queries=sum(r[0].get('kind')=='public_query' for r in ops.values())
need(reads<=24 and queries<=10,'public quota exceeded')
print(json.dumps({'errors':errors,'counts':{'completed':completed,'core_completed':cc,'java_event_completed':native,'active_seconds':seconds,'reads':reads,'queries':queries}},ensure_ascii=False,indent=2));raise SystemExit(int(bool(errors)))
