"""Frozen independent session/comparability/receipt acceptance probes."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from unittest.mock import patch

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
sys.path.insert(0,str(ROOT))
from shopping_decision import cognition_comparison as cog
from shopping_decision.chat_bridge import new_dialogue,submit_message,render_chat
from shopping_decision.model_adapter import ModelRoute,normalize

def inspect(view):
    audit=json.loads(view['report_json'])
    cognition=audit.get('cognition_comparison')
    public=cognition['public'] if cognition else audit.get('public_decision')
    actions=public['next_actions'] if public else []
    first=actions[0] if actions else None
    first_key=None
    if first:
        claim=next((c for c in public['claims'] if c['candidate_id']==first.get('candidate_id')
                    and c['requirement_id']==first.get('requirement_id')),None)
        dimension=claim['dimension'] if claim else first.get('field',first.get('requirement_id'))
        first_key={'kind':first['kind'],'dimension':dimension,
                   'candidate_id':None if first['kind']=='clarify' else first.get('candidate_id')}
    return dict(prompt=view['prompt'],prompt_field=view['prompt_field'],text=view['result_text'],
        first=first,first_key=first_key,states=[(a['candidate_id'],a['research_status']) for a in public['assessments']] if public else [],
        flags={k:audit[k] for k in ('purchase_recommendation_approved','transactions_enabled','live_price_verified')})

def main():
    checks={}
    cases={}
    state=new_dialogue()
    for f,a in (('category','打印机'),('usage','低频家庭打印'),('needs_color','否'),
        ('accepts_outsourced_color','是'),('monthly_pages_range','0-50'),('budget_max_cny','1000'),
        ('device_deployment_region','中国大陆河南省'),('wechat_required','必须'),
        ('wechat_workflow','小程序'),('accepts_initial_setup','接受')):
        state=submit_message(state,f,a)
    for name,s in (
        ('unanswered',deepcopy(state)),
        ('scan_deferred',submit_message(deepcopy(state),'requires_scan','暂不确定')),
        ('not_needed',submit_message(submit_message(deepcopy(state),'requires_scan','否'),'requires_auto_duplex','否')),
    ):
        normal=render_chat(deepcopy(s))
        audit=json.loads(normal['report_json'])
        cognition=audit.get('cognition_comparison')
        checks[name+':normal_comparison_present']=isinstance(cognition,dict)
        if not cognition:
            continue
        bundle=deepcopy(cognition['bundle'])
        with patch('shopping_decision.chat_bridge._analysis',return_value={
                'recommendation':{'status':'research'},'verified_research_bundle':bundle}):
            backend=render_chat(deepcopy(s))
        a,b=inspect(normal),inspect(backend)
        checks[name+':same_first_action']=a['first_key']==b['first_key']
        checks[name+':same_candidate_states']=a['states']==b['states']
        checks[name+':no_authorization_upgrade']=all(x is False for row in (a,b) for x in row['flags'].values())
        if name=='scan_deferred':
            checks[name+':no_repeated_scan_question']=all(row['prompt_field']!='requires_scan' for row in (a,b))
        cases[name]={'default':a,'backend':b}

    params=dict(hardware=500,starter=0,toner_yield=1500,toner_price=100,separate_drum=False,maintenance=0)
    a=cog.lifecycle_cost(pages=0,**params)
    b=cog.lifecycle_cost(pages=1800,**params)
    try:
        unlike=cog.compare_lifecycle_costs(a,b)
        checks['cost:unlike_workload_cannot_choose']=unlike not in ('a','b','tie')
    except (ValueError,TypeError) as exc:
        unlike={'rejected':type(exc).__name__}
        checks['cost:unlike_workload_cannot_choose']=True
    c=cog.lifecycle_cost(pages=1800,**dict(params,hardware=550))
    checks['cost:like_workload_still_compares']=cog.compare_lifecycle_costs(b,c)=='a'
    cases['cost']={'zero_pages':a,'eighteen_hundred_pages':b,'unlike_result':unlike,'like_result':cog.compare_lifecycle_costs(b,c)}

    route=ModelRoute('fixture','mock','responses',32000,2048,'frozen_evaluator_fixture',fixture=True)
    receipt_cases={}
    for name,extra in (('tool_calls',{'tool_calls':[{'id':'unrequested'}]}),
                       ('function_call',{'function_call':{'name':'not_requested','arguments':'{}'}}),
                       ('pure_text',{})):
        body={'model':'mock','status':'completed','output':[{'type':'message','role':'assistant',
              'content':[{'type':'output_text','text':'{}'}],**extra}]}
        result=normalize(route,http_status=200,raw=json.dumps(body))
        checks['receipt:'+name]=result['status']=='complete' if name=='pure_text' else result['status'] not in ('complete','identity_unknown')
        receipt_cases[name]=result
    cases['receipts']=receipt_cases
    failures=[key for key,value in checks.items() if not value]
    print(json.dumps({'purpose':'冻结相邻业务反例；通过仍须独立人审',
        'checks':checks,'failed_checks':failures,'cases':cases},ensure_ascii=False,indent=2))
    return int(bool(failures))

if __name__=='__main__':
    raise SystemExit(main())
