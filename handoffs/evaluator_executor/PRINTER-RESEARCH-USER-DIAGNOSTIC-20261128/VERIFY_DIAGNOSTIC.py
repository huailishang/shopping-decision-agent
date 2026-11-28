"""Draft preflight checker; no participant evidence can be manufactured."""
from DIAGNOSTIC_GUI import Arm,cards,SAFE,load_upstream
from PREP_BASELINE import HERE,OUT,inventory,git,now
import json,hashlib,sys,time,subprocess
from copy import deepcopy
TARGETS={'P1':'requires_scan','P2':'requires_auto_duplex','P3':'idle_weeks_pattern'}
def save(name,data):
    path=OUT/name
    if path.exists(): path=OUT/(path.stem+'.r2'+path.suffix)
    if path.exists(): raise ValueError('refuse overwriting evidence')
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def start(arm,usage):
    a=Arm(arm);a.act('direct');a.act('answer','打印机');a.act('answer',usage);return a
def explicit(a,field,answer):
    v=a.act('select',field);assert v['confirmed']==a.events[-1]['before']['confirmed'];return a.act('answer',answer)
def target_reached(v,target):
    if target=='idle_weeks_pattern':return v['confirmed'].get(target)=='often_long' and (v.get('usage_research') or {}).get('status')=='research_required'
    dim={'requires_scan':'scan','requires_auto_duplex':'auto_duplex'}[target]
    return v['confirmed'].get(target) is True and any(f['dimension']==dim and f['status']=='unknown' for f in v.get('facts',[])) and '核Brother' in v.get('question','')
def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def validate_record(trace,target,review):
    if trace.get('kind')!='synthetic': raise ValueError('human scoring not authorized')
    events=trace.get('events',[])
    if not events or events[-1]['action']!='exit' or any(e['action']=='exit' for e in events[:-1]):raise ValueError('missing terminal exit')
    for i,e in enumerate(events):
        if i and (events[i-1]['after']!=e['before'] or e['elapsed']<events[i-1]['elapsed']):raise ValueError('discontinuous event trail')
        if e['machine_seconds']<0 or not e['ts'] or not e['action_started']:raise ValueError('invalid time evidence')
    raw=review.get('raw')
    if not isinstance(raw,dict) or review.get('raw_sha256')!=digest(raw) or raw.get('trace_sha256')!=digest(trace) or raw.get('target')!=target:raise ValueError('unbound raw record')
    if raw.get('kind')!='synthetic' or raw.get('anonymous_id')!='SYNTHETIC' or raw.get('consent')!='not_applicable_synthetic':raise ValueError('invalid synthetic identity')
    for key in ('reason_text','condition_text','unknown_text','prompt_note','exit_reason'):
        if not isinstance(raw.get(key),str) or not raw[key].strip():raise ValueError('missing raw '+key)
    if raw.get('exit')!=events[-1]['detail'] or raw['exit_reason']!=raw['exit'].get('reason') or type(raw['exit'].get('early')) is not bool:raise ValueError('unbound or unknown exit')
    if raw.get('participant_seconds')!=trace.get('participant_seconds'):raise ValueError('unbound time')
    if review.get('early_exit')!=raw['exit']['early']:raise ValueError('exit coding mismatch')
    for key in ('reason_correct','condition_correct','unknown_correct','prompted','early_exit'):
        if type(review.get(key)) is not bool or not str(review.get('coding_reasons',{}).get(key,'')).strip():raise ValueError('missing coding rationale: '+key)
    if type(raw.get('prompted')) is not bool or raw['prompted']!=review['prompted']:raise ValueError('prompt coding mismatch')
