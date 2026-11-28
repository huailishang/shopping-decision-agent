"""Independent cross-entry and pilot interventions; no model/API calls."""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
sys.path.insert(0, str(ROOT))
PILOT = ROOT / 'handoffs/context-model-pilot-20261126'
sys.path.insert(0, str(PILOT))
from runtime_contract import ModelRoute, normalize, request_payload
from shopping_projection import plan
from shopping_decision import cognition_comparison as cog
from shopping_decision.chat_bridge import new_dialogue, submit_message, render_chat, confirmed_values
from shopping_decision.claim_gate import publish_checked_comparison
from shopping_decision.evidence_comparison import digest, validate_model_result

TASK = OUT.parents[1]
MODEL = TASK / 'evidence/executor/model'
route = ModelRoute('fixture', 'mock', 'responses', 16000, 2048)

def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

manual = []
for case in ('C01','C08','C12','C08_SHORT'):
    folder = MODEL / 'web-gpt-20261125' / case
    b = json.loads((folder / 'request.json').read_text(encoding='utf8'))
    response = json.loads((folder / 'response.json').read_text(encoding='utf8'))
    meta = json.loads((folder / 'meta.json').read_text(encoding='utf8'))
    validated = validate_model_result(b, response)
    rule = publish_checked_comparison(b)
    model = publish_checked_comparison(b, response, origin='model')
    normalized = dict(model, origin='rule')
    excluded = {a['candidate_id'] for a in rule['assessments'] if a['research_status']=='excluded_for_research'}
    manual.append(dict(case=case, input_hash_matches=digest(b)==meta['input_sha256'],
        prompt_hash_matches=sha256((folder/'prompt.txt').read_bytes()).hexdigest()==meta['prompt_sha256'],
        response_hash_matches=sha256((folder/'response.json').read_bytes()).hexdigest()==meta['response_sha256'],
        validated=True, public_equal_except_origin=rule==normalized,
        saved_rule_equal=rule==json.loads((folder/'rule-public.json').read_text(encoding='utf8')),
        excluded=sorted(excluded), first_action=rule['next_actions'][:1],
        excluded_candidate_actions=[a for a in rule['next_actions'] if a['candidate_id'] in excluded]))
write('manual-revalidation.json',manual)

state = new_dialogue()
for f,a in (('category','打印机'),('usage','低频家庭打印'),('needs_color','否'),
    ('accepts_outsourced_color','是'),('monthly_pages_range','0-50'),('budget_max_cny','1000'),
    ('device_deployment_region','中国大陆河南省'),('wechat_required','必须'),
    ('wechat_workflow','小程序'),('accepts_initial_setup','接受'),
    ('requires_scan','否'),('requires_auto_duplex','否')):
    state=submit_message(state,f,a)
pack=cog.load_pack()
cases={}
for name,color,withdraw,scan,duplex in (
    ('original',False,None,False,False),
    ('both_excluded',True,None,True,False),
    ('withdraw_hp_color',True,'hp-mono',True,False),
    ('withdraw_brother_color_duplex',True,'brother-mono',False,True),
    ('withdraw_brother_toner',False,'brother-tn118-yield',False,False),
):
    s=deepcopy(state)
    for f,v in (('needs_color',color),('requires_scan',scan),('requires_auto_duplex',duplex)):
        s=submit_message(s,f,'是' if v else '否')
    p=deepcopy(pack)
    if withdraw:
        p['facts']=[f for f in p['facts'] if f['id']!=withdraw]
    with patch.object(cog,'load_pack',return_value=p):
        view=render_chat(s)
    audit=json.loads(view['report_json'])
    result=audit['cognition_comparison']
    cases[name]=dict(prompt=view['prompt'],prompt_field=view['prompt_field'],text=view['result_text'],
        cognition_decision=result['decision'],cognition_public=result['public'],
        other_public_decision=audit['public_decision'],
        flags={k:audit[k] for k in ('transactions_enabled','live_price_verified','purchase_recommendation_approved')})
