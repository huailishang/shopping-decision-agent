"""Offline task gate: provenance structure, bounded collection and real normal entry.

Source meaning and action value still require independent human/agent review.
"""
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
PARENT=ROOT/'handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117'
MODELS={'HL-L1238W','M232dw'}
PACK='wechat_workflow_20261117'
TOPICS={'wechat_initiation_path','repeat_print_steps','rebind_requirements',
        'network_requirements','region_scope','account_or_service_requirements'}
PATHS={'direct_miniprogram','wechat_to_vendor_app','export_then_app'}
FALSE_FLAGS=('purchase_recommendation_approved','transactions_enabled','wechat_reuse_verified',
             'live_price_verified','long_term_reliability_verified','real_user_effect_verified')

def need(value,message):
    if not value: raise ValueError(message)

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def timestamp(s):
    d=datetime.fromisoformat(s)
    need(d.tzinfo is not None,'timezone required')
    return d

def official_url(url):
    u=urlsplit(url); host=(u.hostname or '').lower()
    return (u.scheme=='https' and not u.username and not u.password
            and any(host==d or host.endswith('.'+d) for d in ('brother.cn','brother.com','hp.com')))

def evidence_ref(ref):
    need(isinstance(ref,dict),'missing evidence reference')
    p=(ROOT/ref.get('path','')).resolve()
    need(p.is_relative_to(TASK/'evidence') and p.is_file(),'reference outside task evidence')
    need(sha(p)==ref.get('sha256'),'evidence changed: '+str(p))
    return p

def product_inventory():
    return {p.relative_to(ROOT).as_posix() for folder,pat in [('shopping_decision','*.py'),
        ('tests','*.py'),('knowledge','*.json'),('desktop','*.java'),('scripts','*.py')]
        for p in (ROOT/folder).rglob(pat)}

def frozen(expected):
    need(sha(TASK/'FROZEN_INPUTS.json')==expected,'frozen manifest changed')
    m=read(TASK/'FROZEN_INPUTS.json')
    for name,digest in m['files'].items():
        need((ROOT/name).is_file() and sha(ROOT/name)==digest,'frozen input changed: '+name)
    current=product_inventory(); original=set(m['product_inventory'])
    need(original<=current,'existing product file removed')
    need(current-original<=set(m['allowed_product_paths']),'new product outside scope')
    return m

def changed_products(m):
    return [p for p in m['allowed_product_paths']
            if ((ROOT/p).exists() and sha(ROOT/p)!=m['allowed_baseline_sha256'].get(p))
            or (not (ROOT/p).exists() and p in m['allowed_baseline_sha256'])]

def validate_claim(c,sources):
    need(c.get('model_id') in MODELS,'claim model mismatch')
    need(c.get('kind')=='manufacturer_workflow_documentation','wrong evidence type')
    need(c.get('topic') in TOPICS,'initial setup/wireless only is not new WeChat evidence')
    need(c.get('supports_only')==[c['topic']],'claim support scope changed')
    need(c.get('basis')=='official_documentation','document evidence became device result')
    need(c.get('model_binding') in {'exact_model','series_explicitly_includes_model'},'unbound series claim')
    need(c.get('market_scope')=='CN','unverified cross-region claim')
    for k in ('id','statement','counter','scope','observed_on','binding_note','new_vs_baseline_reason'):
        need(isinstance(c.get(k),str) and c[k].strip(),'missing claim field: '+k)
    ids=c.get('source_ids')
    need(isinstance(ids,list) and ids and all(s in sources for s in ids),'claim source missing')
    need(any(c['model_id'] in sources[s]['applicable_models'] for s in ids),'source not bound to model')
    if c['topic']=='wechat_initiation_path':
        need(c.get('path_type') in PATHS,'Wi-Fi/unknown is not a documented initiation path')