def score(trace,target,review):
    validate_record(trace,target,review)
    events=trace['events'];end=events[-1]['after']
    safety=any(any(e[k]['safe'].values()) for e in events for k in ('before','after'))
    changes=[e for e in events if e['before']['confirmed']!=e['after']['confirmed']]
    invalid_change=any(e['action'] not in ('answer','category','withdraw','direct','receive') for e in changes)
    explicit_target=any(e['action']=='answer' and e['before']['field']==target and not e['error'] and target in e['after']['confirmed'] for e in events)
    misread=not review['unknown_correct']
    reached=explicit_target and target_reached(end,target)
    deferred=target in end.get('deferred',[]) and not reached
    complete=bool(reached and review['reason_correct'] and review['condition_correct'] and not misread and not review['prompted'] and not review['early_exit'] and not safety and not invalid_change)
    return dict(complete=complete,reached=bool(reached),deferred=deferred,misread=misread,safety=safety,invalid_change=invalid_change,prompted=review['prompted'],early_exit=review['early_exit'],steps=len(events),irrelevant_answers=review.get('irrelevant_answer_count'),non_target_answers=sum(e['action']=='answer' and e['before']['field'] not in (target,'category','usage') for e in events),found_entry=any(e['action']=='select' and e['detail']==target and not e['error'] for e in events),machine_seconds=trace['machine_seconds'],participant_seconds=trace['participant_seconds'])
def reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('expected rejection')
def arms():
    data=cards();assert len(data)==6
    allocation=json.loads((HERE/'SCENARIOS.json').read_text(encoding='utf8'))['allocation']
    assert len(allocation)==6
    from collections import Counter
    assert Counter(x for row in allocation for x in row)==Counter(f'{cid}:{arm}' for cid in data for arm in ('A','B'))
    for i,row in enumerate(allocation):
        assert len(row)==2 and row[0][:2]!=row[1][:2] and [x[-1] for x in row]==list('AB' if i%2==0 else 'BA')
    rows=[]
    for cid,target in [('P1a','requires_scan'),('P2a','requires_auto_duplex'),('P3a','idle_weeks_pattern')]:
        a,b=[start(x,data[cid]['text']) for x in ('A','B')]
        assert a.entry.view()==b.entry.view()
        reject(lambda:a.act('select',target))
        assert a.entry.view()==b.entry.view()
        if target=='idle_weeks_pattern':v=explicit(b,target,'经常连续多周不用')
        else:
            for f,x in [(target,'是'),('needs_color','否'),('device_deployment_region','河南'),('monthly_pages_range','0-50')]:v=explicit(b,f,x)
        assert target_reached(v,target) and not any(v['safe'].values())
        rows.append({'card':cid,'initial_equal':True,'A':a.trace(),'B':b.trace()})
    for arm in ('A','B'):
        a=Arm(arm);a.act('receive','device-research');assert a.entry.view()['confirmed']=={}
        a.act('answer','打印机');a.act('answer',a.entry.use_draft_goal())
        old=deepcopy(a.entry.state);a.act('receive','device-research');assert a.entry.state==old
        bad=load_upstream('device-research');bad['decision']['shopping_handoff']['pending'].append('同版冲突')
        reject(lambda:a.entry.receive(bad));assert a.entry.state==old
        a.act('withdraw');a.act('receive','device-research');assert not a.entry.view()['active']
        fresh=Arm(arm);fresh.act('receive','device-research');assert fresh.entry.view()['active']
        a.act('receive','revise-to-self-service');assert not a.entry.view()['active'];reject(lambda:a.act('receive','device-research'))
        a.act('direct');a.act('answer','打印机');a.act('answer','日常家用');a.act('category','手机')
        assert a.entry.view()['confirmed']=={'category':'phone'} and not a.entry.view()['facts']
        assert not any(a.entry.view()['safe'].values())
        rows.append({'arm':arm,'negative':a.trace(),'known_fresh_process_replay':fresh.entry.view()['active']})
    save('arms.json',rows);print('ARMS: equal initial states, 3 target journeys and both arm guards; cross-process replay remains known failure')
