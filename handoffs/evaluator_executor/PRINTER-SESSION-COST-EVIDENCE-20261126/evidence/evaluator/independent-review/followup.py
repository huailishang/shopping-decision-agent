import sys,json,traceback
from pathlib import Path
from copy import deepcopy
P=Path(__file__).parent;ROOT=P.parents[5];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_session_decision_contract import family,answer,render_chat,audit,backend,public
from test_cost_scenario_binding import scenario,relaxed
from test_printer_decision_journey import hard_met_bundle
rows=[]
s=answer(answer(answer(answer(family(),'wechat_required','偏好'),'needs_color','是'),'needs_color','撤回'),'requires_scan','暂不确定')
v=render_chat(s)
rows.append({'id':'withdrawal_no_public_is_safe_fallback','state':s,'view':v,'note':'Original probe public() helper assumed comparison existed; its TypeError was evaluator helper failure, not product crash. Product returned normally with no stale cognition.'})
for entry in ('default','backend'):
    s=relaxed();b=hard_met_bundle(s) if entry=='backend' else None
    v=backend(s,b) if b else render_chat(s);a=scenario(public(v));a['models'][sorted(a['models'])[0]]['inputs']['toner_price']='1e1000000'
    try:r={'view':backend(s,b,cost_scenario=a) if b else render_chat(s,cost_scenario=a)}
    except Exception as e:r={'exception_type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
    rows.append({'id':entry+'_finite_decimal_overflow','scenario':a,'result':r})
(P/'followup-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print([(x['id'],x.get('result',{}).get('exception_type','normal_return')) for x in rows])
