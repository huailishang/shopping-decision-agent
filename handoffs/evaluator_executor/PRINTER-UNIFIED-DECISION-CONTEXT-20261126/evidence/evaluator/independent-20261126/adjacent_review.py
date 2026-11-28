"""Unseen business and malformed-response probes; no product edits or API calls."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sys
from unittest.mock import patch

OUT=Path(__file__).resolve().parent
TASK=OUT.parents[2]
ROOT=TASK.parents[2]
sys.path.insert(0,str(ROOT))
from shopping_decision import cognition_comparison as cog
from shopping_decision.chat_bridge import new_dialogue,submit_message,render_chat
from shopping_decision.claim_gate import publish_checked_comparison
from shopping_decision.context_builder import build_context
from shopping_decision.action_ranking import rank_actions
from shopping_decision.model_adapter import ModelRoute,normalize

def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def view_record(view):
    audit=json.loads(view['report_json'])
    cog_result=audit.get('cognition_comparison')
    public=cog_result['public'] if cog_result else audit.get('public_decision')
    return dict(prompt=view['prompt'],prompt_field=view['prompt_field'],text=view['result_text'],
        actions=public['next_actions'] if public else None,
        candidate_states=public['assessments'] if public else None,
        decision=cog_result.get('decision') if cog_result else None,
        flags={k:audit[k] for k in ('transactions_enabled','purchase_recommendation_approved','live_price_verified')})

s=new_dialogue()
for f,a in (('category','打印机'),('usage','低频家庭打印'),('needs_color','否'),
    ('accepts_outsourced_color','是'),('monthly_pages_range','0-50'),('budget_max_cny','1000'),
    ('device_deployment_region','中国大陆河南省'),('wechat_required','必须'),
    ('wechat_workflow','小程序'),('accepts_initial_setup','接受')):
    s=submit_message(s,f,a)
cross={}
for name,state in (
    ('scan_unanswered',deepcopy(s)),
    ('scan_deferred',submit_message(deepcopy(s),'requires_scan','暂不确定')),
    ('scan_and_duplex_not_needed',submit_message(submit_message(deepcopy(s),'requires_scan','否'),'requires_auto_duplex','否')),
):
    normal=render_chat(deepcopy(state))
    audit=json.loads(normal['report_json'])
    b=deepcopy(audit['cognition_comparison']['bundle'])
    with patch('shopping_decision.chat_bridge._analysis',return_value={
            'recommendation':{'status':'research'},'verified_research_bundle':b}):
        backend=render_chat(deepcopy(state))
    cross[name]=dict(default=view_record(normal),backend=view_record(backend),
        same_first_action=view_record(normal)['actions'][:1]==view_record(backend)['actions'][:1])
write('cross-entry-unanswered.json',cross)

pack=cog.load_pack()
interventions={}
for name,withdraw,duplex,setup in (
    ('withdraw_brother_color_no_scan_duplex_hard','brother-mono',True,True),
    ('withdraw_maintenance_refuse_setup','hp-replace-on-quality',False,False),
):
    state=deepcopy(s)
    for f,v in (('requires_scan',False),('requires_auto_duplex',duplex),('accepts_initial_setup',setup)):
        state=submit_message(state,f,'是' if v else '否') if f!='accepts_initial_setup' else submit_message(state,f,'接受' if v else '不接受')
    if name.startswith('withdraw_brother'):
        state=submit_message(state,'needs_color','是')
    p=deepcopy(pack)
    p['facts']=[f for f in p['facts'] if f['id']!=withdraw]
    with patch.object(cog,'load_pack',return_value=p):
        view=render_chat(state)
    interventions[name]=view_record(view)
write('normal-adjacent-interventions.json',interventions)

old=ROOT/'handoffs/evaluator_executor/PRINTER-CANDIDATE-TRADEOFF-20261125/evidence/executor/model/web-gpt-20261125/C08/request.json'
b=json.loads(old.read_text(encoding='utf8'))
for source in b['sources']:
    source.pop('observed_at',None)
public=publish_checked_comparison(b)
route=ModelRoute('fixture','mock','responses',32000,2048,'independent_fixture',fixture=True)
plan=build_context(public,route,input_cap=20000)
write('source-time-withdrawal.json',dict(states=[(a['candidate_id'],a['research_status']) for a in public['assessments']],
    plan_mode=plan['mode'],plan_eligibility=plan.get('packet',{}).get('required',{}).get('candidate_eligibility')))

malformed='['*1500+'0'+']'*1500
probes={}
for name,raw in (
    ('deep_json',malformed),
    ('responses_tool_payload',json.dumps({'model':'mock','status':'completed','output':[{
        'type':'message','role':'assistant','tool_calls':[{'id':'unrequested'}],
        'content':[{'type':'output_text','text':'{}'}]}]})),
    ('missing_identity',json.dumps({'status':'completed','output':[{'type':'message','role':'assistant',
        'content':[{'type':'output_text','text':'{}'}]}]})),
):
    try:
        normalized=normalize(route,http_status=200,raw=raw)
        probes[name]={'returned':normalized}
    except Exception as exc:
        probes[name]={'uncaught_exception':type(exc).__name__}
try:
    ordered,audit=rank_actions(public,route,lambda payload:{'http_status':200,'raw':malformed},input_cap=20000)
    probes['ranking_deep_json']={'returned':True,'fallback_equal':ordered==public['next_actions'],'audit':audit}
except Exception as exc:
    probes['ranking_deep_json']={'uncaught_exception':type(exc).__name__}
write('adapter-adjacent.json',probes)

# Scenario comparability: same function currently accepts unlike print volume.
base=dict(hardware=500,starter=0,toner_yield=1500,toner_price=100,separate_drum=False,maintenance=0)
a=cog.lifecycle_cost(pages=0,**base)
c=cog.lifecycle_cost(pages=1800,**base)
write('cost-comparability.json',dict(a_pages=0,b_pages=1800,a=a,b=c,
    compare_result=cog.compare_lifecycle_costs(a,c),
    note='Unlike workload; result should be incomparable rather than a product preference.'))

paired=json.loads((TASK/'evidence/executor/paired-replay.json').read_text(encoding='utf8'))
summary=json.loads((TASK/'evidence/executor/paired-summary.json').read_text(encoding='utf8'))
write('paired-artifact-shape.json',dict(raw_keys=list(paired),summary_keys=list(summary),
    summary_case_count=summary.get('case_count'),raw_case_count=paired.get('case_count'),
    note='Review final raw cases against summary instead of counting simulated sorting as model gain.'))
print(json.dumps(dict(cross_entry={k:v['same_first_action'] for k,v in cross.items()},
    adapter={k:v.get('uncaught_exception',v.get('returned',{}).get('status') if isinstance(v.get('returned'),dict) else v.get('returned')) for k,v in probes.items()},
    unlike_scenarios=cog.compare_lifecycle_costs(a,c)),ensure_ascii=False))
