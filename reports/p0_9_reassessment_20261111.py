"""11-11独立再评估；全离线、无密钥访问，不覆盖11-10证据。"""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from shopping_decision.p0_7_official_details import parse_detail, load_reviewed_local_replay, enrich_discovered_catalog
from shopping_decision.product_compare import compare_products, load_official_catalog
from shopping_decision.public_catalog import catalog_from_brother_snapshot, _read_bounded_json, BROTHER_SNAPSHOT
from shopping_decision.haina_ingest import ingest_haina_product_search
from shopping_decision.discovery_pool import build_discovery_pool


def main():
    now=datetime.now(timezone.utc)
    def evaluate(ident,snippet,expected):
        document_prefix='<!doctype html>' if ident=='style_case_sensitive_class_mismatch' else ''
        raw=(document_prefix+'<html><body><h1>HL-10W HL-10W 黑白激光打印机</h1>'+snippet+'<footer>服务支持</footer></body></html>').encode('utf-8')
        error=None
        try:
            detail=parse_detail('HL-10W',raw,observed_at=now)
            actual=detail['facts'].get('wireless',{}).get('value')
        except ValueError as exc:
            error=str(exc)
            actual=None
        passed=(error is not None) if expected=='reject' else (actual is expected and (expected is None or error is None))
        return {'id':ident,'input':snippet,'standards_doctype':bool(document_prefix),'expected':expected,'actual':actual,'rejected_reason':error,'expectation_met':passed}
    fresh=[
        ('question_not_assertion','本机是否支持无线网络连接？请查阅详细规格。',None),
        ('conditional_not_assertion','如果本机支持无线网络连接，请先连接路由器。',None),
        ('feature_subject_negative','本型号支持无线网络连接。更正：无线网络连接不支持，仅有USB。',None),
        ('long_other_model_section','<section><h2>HL-B2188DW</h2><p>连接方式说明</p><p>家庭网络环境</p><p>设置步骤如下</p><p>支持无线网络连接。</p></section><p>HL-10W仅USB。</p>',None),
        ('inline_css_comment_hidden','<span style="display:/**/none">支持无线网络连接</span>本机仅USB。',None),
        ('style_case_sensitive_class_mismatch','<style>.WIRELESS {display:none}</style><div class="wireless">HL-10W支持无线网络连接。</div>',True),
        ('different_feature_negative_then_positive','本型号不支持扫描。支持无线网络连接。',True),
        ('visible_descendant_not_hidden','<style>.panel .feature {opacity:0.75;display:block}</style><div class="panel"><span class="feature">HL-10W支持无线网络连接。</span></div>',True),
        ('different_model_negative_current_positive','<h2>DCP-B7658DW</h2><p>不支持无线网络连接。</p><h2>HL-10W</h2><p>本型号支持无线网络连接。</p>',True),
        ('unsupported_css_explicit_rejection','<style>.area + .secret{display:none}</style><div class="secret">支持无线网络连接</div>本机仅USB。','reject'),
        ('explicit_html_hidden_attribute','<div hidden="hidden"><p>HL-10W支持无线网络连接。</p></div>本机仅USB。',None),
        ('negation_across_inline_nodes','<p>本机<span>不</span>支持无线网络连接，仅USB。</p>',None),
    ]
    new=[evaluate(*x) for x in fresh]
    old=json.loads((ROOT/'reports/p0_9_independent_review_20261110.json').read_text(encoding='utf-8'))
    previous=[evaluate(x['id'],x['input'],x['expected']) for x in old['new_html_variants']]

    # 证明问句误提取会进入现有比较，而不只是抽取器局部输出。
    known=load_official_catalog()
    view=catalog_from_brother_snapshot(_read_bounded_json(BROTHER_SNAPSHOT),known_catalog=known,now=now)
    view['old_model_ids']=[x['model_id'] for x in known['products']]
    question_body=('<html><body>HL-10W HL-10W 黑白激光打印机 '+fresh[0][1]+' 服务支持</body></html>').encode('utf-8')
    question_detail=parse_detail('HL-10W',question_body,observed_at=now)
    promoted=enrich_discovered_catalog(view,[question_detail])
    question_comparison=compare_products(promoted,category='printer',required={'wireless':True},today=now.date())
    question_row=next(x for x in question_comparison['candidates'] if x['model_id']=='HL-10W')
    fact_admission={'input_is_synthetic_question':True,'wireless_required_met':'wireless' in question_row['required_met'],
                    'candidate_status':question_row['status'],'purchase_recommendation_approved':question_comparison['purchase_recommendation_approved']}

    catalog=load_reviewed_local_replay()
    provenance=[]
    for row in catalog['products']:
        detail=row.get('manufacturer_detail_evidence')
        if not detail: continue
        digest=detail['response_sha256']
        raw=(ROOT/'data/raw/p0_8_official_details'/(digest+'.html')).read_bytes()
        provenance.append({'model_id':row['model_id'],'hash_matches':hashlib.sha256(raw).hexdigest()==digest})
    stale=deepcopy(catalog)
    stale['recorded_on']=now.date().isoformat()
    for row in stale['products']:
        if row.get('manufacturer_detail_evidence'):
            row['manufacturer_detail_evidence']['observed_at']='2020-01-01T00:00:00Z'
    before=deepcopy(stale)
    result=compare_products(stale,category='printer',required={'wireless':True},today=now.date())
    stale_rows=[x for x in result['candidates'] if x.get('manufacturer_detail_evidence')]
    temporal={'rows':len(stale_rows),'all_wireless_unknown':all('wireless' in x['required_unknown'] for x in stale_rows),
        'all_billing_unknown':all(x['billing_model']=='unknown' for x in stale_rows),
        'all_current_consumables_empty':all(not x['consumables'] for x in stale_rows),'original_not_mutated':stale==before}

    payload={'error_code':0,'data':{'rows':[{'title':'兄弟 HL-B2158W 黑白激光打印机','brand_name':'Brother',
        'mall_name':'京东','shop_name':'独立合成店','cate3_name':'打印机','union_spec':'{"型号":"HL-B2158W"}'}]}}
    imported=ingest_haina_product_search(payload,observed_at=now.isoformat(),source_mode='synthetic_test',now=now)
    attacks=[
        ('nested_seller_object','seller_hint',{'url':'https://s.click.taobao.com/t?tracking=synthetic-review-11','price':1}),
        ('unknown_root_field','purchase_recommendation_approved',True),
        ('model_array_nonstring','title_model_candidates',[42]),
        ('nonbool_bundle','bundle_or_variant_ambiguous_hint',1),
        ('url_string_in_brand_hint','brand_hint','https://s.click.taobao.com/t?tracking=synthetic-review-11'),
        ('unhashable_identity_status','identity_status',{}),
    ]
    attacked=[]
    for ident,field,value in attacks:
        modified=deepcopy(imported)
        modified['items'][0][field]=value
        try:
            pool=build_discovery_pool([modified],now=now)
            attacked.append({'id':ident,'rejected_count':pool['rejected_count'],'visible_count':pool['unverified_source_lead_count'],
                'marker_leaked':'synthetic-review-11' in json.dumps(pool),'exception':None})
        except (ValueError,TypeError) as exc:
            attacked.append({'id':ident,'exception':type(exc).__name__,'exception_message':str(exc)})
    turns=[{'text':'独立合成确认：家中黑白、微信、预算千元','answers':{'category':'printer','usage':'家庭作业',
        'needs_color':False,'accepts_outsourced_color':True,'monthly_pages_range':[0,50],
        'budget_max_cny':1000,'wechat_required':True,'wechat_workflow':'miniprogram','requires_wireless':True}},
        {'text':'独立合成改答：改为彩色','answers':{'needs_color':True,'wechat_required':False}}]
    env={k:v for k,v in os.environ.items() if k not in ('PYTHONIOENCODING','PYTHONUTF8')}
    def run_cli(report):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'report.json'
            p.write_text(json.dumps(report,ensure_ascii=False),encoding='utf-8')
            proc=subprocess.run([sys.executable,'-m','shopping_decision.dialogue_flow','--haina-report',str(p)],
                input=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in turns).encode('utf-8'),capture_output=True,cwd=ROOT,env=env,timeout=30)
        output=proc.stdout.decode('utf-8')
        records=[json.loads(x) for x in output.splitlines()]
        return proc,records,output
    proc,records,output=run_cli(imported)
    facts=[r['comparison']['comparison']['comparison'] for r in records[1:]]
    cli={'returncode':proc.returncode,'utf8_env_variables_absent':True,'versions':[r['version'] for r in records[1:]],
        'old_conclusions_invalidated':records[-1]['history']['old_conclusions_invalidated'],
        'fact_counts':[len(r['candidates']) for r in facts],
        'model_count_before_limit':facts[0]['total_candidate_count'],
        'changed_candidates_all_excluded':all(x['status']=='excluded_by_verified_spec' for x in facts[1]['candidates']),
        'real_purchase_approved':records[1]['comparison']['purchase_recommendation_approved'],
        'transactions_enabled':records[1]['comparison']['transactions_enabled']}
    scalar_report=deepcopy(imported)
    scalar_report['items'][0]['brand_hint']=attacks[4][2]
    scalar_proc,scalar_records,scalar_output=run_cli(scalar_report)
    cli['scalar_hint_marker_reaches_cli']='synthetic-review-11' in scalar_output
    malformed_report=deepcopy(imported)
    malformed_row=deepcopy(imported['items'][0])
    malformed_row['source_id']='haina-synthetic-row:002'
    malformed_row['identity_status']={}
    malformed_report['items'].append(malformed_row)
    malformed_proc,malformed_records,malformed_output=run_cli(malformed_report)
    cli['one_bad_enum_discards_valid_report_rows']={
        'returncode':malformed_proc.returncode,'status':malformed_records[1]['discovery_pool']['status'],
        'visible_leads':len(malformed_records[1]['discovery_pool']['unverified_source_leads'])}
    raw_report=deepcopy(imported)
    raw_report['source_mode']='real_response'
    real_mode={'import_blocked':ingest_haina_product_search(payload,observed_at=now.isoformat(),source_mode='real_response',now=now)['status']=='blocked_real_data_use_not_approved',
        'report_blocked':build_discovery_pool([raw_report],now=now)['blocked_report_count']==1}
    data={'role':'independent_reviewer','observed_at':now.isoformat(),'new_html_variants':new,
        'new_case_count':len(new),'new_expectations_met':sum(x['expectation_met'] for x in new),
        'new_false_positives':sum(x['expected'] is None and x['actual'] is True for x in new),
        'new_false_negatives':sum(x['expected'] is True and x['actual'] is not True for x in new),
        'old_fourteen_replayed':previous,'old_expectations_met':sum(x['expectation_met'] for x in previous),
        'provenance':provenance,'stale_detail_checks':temporal,'new_report_mutations':attacked,
        'normal_cli':cli,'fact_admission':fact_admission,'real_mode_checks':real_mode,'new_api_calls':0,'credentials_read':False,
        'business_code_changed':False,'purchase_recommendation_approved':False,'transactions_enabled':False,
        'limitations':['手选故障诊断不代表随机网页总体错误率','本轮未联网回查供应商许可、详情接口、平台身份或地区报价','未知CSS拒绝只验证相应明确错误分支']}
    (ROOT/'reports/p0_9_reassessment_20261111.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:data[k] for k in ('new_case_count','new_expectations_met','new_false_positives','new_false_negatives','old_expectations_met','new_report_mutations','normal_cli','real_mode_checks')},ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