def collection():
    auth=read(TASK/'AUTHORIZATION.json'); ledger=TASK/'evidence/collection_ledger.jsonl'
    events=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines() if s.strip()]
    scheduled={}; terminal={}
    for e in events:
        aid=e['action_id']; need(e.get('phase') in {'executor','evaluator'},'unknown collection phase')
        if e['event']=='scheduled':
            need(aid not in scheduled,'duplicate scheduled action')
            need(e['kind'] in {'search','document_open'},'unauthorized external action')
            need(timestamp(e['at_utc'])>=timestamp(auth['recorded_at_utc']),'pre-authorization collection')
            if e['kind']=='document_open': need(official_url(e['url']),'nonofficial document URL')
            else:
                need(e.get('query') and e.get('domains'),'search has no official-domain restriction')
                need(all(official_url('https://'+d) for d in e['domains']),'unapproved search domain')
            scheduled[aid]=e
        elif e['event']=='completed':
            need(aid in scheduled and aid not in terminal,'missing/duplicate action completion')
            need(e['outcome'] in {'success','failed','access_limited','no_relevant_fact'},'invalid outcome')
            need(timestamp(e['at_utc'])>=timestamp(scheduled[aid]['at_utc']),'reversed action time')
            evidence_ref(e['receipt']); terminal[aid]=e
        else: raise ValueError('invalid collection event')
    need(scheduled and set(scheduled)==set(terminal),'no actual attempt or open collection events')
    counts={k:sum(x['kind']==k for x in scheduled.values()) for k in ('search','document_open')}
    need(counts['search']<=4 and counts['document_open']<=6,'public quota exceeded')
    need(sum(x['kind']=='document_open' and x['phase']=='executor' for x in scheduled.values())<=4,
         'executor used evaluator document reserve')
    d=read(TASK/'evidence/observations.json')
    need(d.get('task_id')==TASK.name,'wrong collection task')
    need(d.get('status') in {'material_found','insufficient','access_limited','quota_exhausted','no_material_gain'},
         'collection outcome missing')
    need(isinstance(d.get('rejected_items'),list),'missing rejected evidence reasons')
    sources=d['sources']; claims=d['claims']; need(isinstance(sources,dict) and isinstance(claims,list),'bad fact pack')
    for sid,s in sources.items():
        need(sid not in {'R7','R10'},'old source dates overwritten')
        need(official_url(s.get('url','')),'unofficial admitted source')
        for k in ('locator','validity_note','evidence_note'):
            need(isinstance(s.get(k),str) and s[k].strip(),'source attribution field missing: '+k)
        need(isinstance(s.get('applicable_models'),list) and set(s['applicable_models'])<=MODELS,
             'source model scope invalid')
        aid=s['action_id']; need(aid in terminal and terminal[aid]['outcome']=='success','source has no successful receipt')
        need(scheduled[aid]['kind']=='document_open' and scheduled[aid]['url']==s['url'],'source action mismatch')
        observed=timestamp(s['retrieved_at_utc'])
        need(timestamp(scheduled[aid]['at_utc'])<=observed<=timestamp(terminal[aid]['at_utc']), 'source date mismatch')
        need('published_on' in s,'unknown publication date must be explicit null')
    need(len({c['id'] for c in claims})==len(claims),'duplicate claim')
    for c in claims: validate_claim(c,sources)
    need(d.get('new_external_product_fact_count')==len(claims),'new fact count mismatch')
    need(bool(claims)==(d['status']=='material_found'),'material-found status mismatch')
    need(d.get('purchase_recommendation_approved') is False and d.get('transactions_enabled') is False,'unsafe fact pack')
    return d,counts

