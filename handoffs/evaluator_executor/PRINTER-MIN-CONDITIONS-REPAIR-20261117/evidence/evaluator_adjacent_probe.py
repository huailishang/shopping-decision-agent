"""Independent adjacent entry, answer revision, source and safety checks."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from shopping_decision.web import evaluate_input
from shopping_decision.chat_bridge import render_chat, submit_message
from shopping_decision.dialogue_flow import new_dialogue

TASK=ROOT/'handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117'
PARENT=ROOT/'handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117'
BASE=json.loads((PARENT/'cases.json').read_text(encoding='utf-8'))['cases'][0]['input']
OUT=TASK/'evidence/evaluator_adjacent'
OUT.mkdir(exist_ok=True)
rows=[]

def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def safe(v):
    return (all(v.get(k) is False for k in ['purchase_recommendation_approved','transactions_enabled',
        'live_price_verified','wechat_reuse_verified','long_term_reliability_verified','real_user_effect_verified'])
        and v['feedback']['actual_response_count']==0)

def entries(ident,changes,expected,pack='setup_two',wechat=None):
    wire=deepcopy(BASE);wire['answers'].update(changes);wire['research_context']['evidence_pack_id']=pack
    p=subprocess.run([sys.executable,'-X','utf8','-m','shopping_decision.dialogue_flow','--real-printer-case'],
        cwd=ROOT,input=(json.dumps(wire,ensure_ascii=False)+'\n').encode('utf-8'),capture_output=True,timeout=60)
    (OUT/(ident+'.stdout.jsonl')).write_bytes(p.stdout)
    (OUT/(ident+'.stderr.log')).write_bytes(p.stderr)
    save(ident+'.input.json',wire)
    assert p.returncode==0,p.stderr.decode('utf-8')
    cli=json.loads(p.stdout.decode('utf-8').splitlines()[-1])['research_case']
    web=evaluate_input({**wire['answers'],'description':'普通家用黑白打印','confirmed':True,
        'research_context':wire['research_context']})
    save(ident+'.web.json',web);view=web['research_case']
    passed=(cli['candidate_assessments']==view['candidate_assessments']
        and cli['condition_conflicts']==view['condition_conflicts']
        and all(x['research_status']==expected for x in cli['candidate_assessments'])
        and safe(cli) and safe(view) and cli['source_registry']==view['source_registry'])
    if wechat is not None:passed &= cli['wechat_requirement_status']==wechat
    rows.append({'id':ident,'passed':bool(passed),'cli_states':[x['research_status'] for x in cli['candidate_assessments']],
        'web_states':[x['research_status'] for x in view['candidate_assessments']],
        'conflicts':cli['condition_conflicts'],'expected':expected})

for ident,changes,expected,pack,wx in [
    ('raw_wifi_alias',{'requirements':['务必支持Wi-Fi打印']},'pending_evidence','setup_two',None),
    ('compound_hard',{'requirements':['必须扫描并且必须自动双面打印']},'pending_evidence','setup_two',None),
    ('unresolved_conflict',{'requires_scan':False,'requirements':['必须扫描且必须A3打印']},'pending_evidence','setup_two',None),
    ('false_flags',{'requires_scan':False,'requires_wireless':False,'requires_auto_duplex':False},'keep_for_research','setup_two',None),
    ('true_after_conflict',{'requires_scan':True,'requirements':['必须扫描']},'pending_evidence','setup_two',None),
    ('known_wechat_unselected',{'wechat_required':True,'wechat_workflow':'miniprogram'},'pending_evidence','setup_empty','required'),
    ('explicit_wechat_conflict',{'wechat_required':False,'requirements':['必须微信打印'],'wechat_workflow':'transfer_to_app'},'pending_evidence','setup_two','required'),
    ('mini_vs_transfer',{'requirements':['必须微信小程序直接打印'],'wechat_workflow':'transfer_to_app'},'pending_evidence','setup_two','required'),
    ('wechat_optional',{'wechat_required':False,'requirements':['希望微信打印']},'keep_for_research','setup_two','optional'),
    ('color_conflict',{'needs_color':False,'requirements':['必须彩印']},'pending_evidence','setup_two',None),
    ('empty_unsupported',{'requirements':['必须A3打印']},'pending_evidence','setup_empty',None),
    ('setup_refused_with_hard',{'accepts_initial_setup':False,'requires_scan':True},'pending_evidence','setup_two',None),
]:entries(ident,changes,expected,pack,wx)

state=new_dialogue()
for k,v in [('category','打印机'),('usage','必须扫描'),('needs_color','否'),('accepts_outsourced_color','是'),
    ('accepts_initial_setup','接受'),('device_deployment_region','中国大陆河南省'),
    ('budget_max_cny','1000'),('monthly_pages_range','0-50'),('requires_scan','否')]:
    state=submit_message(state,k,v)
state['research_context']=deepcopy(BASE['research_context'])
before=render_chat(state);state=submit_message(state,'requires_scan','是');corrected=render_chat(state)
state=submit_message(state,'usage','普通家用黑白打印');state=submit_message(state,'requires_scan','暂不确定');cleared=render_chat(state)
save('chat_revision.json',{'before':before,'corrected':corrected,'cleared':cleared})
v=[json.loads(c['report_json'])['research_result']['research_case'] for c in [before,corrected,cleared]]
rows.append({'id':'chat_false_true_clear','passed':bool(v[0]['condition_conflicts']) and not v[1]['condition_conflicts']
    and not v[2]['condition_conflicts'] and all(x['research_status']=='pending_evidence' for x in v[1]['candidate_assessments'])
    and all(x['research_status']=='keep_for_research' for x in v[2]['candidate_assessments']) and all(safe(x) for x in v)})

# Confirm absence of a new automatic action while preserving current known answers.
optional=evaluate_input({**BASE['answers'],'description':'普通家用黑白打印','confirmed':True,
    'wechat_required':False,'research_context':BASE['research_context']})['research_case']
save('optional_next_action.json',{'status':optional['wechat_requirement_status'],
    'next_actions':optional['next_actions'],'prepared_feedback':optional['feedback']['questions_prepared_not_sent']})
notes=[]
if any('确认微信打印是否必须' in x['exact_item'] for x in optional['next_actions']):
    notes.append({'priority':'P3','finding':'explicit optional WeChat answer is preserved in status but next action wording asks it again; inherited non-blocking wording issue'})

result={'basis':'independent offline adjacent checks, not user-effect evaluation','total':len(rows),
    'passed':sum(x['passed'] for x in rows),'checks':rows,'nonblocking_notes':notes}
save('summary.json',result)
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(0 if result['passed']==result['total'] else 1)
