"""Independent evaluator probes: inputs and complete outputs retained, no product edits."""
import sys,json,hashlib,subprocess,time
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[6]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_session_decision_contract import family,answer,public,backend,bundle,render_chat,audit,first
from test_cost_scenario_binding import scenario,inputs,relaxed
from test_printer_decision_journey import hard_met_bundle
from test_model_receipt_boundaries import body,message,run,R,C
from shopping_decision.cognition_comparison import lifecycle_cost,compare_lifecycle_costs
from shopping_decision.context_builder import build_context
from shopping_decision.cost_scenario import dependency_fingerprints
from shopping_decision.evidence_comparison import digest
OUT=Path(__file__).parent
rows=[]
def add(name,fn):
    start=datetime.now(timezone.utc).isoformat()
    try: result=fn()
    except Exception as e: result={'exception_type':type(e).__name__,'exception':str(e)}
    rows.append({'id':name,'start':start,'end':datetime.now(timezone.utc).isoformat(),'result':result})
def view(v):
    return {k:v[k] for k in ('prompt_field','prompt','choices','result_text','state_json','report_json')}
def pair(s):
    a,b=render_chat(deepcopy(s)),backend(s)
    return {'input':s,'default':view(a),'backend':view(b),'first_default':first(a),'first_backend':first(b),'same_first':first(a)==first(b)}
add('holdout_deferred_scan_duplex_required_reject_setup',lambda:pair(answer(answer(answer(family(),'requires_scan','暂不确定'),'requires_auto_duplex','是'),'accepts_initial_setup','不接受')))
def revise():
    s=answer(answer(family(),'wechat_required','偏好'),'needs_color','是')
    s=answer(answer(s,'needs_color','撤回'),'requires_scan','暂不确定')
    return pair(s)
add('holdout_color_withdrawn_scan_deferred_wechat_preference',revise)
def cost_views():
    s=answer(answer(family(),'requires_scan','否'),'requires_auto_duplex','否');b=hard_met_bundle(s)
    p=public(backend(s,b));a=scenario(p);z=scenario(p,starter=1500)
    return {'state':s,'bundle':b,'scenario_before':a,'scenario_after':z,'before':view(backend(s,b,cost_scenario=a)),'after':view(backend(s,b,cost_scenario=z))}
add('hard_met_cost_flip_actual_chat',cost_views)
def independent_cost():
    base=lifecycle_cost(**inputs())
    cases={}
    for k,v in [('pages',0),('months',12),('currency','USD'),('fee_scope','hardware_only')]:
        try: cases[k]=compare_lifecycle_costs(base,lifecycle_cost(**inputs(**{k:v})))
        except ValueError as e:cases[k]={'rejected':str(e)}
    for pages in (0,1500,1501,3000,3001):
        cases[str(pages)]=lifecycle_cost(**inputs(pages=pages,starter=1500,separate_drum=True,drum_starter=3000,drum_yield=3000,drum_price=200))
    return cases
add('math_and_basis_independent',independent_cost)
def cost_failure(value):
    s=relaxed();p=public(render_chat(s));a=scenario(p)
    a['models'][sorted(a['models'])[0]]['inputs']['toner_price']=value
    return {'scenario':a,'result':view(render_chat(s,cost_scenario=a))}
add('finite_extreme_decimal_default_boundary',lambda:cost_failure('1e1000000'))
def dependency_withdrawal():
    s=relaxed();b=bundle(s);p=public(backend(s,b));a=scenario(p)
    hp=next(n for n in a['models'] if 'HP' in n);fid='hp-replace-on-quality'
    a['models'][hp].update(dependency_fact_ids=[fid],dependency_fingerprints={fid:dependency_fingerprints(p,hp)[fid]})
    old=backend(s,b,cost_scenario=a)
    src=next(x for x in b['sources'] if x.get('snapshot'));src['snapshot']['body']['version']+=' evaluator new revision';src['snapshot']['sha256']=digest(src['snapshot']['body'])
    new=backend(s,b,cost_scenario=a)
    return {'old':view(old),'new':view(new),'same_confirmed':audit(old)['confirmed_fields']==audit(new)['confirmed_fields']}
add('independent_same_id_version_cost',dependency_withdrawal)
def receipts():
    res=[]
    for route in (R,C):
        for k,v in [('tool_calls',[{'id':'x'}]),('function_call',{'name':'x'}),('refusal','no')]:
            b=body(route);message(route,b)[k]=v;res.append({'protocol':route.protocol,'key':k,'receipt':run(route,b)})
        good=body(route);message(route,good)['vendor_metadata']={'arbitrary':1}
        res.append({'protocol':route.protocol,'key':'allowed_metadata','receipt':run(route,good)})
    return res
add('protocol_negatives_and_metadata',receipts)
def hidden_reasoning_tool():
    b=body(R);b['output'].insert(0,{'type':'reasoning','content':[{'type':'function_call','name':'place_order','arguments':'{}'}]})
    return {'input':b,'receipt':run(R,b)}
add('unsupported_output_inside_reasoning',hidden_reasoning_tool)
def receipt_fallback():
    from test_action_ranking import state as rs,fake,ROUTE
    from shopping_decision import cognition_comparison as cog
    from unittest.mock import patch
    from datetime import date
    s=rs();pack=cog.load_pack()
    for x in pack['sources']:x.pop('observed_at',None)
    calls=[]
    def transport(payload):
        calls.append(1);r=fake(payload);d=json.loads(r['raw']);d['output'].insert(0,{'type':'reasoning','content':[{'type':'function_call','name':'place_order','arguments':'{}'}]});return dict(r,raw=json.dumps(d))
    with patch.object(cog,'load_pack',return_value=pack),patch('shopping_decision.chat_bridge.date') as clk:
        clk.today.return_value=date(2026,11,25)
        a=render_chat(deepcopy(s));b=render_chat(deepcopy(s),ranking_route=ROUTE,ranking_transport=transport,ranking_budget={'input_cap':25000})
    return {'before':view(a),'after':view(b),'transport_calls':len(calls),'accepted':audit(b)['ranking_audit']['business_accepted']}
add('reasoning_mixed_tool_actual_entry',receipt_fallback)
def summary_integrity():
    ex=OUT.parents[1]/'executor';summary=json.loads((ex/'paired-summary-v1.json').read_text(encoding='utf8'));raw=(ex/summary['raw']).read_bytes();pairs=json.loads(raw)['pairs']
    return {'raw_sha_match':hashlib.sha256(raw).hexdigest()==summary['raw_sha256'],'raw_bytes_match':len(raw)==summary['raw_bytes'],'generator_sha_match':hashlib.sha256((ex/'generate_pairs.py').read_bytes()).hexdigest()==summary['generator_sha256'],'pairs':len(pairs),'render_pairs':sum(p['kind']=='render_chat' for p in pairs),'no_gain':next(p['observation'] for p in pairs if p['id']=='hard_pending'),'fallback':next(p['observation'] for p in pairs if p['id']=='default_rank_mixed')}
add('summary_hashes_counts_sample',summary_integrity)
(OUT/'probe-results.json').write_text(json.dumps({'started':'see per-case times','rows':rows},ensure_ascii=False,indent=2),encoding='utf8')
for row in rows:
    r=row['result'];brief={k:v for k,v in r.items() if k in ('exception_type','exception','same_first','first_default','first_backend','accepted','raw_sha_match','raw_bytes_match','generator_sha_match','pairs','render_pairs')} if isinstance(r,dict) else ''
    print(row['id'],json.dumps(brief,ensure_ascii=False))