def scoring():
    target='requires_scan';good=start('B',cards()['P1a']['text'])
    for f,x in [(target,'是'),('needs_color','否'),('device_deployment_region','河南'),('monthly_pages_range','0-50')]:explicit(good,f,x)
    miss=start('A',cards()['P1a']['text'])
    deferred=start('B',cards()['P1a']['text']);explicit(deferred,target,'暂不确定')
    early=start('B',cards()['P1a']['text'])
    for a in (good,miss,deferred,early):
        a.act('exit',dict(reason='提前停止' if a is early else '完成本次操作',stage='early' if a is early else 'finished',early=a is early))
    def record(a,reason=True,condition=True,unknown=True,prompted=False):
        trace=a.trace();exit=trace['events'][-1]['detail']
        raw=dict(kind='synthetic',anonymous_id='SYNTHETIC',consent='not_applicable_synthetic',trace_sha256=digest(trace),target=target,reason_text='需要保存纸质资料' if reason else '没有理由',condition_text='需要扫描，型号仍需核对' if condition else '不清楚条件',unknown_text='功能待核，不能据此购买' if unknown else '已经可以购买',prompt_note='主持人告诉我选扫描' if prompted else '未提示',prompted=prompted,exit=exit,exit_reason=exit['reason'],participant_seconds=None)
        r=dict(reason_correct=reason,condition_correct=condition,unknown_correct=unknown,prompted=prompted,early_exit=exit['early'],raw=raw,raw_sha256=digest(raw))
        r['coding_reasons']={k:'合成固定编码：'+str(r[k]) for k in ('reason_correct','condition_correct','unknown_correct','prompted','early_exit')}
        return trace,r
    tests=[('success',*record(good),True),('miss',*record(miss),False),('prompted',*record(good,prompted=True),False),('misread',*record(good,unknown=False),False),('deferred',*record(deferred),False),('early_exit',*record(early),False)]
    result=[]
    for name,trace,r,expected in tests:
        s=score(trace,target,r);assert s['complete']==expected
        if name=='deferred':assert s['deferred']
        result.append({'case':name,'review_codes_synthetic':r,'trace':trace,'score':s})
    trace,r=record(good)
    for name,t,q in [('missing_raw',trace,{k:v for k,v in r.items() if k!='raw'}),('missing_exit',dict(trace,events=trace['events'][:-1]),r),('mismatched_exit',trace,dict(r,early_exit=True)),('changed_raw',trace,dict(r,raw=dict(r['raw'],unknown_text='已经可以买'))),('no_coding',trace,dict(r,coding_reasons={})),('discontinuous',dict(trace,events=[trace['events'][0],*trace['events'][2:]]),r)]:
        reject(lambda:score(t,target,q));result.append({'case':name,'rejected':True})
    save('scoring.json',result);print('SCORING: 12/12 synthetic checks, including 6 incomplete record rejections; not participants')
def human():
    print('BLOCKED / INCONCLUSIVE: no separately authorized participants; zero human records');return 2
def scope():
    b=json.loads((OUT/'baseline.json').read_text(encoding='utf8'));actual=inventory()
    changed=sorted(k for k in set(actual)|set(b['files']) if actual.get(k)!=b['files'].get(k))
    head=git('rev-parse','HEAD').decode().strip();index=hashlib.sha256(git('ls-files','--stage','-z')).hexdigest()
    save('scope.json',dict(count=len(actual),changed=changed,head_same=head==b['head'],index_same=index==b['index'],historical_worktime=None,pre_baseline_prep_seconds=None))
    assert not changed and head==b['head'] and index==b['index']
    print('SCOPE',len(actual),'unchanged; initial prep wall time unknown, not certified freeze')
def main():
    if len(sys.argv)!=2:raise SystemExit('arms|scoring|human-evidence|scope-time')
    mode=sys.argv[1];return {'arms':arms,'scoring':scoring,'human-evidence':human,'scope-time':scope}[mode]()
if __name__=='__main__':raise SystemExit(main())
