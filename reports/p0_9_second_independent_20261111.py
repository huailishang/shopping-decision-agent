"""第二轮独立准入/报告边界复验；无网络、无凭证、无业务代码修改。"""
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from shopping_decision.p0_7_official_details import parse_detail,enrich_discovered_catalog,load_reviewed_local_replay
from shopping_decision.public_catalog import catalog_from_brother_snapshot,_read_bounded_json,BROTHER_SNAPSHOT
from shopping_decision.product_compare import load_official_catalog,compare_products
from shopping_decision.haina_ingest import ingest_haina_product_search
from shopping_decision.discovery_pool import build_discovery_pool


def main():
    now=datetime.now(timezone.utc)
    def view():
        known=load_official_catalog()
        result=catalog_from_brother_snapshot(_read_bounded_json(BROTHER_SNAPSHOT),known_catalog=known,now=now)
        result['old_model_ids']=[x['model_id'] for x in known['products']]
        return result
    cases=[
        ('speculation','用户留言：本型号可能支持无线网络连接，尚待核对。'),
        ('quoted_question','客户问：“哪款机器支持无线网络连接？”本页没有回答。'),
        ('conditional_with_examples','在设备支持无线网络连接的前提下执行以下步骤。'),
        ('other_model_new_section','<section><h2>MFC-L2750DW使用指南</h2><p>支持无线网络连接。</p></section><p>HL-10W连接方式待确认。</p>'),
        ('positive_auto_unreviewed','HL-10W支持无线网络连接，微信小程序直连，支持远程打印。'),
        ('cancelled_claim','支持无线网络连接是旧模板文字，当前配置尚未确认。'),
        ('hidden_css_variable','<style>.x{display:var(--mode)}</style><span class="x">支持无线网络连接。</span>可见性未核。'),
        ('negative_record_not_promoted','本型号连接方式由人工核对。'),
    ]
    auto=[]
    for ident,text in cases:
        body=('<html><body><h1>HL-10W HL-10W 黑白激光打印机</h1>'+text+'<footer>服务支持</footer></body></html>').encode('utf-8')
        d=parse_detail('HL-10W',body,observed_at=now)
        if ident=='negative_record_not_promoted':
            d['facts']['wireless']={'value':False,'source_url':d['source_url'],'note':'独立合成负值准入测试'}
        catalog=enrich_discovered_catalog(view(),[d])
        compared=compare_products(catalog,category='printer',required={'wireless':True},today=now.date())
        row=next(x for x in compared['candidates'] if x['model_id']=='HL-10W')
        model=next(x for x in catalog['products'] if x['model_id']=='HL-10W')
        passed=('wireless' in row['required_unknown'] and not row['required_met'] and not row['required_failed']
                and model.get('manufacturer_claim_pending_review',{}).get('status')=='awaiting_per_field_review')
        auto.append({'id':ident,'input':text,'extracted_wireless':d['facts'].get('wireless',{}).get('value'),
                     'required_met':row['required_met'],'required_unknown':row['required_unknown'],
                     'required_failed':row['required_failed'],'expectation_met':passed})

    trusted=load_reviewed_local_replay()
    manifest_path=ROOT/'reports/p0_8_refetched_official_sources_20261109.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    trusted_checks=[]
    for record in manifest['models']:
        mid=record['model_id']
        digest=record['response_sha256']
        body=(ROOT/'data/raw/p0_8_official_details'/(digest+'.html')).read_bytes()
        d=parse_detail(mid,body,observed_at=datetime.fromisoformat(record['observed_at']))
        checks=[]
        for ident,mutate in [
            ('value',lambda x:x['facts']['wireless'].update(value=False)),
            ('digest',lambda x:x.update(response_sha256='0'*64)),
            ('billing',lambda x:x.update(billing_model='unknown' if x['billing_model']!='unknown' else 'buy_print_pages_to_claim_consumables')),
            ('consumables',lambda x:x['consumables'].append({'model':'TN_FAKE','source_url':x['source_url']})),
        ]:
            damaged=deepcopy(d)
            mutate(damaged)
            try:
                enrich_discovered_catalog(view(),[damaged],reviewed_local_replay=True)
                rejected=False
            except ValueError:
                rejected=True
            checks.append({'field':ident,'rejected':rejected})
        row=next(x for x in trusted['products'] if x['model_id']==mid)
        trusted_checks.append({'model':mid,'hash_matches':hashlib.sha256(body).hexdigest()==digest,
            'wireless_positive_retained':row['facts']['wireless']['value'] is True,'tamper_checks':checks})

    changed=deepcopy(manifest)
    changed['models'][0]['observed_at']='2026-11-10T12:00:00+00:00'
    original_read=Path.read_text
    def changed_read(path,*args,**kwargs):
        return json.dumps(changed) if path==manifest_path else original_read(path,*args,**kwargs)
    with patch.object(Path,'read_text',changed_read):
        refreshed=load_reviewed_local_replay()
    mid=manifest['models'][0]['model_id']
    comparison_day=date(2026,12,10)
    results=[]
    for name,catalog in [('original',trusted),('modified_manifest_time',refreshed)]:
        simulated=deepcopy(catalog)
        simulated['recorded_on']=comparison_day.isoformat()
        rows=compare_products(simulated,category='printer',required={'wireless':True},today=comparison_day)['candidates']
        row=next(x for x in rows if x['model_id']==mid)
        results.append({'mode':name,'observed_at':row['manufacturer_detail_evidence']['observed_at'],
                        'age_days':row['manufacturer_detail_age_days'],'is_stale':row['manufacturer_detail_is_stale'],
                        'required_met':row['required_met'],'required_unknown':row['required_unknown'],'status':row['status']})
    timestamp={'model':mid,'raw_bytes_unchanged':True,'only_manifest_observation_changed':True,
        'manifest_mutated_only_in_memory':True,'simulated_comparison_day':comparison_day.isoformat(),
        'catalog_date_freshness_held_equal_in_both_arms':True,'results':results,
        'expectation_met':not any(x['required_met'] for x in results)}

    payload={'error_code':0,'data':{'rows':[{'title':'兄弟 HL-B2158W 黑白激光打印机','brand_name':'Brother',
        'mall_name':'京东','shop_name':'独立合成好行','cate3_name':'打印机'}]}}
    base=ingest_haina_product_search(payload,observed_at=now.isoformat(),now=now,source_mode='synthetic_test')
    mutations=[
        ('encoded_url','brand_hint','https%3A%2F%2Fs.click.taobao.com/t?tracking=independent-second'),
        ('url_in_category','category_hint','https://s.click.taobao.com/t?tracking=independent-second'),
        ('tracking_in_seller','seller_hint','?utm_source=independent-second'),
        ('unhashable_link_kind','link_kind',[]),
        ('unhashable_product_kind','product_kind_status',{}),
        ('unknown_row_field','payment_approved',True),
        ('nonboolean_newness','used_or_refurbished_hint','no'),
        ('bad_time','observed_at','2099-01-01T00:00:00Z'),
    ]
    mixed=deepcopy(base)
    for index,(ident,field,value) in enumerate(mutations,2):
        bad=deepcopy(base['items'][0]);bad['source_id']=f'haina-synthetic-row:{index:03d}';bad[field]=value
        mixed['items'].append(bad)
    pool=build_discovery_pool([mixed],now=now)
    env={k:v for k,v in os.environ.items() if k not in ('PYTHONUTF8','PYTHONIOENCODING')}
    turns=[{'text':'独立复核合成需求','answers':{'category':'printer','needs_color':False,'accepts_outsourced_color':True,
        'usage':'家用','monthly_pages_range':[0,50],'requires_wireless':True,'requires_auto_duplex':True}},
        {'text':'独立复核合成改答彩色','answers':{'needs_color':True}}]
    with TemporaryDirectory() as tmp:
        file=Path(tmp)/'synthetic.json';file.write_text(json.dumps(mixed,ensure_ascii=False),encoding='utf-8')
        proc=subprocess.run([sys.executable,'-m','shopping_decision.dialogue_flow','--haina-report',str(file)],
            input=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in turns).encode('utf-8'),capture_output=True,cwd=ROOT,env=env,timeout=30)
    output=proc.stdout.decode('utf-8');records=[json.loads(line) for line in output.splitlines()]
    cli={'returncode':proc.returncode,'without_utf8_env_or_flags':True,'versions':[x['version'] for x in records[1:]],
         'old_conclusions_invalidated':records[-1]['history']['old_conclusions_invalidated'],
         'valid_rows_retained':records[1]['discovery_pool']['unverified_source_lead_count'],
         'bad_rows_rejected':records[1]['discovery_pool']['rejected_count'],'marker_absent':'independent-second' not in output,
         'candidate_display_counts':[len(x['comparison']['comparison']['comparison']['candidates']) for x in records[1:]],
         'has_explicit_exclusion':any(x['status']=='excluded_by_verified_spec' for x in records[1]['comparison']['comparison']['comparison']['candidates']),
         'changed_color_excludes_black':all(x['status']=='excluded_by_verified_spec' for x in records[2]['comparison']['comparison']['comparison']['candidates'])}
    result={'role':'independent_reviewer','observed_at':now.isoformat(),'new_unreviewed_claim_cases':auto,
        'admission_cases_passed':sum(x['expectation_met'] for x in auto),'admission_cases_total':len(auto),
        'reviewed_three_sources':trusted_checks,'timestamp_binding_test':timestamp,
        'new_report_mutations':[x[0] for x in mutations],
        'mixed_report':{'valid_rows':pool['unverified_source_lead_count'],'rejected':pool['rejected_count'],
            'platform_candidates':pool['candidate_count'],'marker_absent':'independent-second' not in json.dumps(pool)},
        'normal_cli':cli,'credentials_read':False,'new_api_calls':0,'business_code_modified':False,
        'purchase_recommendation_approved':False,'transactions_enabled':False,
        'limitations':['合成时效反证，不是现实来源已被篡改或本日已过期','准入隔离成绩不代表通用HTML抽取正确率','不复验供应商授权/平台身份或地区报价']}
    (ROOT/'reports/p0_9_second_independent_20261111.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('admission_cases_passed','admission_cases_total','timestamp_binding_test','mixed_report','normal_cli')},ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