def validate_view(v,d):
    old=read(PARENT/'evidence_packs.json')['packs']['setup_two']
    need(v.get('case_id')=='PRINTER-HENAN-FAMILY-20261116' and v.get('input_basis')=='project_owner_proxy',
         'proxy input promoted to direct user/device evidence')
    need(all(v.get(k) is False for k in FALSE_FLAGS),'unverified capability or purchase enabled')
    need(v.get('wechat_requirement_status')=='required','confirmed WeChat requirement lost')
    need(v.get('new_external_fact_count')==len(d['claims']),'runtime new fact count mismatch')
    need(v.get('used_facts')==old['claims']+d['claims'],'runtime omitted/changed/unselected fact')
    need(v.get('source_registry')=={**old['sources'],**d['sources']},'source/date binding changed')
    need(v.get('flow_status')=='research_delivered_with_limits','overclaimed flow status')
    need(v.get('feedback',{}).get('status')=='not_collected' and v['feedback'].get('actual_response_count')==0,
         'missing feedback promoted to real feedback')
    rows=v.get('candidate_assessments',[])
    need(len(rows)==2 and {x['model_id'] for x in rows}==MODELS,'missing model')
    for row in rows:
        mid=row['model_id']; new=[x for x in d['claims'] if x['model_id']==mid]
        need(row.get('research_status') in {'pending_evidence','keep_for_research'},'unsupported winner/exclusion')
        need(set(row.get('supported_claim_ids',[]))=={x['id'] for x in old['claims']+new if x['model_id']==mid},
             'cross-model source borrowing')
        need({'wechat_reuse','live_price','long_term_reliability'}<=set(row.get('unknown_fields',[])),
             'documented workflow promoted to real-world verification')
        if d['claims']:
            wd=row.get('wechat_documentation',{})
            paths={x['path_type'] for x in new if x['topic']=='wechat_initiation_path'}
            need(set(wd.get('path_types',[]))==paths,'documented path claim missing or invented')
            need(wd.get('initiation_status')==('documented' if paths else 'unknown'),'initiation status unsupported')
            repeated=any(x['topic'] in {'repeat_print_steps','rebind_requirements'} for x in new)
            need(wd.get('repeat_use_status')==('documented' if repeated else 'unknown'),'initial setup became repeat use')
            need(wd.get('user_path_acceptance')=='unconfirmed','unconfirmed workflow preference answered for user')
            need(set(wd.get('claim_ids',[]))=={x['id'] for x in new},'document claim scope mismatch')
        elif not new: need(row['research_status']=='pending_evidence','empty new evidence approved required workflow')
    need(isinstance(v.get('report_text'),str) and len(v['report_text'])>=120,'readable comparison absent')
    need(v.get('next_actions') and all(a.get('exact_item') and a.get('owner_role') for a in v['next_actions']),
         'vague next action')

