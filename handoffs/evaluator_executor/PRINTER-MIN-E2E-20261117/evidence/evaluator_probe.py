"""Independent offline counterexamples; preserve normal CLI/chat/web output."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from shopping_decision.chat_bridge import render_chat, submit_message
from shopping_decision.dialogue_flow import new_dialogue
from shopping_decision.web import evaluate_input

TASK = ROOT / 'handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117'
OUT = TASK / 'evidence/evaluator_counterexamples'
OUT.mkdir(exist_ok=True)
BASE = json.loads((TASK / 'cases.json').read_text(encoding='utf-8'))['cases'][0]['input']

def save(name, data):
    p = OUT / name
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

def cli(name, changes):
    inp = deepcopy(BASE)
    inp['answers'].update(changes)
    p = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'shopping_decision.dialogue_flow', '--real-printer-case'],
        cwd=ROOT, input=(json.dumps(inp, ensure_ascii=False)+'\n').encode('utf-8'), capture_output=True, timeout=60)
    (OUT / (name+'.stdout.jsonl')).write_bytes(p.stdout)
    (OUT / (name+'.stderr.log')).write_bytes(p.stderr)
    save(name+'.input.json', inp)
    assert p.returncode == 0, p.stderr.decode('utf-8')
    return json.loads(p.stdout.decode('utf-8').splitlines()[-1])

def chat(usage, extra):
    state = new_dialogue()
    for k, v in [('category','打印机'),('usage',usage),('needs_color','否'),
                 ('accepts_outsourced_color','是'),('accepts_initial_setup','接受'),
                 ('device_deployment_region','中国大陆河南省'),('monthly_pages_range','0-50'),
                 ('budget_max_cny','1000'), *extra]:
        state = submit_message(state,k,v)
    state['research_context'] = deepcopy(BASE['research_context'])
    return render_chat(state)

records=[]
for key, raw in [('requires_scan','必须扫描'),('requires_auto_duplex','必须自动双面打印'),
                 ('requires_wireless','必须无线打印')]:
    r = cli(key+'_conflict', {key:False, 'requirements':[raw]})
    view=r['research_case']
    records.append({'id':key+'_conflict','expected':'selected research must preserve the normal path condition conflict',
        'observed_normal_status':r['comparison']['status'], 'observed_normal_conflicts':r['comparison'].get('conflicts'),
        'observed_selected_conflicts':view['condition_conflicts'],
        'observed_candidate_states':[x['research_status'] for x in view['candidate_assessments']],
        'meets_expectation':bool(view['condition_conflicts'])})

r=cli('wireless_true',{'requires_wireless':True})
web=evaluate_input({**BASE['answers'],'description':BASE['answers']['usage'],'confirmed':True,
                   'requires_wireless':True,'research_context':BASE['research_context']})
save('wireless_true.web.json',web)
records.append({'id':'wireless_entry_parity','expected':'CLI and web selected research must preserve the same explicit wireless requirement',
    'normal_web_required':web['normalized_constraints']['product_conditions']['required'],
    'cli_states':[x['research_status'] for x in r['research_case']['candidate_assessments']],
    'web_states':[x['research_status'] for x in web['research_case']['candidate_assessments']],
    'meets_expectation':r['research_case']['candidate_assessments']==web['research_case']['candidate_assessments']})

for ident,usage,extra in [('chat_scan_conflict','必须扫描',[('requires_scan','否')]),
                         ('chat_duplex_conflict','必须自动双面打印',[('requires_auto_duplex','否')]),
                         ('chat_wechat_raw','必须微信打印',[('wechat_workflow','转App')]),
                         ('chat_unresolved_hard','必须A3打印',[])]:
    c=chat(usage,extra); save(ident+'.chat.json',c)
    analysis=json.loads(c['report_json'])['research_result']; view=analysis['research_case']
    normal=analysis['normalized_constraints']['product_conditions']
    records.append({'id':ident,'normal_required':normal['required'],'normal_conflicts':normal['conflicts'],
        'selected_conflicts':view['condition_conflicts'],'selected_wechat_status':view['wechat_requirement_status'],
        'candidate_states':[x['research_status'] for x in view['candidate_assessments']],
        'visible_text':c['result_text'],
        'meets_expectation': bool(view['condition_conflicts']) if normal['conflicts'] else
            ('微信是否必须仍是未答目标' not in c['result_text']) if ident=='chat_wechat_raw' else
            ('A3' in c['result_text'])})

for ident,changes in [('setup_refused',{'accepts_initial_setup':False}),
                      ('wechat_conflict',{'wechat_required':False,'requirements':['必须微信小程序直接打印']}),
                      ('foreign_scope',{'device_deployment_region':'新加坡'})]:
    r=cli(ident,changes); view=r['research_case']
    records.append({'id':ident,'meets_expectation':all(x['research_status']=='pending_evidence' for x in view['candidate_assessments'])})

result={'task_id':'PRINTER-MIN-E2E-20261117','basis':'independent offline normal-entry counterexamples; not recommendation accuracy',
        'checks':records,'passed':sum(x['meets_expectation'] for x in records),'total':len(records)}
save('summary.json',result)
print(json.dumps({'passed':result['passed'],'total':result['total'],
                  'checks':[{k:v for k,v in x.items() if k!='visible_text'} for x in records]},ensure_ascii=False))
