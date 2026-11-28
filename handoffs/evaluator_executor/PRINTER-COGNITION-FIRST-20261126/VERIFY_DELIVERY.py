"""Frozen mechanical audit; source truth and user comprehension remain independent."""
import hashlib,json,re
from pathlib import Path
from datetime import datetime
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];EX=TASK/'evidence/executor';errors=[]
def need(x,m):
    if not x:errors.append(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(x):p=(ROOT/x).resolve();p.relative_to(ROOT.resolve());return p
def load(p):
    try:return json.loads(p.read_text(encoding='utf8'))
    except (OSError,ValueError,TypeError) as exc:errors.append(str(p.relative_to(ROOT))+':'+str(exc));return {}
def refs(items,label):
    need(isinstance(items,list) and bool(items),'missing raw references '+label)
    if not isinstance(items,list):return
    for r in items:
        try:p=local(r['path']);need(p.is_file() and sha(p)==r['sha256'],'artifact SHA mismatch '+label+':'+r['path'])
        except (ValueError,TypeError,KeyError,OSError) as exc:errors.append(label+':'+str(exc))
def at(x):
    t=datetime.fromisoformat(x.replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('timezone required')
    return t
for n in ['REPORT.md','COMPARISON.md','USAGE.md']:need((TASK/n).is_file() and (TASK/n).stat().st_size>250,'missing meaningful '+n)
expected=load(EX/'expectations.json');need(len(expected.get('cases',[]))==20,'missing preregistered 20 expectations')
raw=EX/'journeys.json';data=load(raw);cases=data.get('cases',[]);ids={f'G{i:02d}' for i in range(1,21)};core={f'G{i:02d}' for i in range(1,15)}
need(data.get('schema_version')==1 and len(cases)==20 and {c.get('id') for c in cases}==ids,'require exactly G01-G20')
completed=sum(c.get('completed') is True for c in cases);cc=sum(c.get('completed') is True and c.get('id') in core for c in cases);native=sum(c.get('completed') is True and c.get('route')=='java_event' for c in cases)
need(completed>=18 and cc==14 and native>=8,'completion/core/native threshold')
for c in cases:
    ident=c.get('id');need(c.get('core')==(ident in core),'core flag mismatch '+str(ident))
    need(c.get('route') in ('java_event','bridge_process'),'invalid route '+str(ident))
    need(bool(c.get('expected')) and bool(c.get('before')) and bool(c.get('after')),'missing trace '+str(ident))
    if ident in ('G01','G05','G13','G14'):need(c.get('route')=='java_event' and c.get('completed') is True,'native required '+str(ident))
    refs(c.get('raw_artifacts'),str(ident))
summary=load(EX/'summary.json');gen=EX/'generate_summary.py'
need(raw.is_file() and summary.get('raw_sha256')==sha(raw),'journey SHA mismatch')
need(gen.is_file() and summary.get('generator_sha256')==sha(gen),'generator SHA mismatch')
for k,v in [('completed',completed),('core_completed',cc),('java_event_completed',native),('safety_errors',0)]:need(type(summary.get(k)) is int and summary.get(k)==v,'summary mismatch '+k)
materials=load(EX/'source-claims.json');sources=materials.get('sources',[]);claims=materials.get('claims',[])
need(materials.get('schema_version')==1 and isinstance(sources,list) and isinstance(claims,list),'source-claims schema')
source_map={s.get('id'):s for s in sources};need(len(source_map)==len(sources),'duplicate source id')
for s in sources:
    need(all(k in s for k in ('id','type','source_group','url','published_on','captured_on','locator','limitations')),'incomplete source '+str(s.get('id')))
    refs(s.get('raw_artifacts'),'source '+str(s.get('id')))
supported=[c for c in claims if c.get('evidence_status')=='supported'];used=set()
for c in supported:
    need(all(k in c for k in ('id','text','source_ids','conditions','exceptions','counter_evidence')),'incomplete cognition claim '+str(c.get('id')))
    need(bool(c.get('source_ids')) and set(c.get('source_ids',[]))<=set(source_map),'unsupported source links')
    used.update(c.get('source_ids',[]));refs(c.get('raw_artifacts'),'claim '+str(c.get('id')))
groups={source_map[i].get('source_group') for i in used if i in source_map}
types={source_map[i].get('type') for i in used if i in source_map}
technical={'standard','standard_register','technical_reference','manufacturer','manufacturer_document','official_exact_model_document','official_technical_document'}
professional={'professional_review','independent_test','independent_laboratory','independent_comparison_method','consumer_comparison','regional_comparison','independent_consumer_test_method'}
need(len(supported)>=3 and len(groups-{None,''})>=2,'real cognition minimum not mechanically documented')
need(bool(types&technical) and bool(types&professional),'need technical/original and independent professional method/test roles')
pairs=load(EX/'comparisons.json').get('pairs',[]);need(len(pairs)>=6,'need at least six fair paired tasks')
need(len({p.get('id') for p in pairs})==len(pairs),'duplicate comparison id')
outcomes=[]
for pair in pairs:
    basis=pair.get('basis',{});need(all(bool(basis.get(k)) for k in ('initial_request_sha256','source_set_sha256','user_profile_sha256','as_of')),'missing common basis')
    need(pair.get('outcome') in ('improved','equal','regressed','inconclusive'),'invalid outcome');outcomes.append(pair.get('outcome'))
    refs(pair.get('reference_artifacts'),'paired reference '+str(pair.get('id')))
    for arm in ('a','b'):
        row=pair.get(arm,{});need(row.get('basis')==basis and bool(row.get('output')),'unfair/incomplete arm '+str(pair.get('id'))+arm);refs(row.get('raw_artifacts'),'arm '+str(pair.get('id'))+arm)
need('equal' in outcomes or 'inconclusive' in outcomes,'missing no-gain/uncertain control')
def ledger(path,kinds=None):
    starts={};ends={};need(path.is_file(),'missing ledger '+path.name)
    if not path.is_file():return starts,ends
    for n,line in enumerate(path.read_text(encoding='utf8').splitlines(),1):
        if not line.strip():continue
        try:
            r=json.loads(line);ident=r['id'];t=at(r['at'])
            if r['event']=='start':
                need(ident not in starts,'duplicate start');starts[ident]=(r,t)
                if kinds:need(r.get('kind') in kinds and bool(r.get('url')) and bool(r.get('purpose')),'bad operation start')
                else:need(bool(r.get('label')),'missing active label')
            elif r['event']==('finish' if kinds else 'end'):
                need(ident in starts and ident not in ends,'bad terminal');ends[ident]=(r,t)
                if kinds:
                    p=local(r['artifact']);need(p.is_file() and sha(p)==r['sha256'] and bool(r.get('result')),'operation terminal hash/result')
            else:errors.append('invalid event')
        except (ValueError,KeyError,TypeError,OSError) as exc:errors.append(path.name+':'+str(n)+':'+str(exc))
    need(set(starts)==set(ends),'unpaired ledger '+path.name)
    for k in starts.keys()&ends.keys():need(ends[k][1]>=starts[k][1],'negative duration')
    return starts,ends
sessions,ends=ledger(EX/'active-sessions.jsonl');intervals=sorted((v[1],ends[k][1]) for k,v in sessions.items() if k in ends)
seconds=sum((b-a).total_seconds() for a,b in intervals);need(seconds>0,'missing active work');need(all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])),'overlapping active sessions')
process=load(EX/'process.json');need(process.get('time_accounting_complete') is True and process.get('unrecorded_segments')==[],'current active accounting incomplete')
prior=process.get('consumed_predecessor_active_seconds');need(type(prior) in (int,float) and prior>=0,'missing predecessor consumption')
if type(prior) in (int,float):need(seconds+prior<=180*3600,'combined budget exceeded')
rounds=process.get('repair_rounds');need(isinstance(rounds,list) and len(rounds)<=6,'repair limit/record')
if isinstance(rounds,list):
    need(len({r.get('id') for r in rounds})==len(rounds),'duplicate repair id')
    for r in rounds:
        try:need(at(r['end'])>=at(r['start']) and bool(r['reason']),'invalid repair')
        except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
ops,terminal=ledger(EX/'operations.jsonl',{'public_read','public_query'})
reads=sum(r[0].get('kind')=='public_read' for r in ops.values());queries=sum(r[0].get('kind')=='public_query' for r in ops.values());need(reads<=32 and queries<=12,'public quota exceeded')
print(json.dumps({'errors':errors,'counts':{'completed':completed,'core_completed':cc,'java_event_completed':native,'supported_claims':len(supported),'source_groups':len(groups-{None,''}),'paired_tasks':len(pairs),'active_seconds':seconds,'reads':reads,'queries':queries},'limit':'mechanical completeness is not source truth, model gain or human comprehension'},ensure_ascii=False,indent=2));raise SystemExit(int(bool(errors)))