def run_flow(out,d):
    sys.path.insert(0,str(ROOT))
    from shopping_decision.chat_bridge import submit_message,render_chat
    from shopping_decision.dialogue_flow import new_dialogue
    out.mkdir(parents=True,exist_ok=True)
    inp=deepcopy(read(TASK/'cases.json')['input'])
    if not d['claims']: inp['research_context']['evidence_pack_id']='setup_two'
    wire=(json.dumps(inp,ensure_ascii=False)+'\n').encode('utf-8')
    p=subprocess.run([sys.executable,'-X','utf8','-m','shopping_decision.dialogue_flow','--real-printer-case'],
        cwd=ROOT,input=wire,capture_output=True,timeout=60)
    (out/'updated.input.jsonl').write_bytes(wire);(out/'updated.stdout.jsonl').write_bytes(p.stdout)
    (out/'updated.stderr.log').write_bytes(p.stderr);need(p.returncode==0,'normal CLI failed')
    view=json.loads(p.stdout.decode('utf-8').splitlines()[-1])['research_case'];validate_view(view,d)
    state=new_dialogue()
    for field,msg in [('category','打印机'),('usage',inp['answers']['usage']),('needs_color','否'),
        ('accepts_outsourced_color','是'),('accepts_initial_setup','接受'),('wechat_required','必须'),
        ('device_deployment_region','中国大陆河南省'),('monthly_pages_range','0-50'),('budget_max_cny','1000')]:
        state=submit_message(state,field,msg)
    state['research_context']=inp['research_context'];chat=render_chat(state)
    (out/'updated.chat.json').write_text(json.dumps(chat,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cv=json.loads(chat['report_json'])['research_result']['research_case'];validate_view(cv,d)
    need(cv==view and view['report_text'] in chat['result_text'],'CLI/chat divergence or hidden result')
    spec=importlib.util.spec_from_file_location('old_minimal_checker',PARENT/'check_delivery.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    legacy=mod.run_cases(out/'legacy')
    summary={'normal_entry_same':True,'new_document_fact_count':len(d['claims']),'legacy':legacy,
             'limit':'One proxy case, no real-device or user-effect test'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return summary

def delivery(d,counts):
    a=read(TASK/'evidence/assessment.json');need(a.get('effect_verdict')=='inconclusive','unmeasured user benefit')
    need(a.get('action_change') in {'observed','no_change','inconclusive'},'action effect missing')
    need(a.get('reason') and len(a.get('questions',[]))==3,'three frozen evidence-use questions not assessed')
    need(a.get('baseline_sha256')==sha(TASK/'preparation/confirmed_need.stdout.jsonl'),'baseline replaced')
    evidence_ref(a['after_output'])
    for q in a['questions']:
        need(q.get('id') in {'EQ-01','EQ-02','EQ-03'} and q.get('status') in {'correct','incomplete','incorrect','unknown'},
             'invalid question judgment')
        need(q.get('reason') and q.get('claim_ids') is not None,'missing per-question evidence judgment')
    need({q['id'] for q in a['questions']}=={'EQ-01','EQ-02','EQ-03'},'question IDs missing')
    if not d['claims']: need(a['action_change']!='observed','zero new facts claimed evidence gain')
    it=read(TASK/'evidence/iterations.json');need(1<=it['concentrated_iterations']<=2,'iteration budget exceeded')
    need(it['historical_parent_effective_hours']=='unknown','historical cost invented')
    elapsed=0;previous=None
    for s in it['segments']:
        start,end=timestamp(s['started_at']),timestamp(s['ended_at'])
        need(end>=start and (previous is None or start>=previous) and s.get('activity'),'bad/overlapping work segment')
        elapsed+=(end-start).total_seconds();previous=end
    need(it['segments'] and elapsed<=6*3600,'work-time evidence missing or budget exceeded')
    for k in ('business_api_calls','credentials_read','messages_sent','device_operations','transactions','git_commit','git_push'):
        need(it.get(k)==0,'forbidden side effect: '+k)
    for name in ('REPORT.md','RESEARCH_DELIVERY.md','evidence/breakpoints.json'):
        need((TASK/name).is_file() and (TASK/name).stat().st_size,'missing delivery: '+name)
    return {'status':'delivery_present_needs_semantic_review','recorded_wall_seconds':elapsed,'collection':counts}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',choices=['frozen','collection','flow','tests','regression','delivery'],required=True)
    p.add_argument('--frozen-sha',required=True);p.add_argument('--out',type=Path);a=p.parse_args()
    try:
        m=frozen(a.frozen_sha)
        if a.check=='frozen': result={'status':'frozen_match','protected_count':len(m['files'])}
        else:
            d,counts=collection();changes=changed_products(m)
            if not d['claims']: need(not changes,'no material gain must not cause product expansion')
            else:
                reg=ROOT/'knowledge/printer_wechat_workflow_evidence.json'
                need(reg.is_file() and sha(reg)==sha(TASK/'evidence/observations.json'),'runtime pack differs from observations')
            if a.check=='collection':result={'status':d['status'],'new_fact_count':len(d['claims']),'counts':counts}
            elif a.check=='flow':
                need(a.out is not None,'separate flow output required');out=(ROOT/a.out).resolve()
                need(out.is_relative_to(TASK/'evidence'),'flow output outside task');result=run_flow(out,d)
            elif a.check in {'tests','regression'}:
                if not changes: result={'status':'not_repeated_no_product_change','prior_full_tests':464}
                else:
                    if a.check=='tests':
                        import unittest
                        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_printer_wechat_workflow.py')
                        need(suite.countTestCases()>=8,'meaningful workflow/negative tests missing')
                        suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_minimal_research_flow.py'))
                        r=unittest.TextTestRunner(verbosity=2).run(suite);need(r.wasSuccessful(),'focused regression failed')
                    else:
                        r=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-v'],cwd=ROOT)
                        need(r.returncode==0,'full regression failed')
                    result={'status':'actual_regression_passed','kind':a.check}
            else:result=delivery(d,counts)
        print(json.dumps(result,ensure_ascii=False));return 0
    except (ValueError,KeyError,TypeError,OSError,IndexError,subprocess.TimeoutExpired) as e:
        print(json.dumps({'status':'check_failed','reason':str(e)},ensure_ascii=False));return 1

if __name__=='__main__':raise SystemExit(main())
