"""Generate actual paired observations. Run at repo root with PYTHONPATH=.:tests."""
import json,hashlib
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from test_session_decision_contract import *
from test_cost_scenario_binding import inputs,scenario,relaxed
from test_printer_decision_journey import hard_met_bundle
from test_model_receipt_boundaries import body,message,run,R,C
from test_evidence_snapshot_lineage import evidence
from shopping_decision.evidence_snapshot import snapshot_valid
from shopping_decision.cognition_comparison import lifecycle_cost,compare_lifecycle_costs
from test_action_ranking import state as rank_state, fake, ROUTE
from shopping_decision import cognition_comparison as cog
from datetime import date
out=Path(__file__).parent
pairs=[]
def add(name,change,kind,a,b,observed):
    pairs.append(dict(id=name,changed=change,kind=kind,before=a,after=b,observation=observed))
def view(v):
    return {'prompt':v['prompt'],'prompt_field':v['prompt_field'],'result_text':v['result_text'],'audit':audit(v)}
s=family()
for name,t in [('unanswered',s),('deferred',answer(s,'requires_scan','暂不确定')),('scan_no',answer(s,'requires_scan','否')),('both_no',answer(answer(s,'requires_scan','否'),'requires_auto_duplex','否')),('scan_required',answer(s,'requires_scan','是')),('withdrawn',answer(answer(s,'requires_scan','是'),'requires_scan','撤回')),('hard_color',answer(s,'needs_color','是')),('setup_rejection',answer(s,'accepts_initial_setup','不接受'))]:
    a,b=render_chat(deepcopy(t)),backend(t)
    add(name,'同一状态，默认 vs 合法后端','render_chat',view(a),view(b),{'same_first':first(a)==first(b),'first':first(a)})
t=answer(answer(s,'requires_scan','否'),'requires_auto_duplex','否');b=hard_met_bundle(t);p=public(backend(t,b));a=scenario(p);z=scenario(p,starter=1500)
def costpair(name,change,t,b,a,z):
    x,y=backend(t,b,cost_scenario=a),backend(t,b,cost_scenario=z)
    add(name,change,'render_chat',{'scenario':a,**view(x)},{'scenario':z,**view(y)},{'before':public(x)['cost_comparison'],'after':public(y)['cost_comparison'],'same_first':first(x)==first(y)})
costpair('cost_flip','受控硬条件均满足；仅A随箱量0→1500',t,b,a,z)
costpair('cost_incomparable','仅A打印量1800→0',t,b,a,scenario(p,pages=0))
p=public(backend(t));costpair('hard_pending','真实硬缺证；仅A随箱量变化',t,bundle(t),scenario(p),scenario(p,starter=1500))
dep=deepcopy(a);hp=next(n for n in dep['models'] if 'HP' in n);dep['models'][hp]['dependency_fact_ids']=['hp-replace-on-quality']
from shopping_decision.cost_scenario import dependency_fingerprints
dep['models'][hp]['dependency_fingerprints']={'hp-replace-on-quality':dependency_fingerprints(public(backend(t,b)),hp)['hp-replace-on-quality']}
x=backend(t,b,cost_scenario=dep);removed=deepcopy(b)
for source in removed['sources']:
    if source.get('snapshot'):source['revoked']=True
y=backend(t,removed,cost_scenario=dep)
add('maintenance_revoked','仅撤回HP维护来源','render_chat',{'scenario':dep,**view(x)},{'scenario':dep,**view(y)},{'before':public(x)['cost_comparison'],'after':public(y)['cost_comparison'],'same_confirmed':audit(x)['confirmed_fields']==audit(y)['confirmed_fields']})
t2=answer(t,'budget_max_cny','800');y=backend(t2,hard_met_bundle(t2),cost_scenario=a)
add('stale_cost','修改预算1000→800，保留旧情景','render_chat',view(backend(t,b,cost_scenario=a)),view(y),public(y)['cost_comparison'])
for route in (R,C):
    base=body(route)
    for field,value in [('tool_calls',[{'id':'x'}]),('function_call',{'name':'x'}),('refusal','no')]:
        changed=deepcopy(base);message(route,changed)[field]=value
        add(route.protocol+'_'+field,'合法文本附加'+field,'component',{'input':base,'receipt':run(route,base)},{'input':changed,'receipt':run(route,changed)},'应拒绝混合输出')
src,f=evidence();bad=deepcopy(src);bad['snapshot']['body']['excerpt']+='x'
add('snapshot_tampered','摘录变化但原哈希不变','component',{'source':src,'fact':f,'valid':snapshot_valid(src,f)},{'source':bad,'fact':f,'valid':snapshot_valid(bad,f)},'旧哈希拒绝变造')
# Actual ranking transport in each of two entry paths. Fixture deliberately removes observation times,
# ensuring two equally-ranked research actions, not a fabricated product claim.
def mix(payload):
    r=fake(payload);d=json.loads(r['raw']);d['output'][0]['tool_calls']=[{'id':'unrequested'}];return dict(r,raw=json.dumps(d))
def stale(payload):
    r=fake(payload);d=json.loads(r['raw']);a=json.loads(d['output'][0]['content'][0]['text']);a['context_id']='old';d['output'][0]['content'][0]['text']=json.dumps(a);return dict(r,raw=json.dumps(d))
rs=rank_state();pack=cog.load_pack()
for src in pack['sources']:src.pop('observed_at',None)
budget={'input_cap':25000}
with patch.object(cog,'load_pack',return_value=pack),patch('shopping_decision.chat_bridge.date') as clock:
    clock.today.return_value=date(2026,11,25)
    rb=render_chat(deepcopy(rs))
    rviews=[render_chat(deepcopy(rs),ranking_route=ROUTE,ranking_transport=transport,ranking_budget=budget) for transport in (fake,mix,stale)]
    for name,v in zip(('legal','mixed','stale'),rviews):
        add('default_rank_'+name,'规则 vs 离线'+name,'render_chat',view(rb),view(v),{'first':first(v),'accepted':audit(v)['ranking_audit']['business_accepted']})
from test_unified_decision_actions import fixture
from shopping_decision.chat_bridge import confirmed_values
from shopping_decision.evidence_comparison import digest
b=fixture('C08')
for src in b['sources']:src.pop('observed_at',None)
b.update(dialogue_version=rs['version'],confirmed_values_sha256=digest(confirmed_values(rs)),as_of=date.today().isoformat())
rb=backend(rs,b)
for name,transport in [('legal',fake),('mixed',mix),('stale',stale)]:
    v=backend(rs,b,ranking_route=ROUTE,ranking_transport=transport,ranking_budget=budget)
    add('backend_rank_'+name,'规则 vs 离线'+name,'render_chat',view(rb),view(v),{'first':first(v),'accepted':audit(v)['ranking_audit']['business_accepted']})
raw=out/'paired-observations-v1.json'
raw.write_text(json.dumps({'schema_version':1,'real_model_calls':0,'pairs':pairs},ensure_ascii=False,indent=2),encoding='utf8')
summary={'schema_version':1,'raw':raw.name,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'raw_bytes':raw.stat().st_size,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'pair_count':len(pairs),'render_chat_pairs':sum(p['kind']=='render_chat' for p in pairs),'observations':[{'id':p['id'],'observed':p['observation']} for p in pairs],'limitations':'离线合成、非盲；真实模型质量/耗时/真人收益未测。旧包摘要原件不覆盖。'}
(out/'paired-summary-v1.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print({k:v for k,v in summary.items() if k!='observations'})
