"""P0.9独立新增故障诊断；全部离线，不调用海纳，不改原始证据/业务代码。"""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shopping_decision.p0_7_official_details import parse_detail, load_reviewed_local_replay
from shopping_decision.product_compare import compare_products
from shopping_decision.dialogue_flow import new_dialogue, apply_turn, compare_dialogue
from shopping_decision.haina_ingest import ingest_haina_product_search
from shopping_decision.discovery_pool import build_discovery_pool
from shopping_decision.discovery_bridge import review_user_links


def main():
    now = datetime.now(timezone.utc)
    variants = [
        ("css_descendant_hidden", '<style>.wrap .secret{display:none}</style><div class="wrap"><div class="secret">支持无线网络连接</div></div>本型号仅USB。', None),
        ("css_attribute_hidden", '<style>[data-secret="yes"]{display:none}</style><div data-secret="yes">支持无线网络连接</div>本型号仅USB。', None),
        ("css_tag_hidden", '<style>aside{display:none}</style><aside>支持无线网络连接</aside>本型号仅USB。', None),
        ("css_compound_classes_hidden", '<style>.spec.secret{visibility:hidden}</style><div class="spec secret">支持无线网络连接</div>本型号仅USB。', None),
        ("other_family_dcp_scope", 'DCP-B7658DW支持无线网络连接；HL-10W仅USB。', None),
        ("other_family_mfc_scope", 'MFC-L5728DW支持无线网络连接。HL-10W仅USB。', None),
        ("paragraph_other_model_scope", '<section><h2>HL-B2188DW。</h2><p>支持无线网络连接。</p></section><section>HL-10W仅USB。</section>', None),
        ("positive_negative_separate_sentences", '本型号支持无线网络连接。更正：本型号不支持无线网络连接，仅USB。', None),
        ("positive_scope_following_sentence", '支持无线网络连接。以上功能仅适用于HL-B2188DW，HL-10W仅USB。', None),
        ("visible_opacity_half", '<span style="opacity:0.5">本型号支持无线网络连接。</span>', True),
        ("visible_comparison_with_other_model", '与HL-B2188DW相比，HL-10W同样支持无线网络连接。', True),
        ("visible_wireless_other_feature_negative", 'HL-10W支持无线网络连接，但不支持自动双面。', True),
        ("inherited_hidden_parent", '<div hidden><section><b>支持无线网络连接</b></section></div>本型号仅USB。', None),
        ("malformed_hidden_child", '<div hidden><span>支持无线网络连接</div>本型号仅USB。', None),
    ]
    results = []
    for ident, snippet, expected in variants:
        body = ('<html><body><h1>HL-10W HL-10W 黑白激光打印机</h1>' + snippet + '<footer>服务支持</footer></body></html>').encode('utf-8')
        parsed = parse_detail('HL-10W', body, observed_at=now)
        actual = parsed['facts'].get('wireless', {}).get('value')
        results.append({'id': ident, 'input': snippet, 'expected': expected,
                        'actual': actual, 'expectation_met': actual is expected})

    catalog = load_reviewed_local_replay()
    manifest_path = ROOT / 'reports/p0_8_refetched_official_sources_20261109.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    raw_checks = []
    for row in manifest['models']:
        item = next(x for x in catalog['products'] if x['model_id'] == row['model_id'])
        digest = row['response_sha256']
        raw = (ROOT / 'data/raw/p0_8_official_details' / (digest + '.html')).read_bytes()
        raw_checks.append({'model': row['model_id'], 'raw_sha256_matches': hashlib.sha256(raw).hexdigest() == digest,
                           'normal_output_uses_archive': item['manufacturer_detail_evidence']['response_sha256'] == digest})

    fault_checks = []
    real_read_text = Path.read_text
    for ident, change in (
        ('manifest_future_time', lambda x: x['models'][0].update(observed_at='2099-01-01T00:00:00Z')),
        ('manifest_invalid_digest', lambda x: x['models'][0].update(response_sha256='z' * 64)),
        ('manifest_duplicate_model', lambda x: x['models'].__setitem__(1, deepcopy(x['models'][0]))),
    ):
        changed = deepcopy(manifest)
        change(changed)
        def changed_read(path, *args, **kwargs):
            return json.dumps(changed) if path == manifest_path else real_read_text(path, *args, **kwargs)
        with patch.object(Path, 'read_text', changed_read):
            try:
                load_reviewed_local_replay()
                rejected = False
            except (ValueError, FileNotFoundError):
                rejected = True
        fault_checks.append({'id': ident, 'expectation_met': rejected})

    stale = deepcopy(catalog)
    stale['recorded_on'] = now.date().isoformat()
    old = next(x for x in stale['products'] if x['model_id'] == 'HL-10W')
    old['manufacturer_detail_evidence']['observed_at'] = '2020-01-01T00:00:00Z'
    stale_before = deepcopy(old)
    result = compare_products(stale, category='printer', required={'wireless': True},
                              preferred={'wechat_miniprogram': True}, today=now.date())
    old_result = next(x for x in result['candidates'] if x['model_id'] == 'HL-10W')
    stale_check = {'current_required_unknown': 'wireless' in old_result['required_unknown'],
                   'current_preference_unknown': 'wechat_miniprogram' in old_result['preferred_unknown'],
                   'historical_input_not_mutated': old == stale_before, 'status': old_result['status'],
                   'billing_still_exposed': old_result['billing_model']}

    state = apply_turn(new_dialogue(), {'category':'printer', 'usage':'独立合成家用场景',
        'needs_color':False,'accepts_outsourced_color':True,'monthly_pages_range':[0,50],
        'requires_wireless':True,'requires_auto_duplex':True,'wechat_required':False}, raw_text='独立合成确认')
    changed_state = apply_turn(state, {'requires_wireless':False,'requires_auto_duplex':False,'needs_color':True}, raw_text='独立合成改彩色')
    changed_result = compare_dialogue(changed_state)

    def payload(title='兄弟 HL-B2158W 黑白激光打印机', spec=None):
        return {'error_code':0,'data':{'rows':[{'title':title,'union_spec':spec or '{}','brand_name':'Brother',
            'cate3_name':'打印机','mall_name':'京东','shop_name':'独立合成店',
            'url':'https://union-click.jd.com/jdc?tracking=synthetic-marker',
            'price':1,'score':1,'comment_cnt':100,'platform_item_id':'1234567890',
            'purchase_recommendation_approved':True,'purchasable':True}]}}
    imported = ingest_haina_product_search(payload(), observed_at=now.isoformat(), source_mode='synthetic_test', now=now)
    normal_pool = build_discovery_pool([imported], now=now)
    malformed = deepcopy(imported)
    malformed['items'][0]['brand_hint'] = {'url':'https://s.click.taobao.com/t?tracking=synthetic-marker',
                                         'price':1,'purchase_recommendation_approved':True}
    malformed_pool = build_discovery_pool([malformed], now=now)
    rendered_malformed = json.dumps(malformed_pool)
    haina_checks = {
        'real_mode_blocked': ingest_haina_product_search(payload(), observed_at=now.isoformat(), source_mode='real_response', now=now)['status'] == 'blocked_real_data_use_not_approved',
        'raw_forged_platform_id_ignored': imported['items'][0]['platform_item_id'] is None,
        'raw_price_score_comments_ignored': all(k not in imported['items'][0] for k in ('price','score','comment_cnt')),
        'idless_stays_out_of_candidates': normal_pool['candidate_count'] == 0 and normal_pool['unverified_source_lead_count'] == 1,
        'imported_report_nested_hint_blocked': 'synthetic-marker' not in rendered_malformed,
        'nested_hint_actual': malformed_pool['unverified_source_leads'][0].get('brand_hint') if malformed_pool['unverified_source_leads'] else None,
        'mixed_platform_same_digits_separate': build_discovery_pool([
            review_user_links('打印机','https://item.jd.com/1234567890.html',now=now),
            review_user_links('打印机','https://item.taobao.com/item.htm?id=1234567890',platform='taobao',now=now)], now=now)['candidate_count'] == 2,
    }

    env = {**os.environ, 'PYTHONIOENCODING':'utf-8'}
    turns = [{'text':'独立合成初始确认','answers':{k:v['value'] for k,v in state['answers'].items()}},
             {'text':'独立合成修改','answers':{'requires_wireless':False,'requires_auto_duplex':False,'needs_color':True}}]
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'synthetic-report.json'
        path.write_text(json.dumps(malformed, ensure_ascii=False), encoding='utf-8')
        cli = subprocess.run([sys.executable,'-m','shopping_decision.dialogue_flow','--haina-report',str(path)],
            input=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in turns),
            capture_output=True, text=True, encoding='utf-8',env=env,cwd=ROOT,timeout=30)
    records = [json.loads(x) for x in cli.stdout.splitlines()]
    compared = [x['comparison']['comparison']['comparison'] for x in records[1:]]
    cli_check = {'returncode':cli.returncode, 'utf8_environment_explicit':True,
        'versions':[x['version'] for x in records[1:]],
        'old_conclusion_invalidated':records[2]['history']['old_conclusions_invalidated'],
        'candidate_counts':[len(x['candidates']) for x in compared],
        'first_has_exclusion':any(x['status']=='excluded_by_verified_spec' for x in compared[0]['candidates']),
        'all_changed_color_candidates_excluded':all(x['status']=='excluded_by_verified_spec' for x in compared[1]['candidates']),
        'malformed_hint_reaches_cli': 'synthetic-marker' in cli.stdout,
        'purchase_approved':changed_result['purchase_recommendation_approved'], 'transactions_enabled':changed_result['transactions_enabled']}

    smoke = json.loads((ROOT / 'reports/haina_local_smoke_20261110.json').read_text(encoding='utf-8'))
    smoke_check = {'recorded_http_status':smoke['http_status'],'recorded_business_code':smoke['business_code'],
        'summary_count':len(smoke['product_summaries']), 'recorded_returned_rows':smoke['returned_rows'],
        'mall_counts':{name:sum(x['mall_name']==name for x in smoke['product_summaries']) for name in ('京东','淘宝精选')},
        'raw_response_saved':smoke['raw_response_saved'],'raw_hash_independently_recomputable':False,
        'new_api_calls':0}
    # 仅本机精确比对，不打印密钥或文件内容。
    key_path = ROOT / 'data/private/haina.env'
    lines = key_path.read_text(encoding='utf-8-sig').splitlines()
    secrets = [line.split('=',1)[1].strip().strip('\"\'') for line in lines if line.strip().startswith('HAINA_API_KEY=')]
    files = subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0')
    matches = 0
    for relative in set(filter(None,files)):
        p = ROOT / relative
        if p.is_file():
            content = p.read_bytes()
            matches += int(any(s and s.encode('utf-8') in content for s in secrets))
    smoke_check['current_key_found_in_unignored_files'] = matches
    smoke_check['credential_git_ignored'] = subprocess.run(['git','check-ignore','-q','data/private/haina.env'],cwd=ROOT).returncode == 0
    smoke_check['credential_tracked'] = bool(subprocess.check_output(['git','ls-files','--','data/private/haina.env'],cwd=ROOT).strip())

    output = {'role':'independent_reviewer','observed_at':now.isoformat(), 'new_html_variants':results,
        'html_variant_count':len(results),'html_expectations_met':sum(x['expectation_met'] for x in results),
        'false_positive_count':sum(x['expected'] is None and x['actual'] is True for x in results),
        'false_negative_count':sum(x['expected'] is True and x['actual'] is not True for x in results),
        'normal_provenance':raw_checks,'source_fault_checks':fault_checks,'stale_check':stale_check,
        'haina_checks':haina_checks,'normal_cli':cli_check,'smoke_audit':smoke_check,
        'new_api_calls':0,'business_implementation_modified':False,
        'limitations':['合成故障诊断，不是抽取总体错误率或真实推荐成绩','真实业务响应未保留，无法本轮复算其原始字节哈希','不将synthetic_test标签当成实际来源真实性证明']}
    rendered = json.dumps(output,ensure_ascii=False,indent=2)+'\n'
    assert all(not s or s not in rendered for s in secrets)
    (ROOT / 'reports/p0_9_independent_review_20261110.json').write_text(rendered,encoding='utf-8')
    print(json.dumps({'new_html_variants':len(results),'expectations_met':sum(x['expectation_met'] for x in results),
        'false_positives':output['false_positive_count'],'false_negatives':output['false_negative_count'],
        'source_faults_rejected':sum(x['expectation_met'] for x in fault_checks),
        'normal_cli':cli_check,'haina_checks':haina_checks,'smoke_audit':smoke_check},ensure_ascii=True,indent=2))


if __name__ == '__main__':
    main()