write('normal-entry-interventions.json',cases)

# Supply the exact same admitted bundle through the backend entry.
base=json.loads((MODEL/'web-gpt-20261125/C08/request.json').read_text(encoding='utf8'))
s=deepcopy(state)
s=submit_message(s,'needs_color','是')
s=submit_message(s,'requires_scan','是')
values=confirmed_values(s)
b=deepcopy(base)
b.update(dialogue_version=s['version'],confirmed_values_sha256=digest(values),as_of=date.today().isoformat())
with patch('shopping_decision.chat_bridge._analysis',return_value={
    'recommendation':{'status':'research'},'verified_research_bundle':b}):
    view=render_chat(s)
audit=json.loads(view['report_json'])
write('backend-entry.json',dict(prompt=view['prompt'],prompt_field=view['prompt_field'],
    text=view['result_text'],public=audit['public_decision'],cognition=audit['cognition_comparison']))

# New adjacent pilot probe: structural source metadata must not bypass the publication gate.
invalid=deepcopy(base)
for source in invalid['sources']:
    source.pop('observed_at',None)
pub=publish_checked_comparison(invalid)
planned=plan(invalid,route)
write('pilot-source-bypass.json',dict(intervention='remove observed_at from every source; other inputs unchanged',
    publication_states=[(a['candidate_id'],a['research_status']) for a in pub['assessments']],
    pilot_mode=planned['mode'],pilot_reason=planned.get('reason'),
    pilot_states=[(a['candidate_id'],a['research_status']) for a in planned['gold']['assessments']],
    action_candidates=planned['actions']))

partial=normalize(route,200,{'status':'completed','output':[{'type':'message','content':[
    {'type':'output_text','text':'{}'}]}]})
zero=normalize(route,200,{'model':'mock','status':'completed','output':[{'type':'message','role':'user','content':[
    {'type':'output_text','text':'{}'}]}]})
write('pilot-adapter-adjacent.json',dict(missing_model=partial,non_assistant_message=zero))

# Strict historical scope remains untouched; diagnose membership without rewriting it.
baseline=json.loads((TASK/'BASELINE.json').read_text(encoding='utf8'))
changes=[]
for path,expected in baseline['protected_files_sha256'].items():
    p=ROOT/path
    actual=sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    if actual!=expected:
        changes.append(path)
products={p:sha256((ROOT/p).read_bytes()).hexdigest() if (ROOT/p).is_file() else None
          for p in baseline['product_sha256']}
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
write('scope-diagnostic.json',dict(old_manifest_hash=sha256((TASK/'BASELINE.json').read_bytes()).hexdigest(),
    expected_head=baseline['baseline_head'],actual_head=head,protected_count=len(baseline['protected_files_sha256']),
    changed_original_protected_paths=changes,current_product_sha256=products,
    staged_paths=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT).decode().splitlines()))

raw=[]
for label in ('C01','C08','C12','C12-r1'):
    meta=json.loads((MODEL/('modelscope-'+label)/'meta.json').read_text(encoding='utf8'))
    path=ROOT/'data/private/modelscope'/('tradeoff-20261125-response-'+label+'.json')
    payload=path.read_bytes()
    row=dict(case=label,hash_matches=sha256(payload).hexdigest()==meta['response_sha256'],bytes=len(payload),
             recorded_failure=meta.get('failure'))
    try:
        body=json.loads(payload)
        row.update(parseable_json=True,provider_status=body.get('status'),
            output_item_types=[x.get('type') for x in body.get('output',[]) if isinstance(x,dict)])
    except (ValueError,UnicodeError):
        row['parseable_json']=False
    raw.append(row)
write('raw-response-audit.json',raw)
print(json.dumps(dict(manual_cases=len(manual),normal_cases=len(cases),source_bypass=planned['mode'],
    raw_hashes=[r['hash_matches'] for r in raw],changed_protected=changes),ensure_ascii=False))
