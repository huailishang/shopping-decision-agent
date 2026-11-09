"""Swing 子进程文本协议（所有值 Base64，避免 JSON 库和转义差异）。"""
import base64
import sys
import json
import re
import os
import time
from .web import evaluate_input

NAMES = ('monthly_pages','budget_max_cny','idle_weeks','needs_color','accepts_outsourced_color','requires_wireless','requires_scan')
LABELS = {'monochrome_print': '黑白打印', 'color_print': '彩色打印', 'wireless': '无线连接',
          'scan': '扫描', 'auto_duplex': '自动双面', 'wechat_miniprogram': '微信小程序打印',
          'wechat_transfer_to_app': '微信文件转存厂商App打印',
          'wechat_workflow_unconfirmed': '微信打印方式尚未确认'}
MISSING_LABELS = {'seller': '销售方', 'exact_model_and_selected_configuration': '准确型号与销售配置',
                  'condition_new_or_used': '新旧状态', 'price_and_currency': '金额与币种',
                  'promotion_eligibility': '优惠资格', 'shipping_and_required_extras': '运费及必要支出',
                  'delivery_region_and_stock': '地区与库存', 'valid_until': '有效期',
                  'included_consumables': '随机耗材', 'after_sales': '商家售后'}


def features(keys):
    return '、'.join(LABELS.get(k, '未理解的原文硬要求' if k.startswith('unresolved_hard_condition_') else k) for k in keys) or '无'

def encode(s):
    return base64.b64encode(str(s).encode('utf-8')).decode('ascii')

def main():
    try:
        raw = [base64.b64decode(v, validate=True).decode('utf-8') for v in sys.argv[1:]]
        if len(raw) not in (9, 14):
            raise ValueError('条件数量不正确')
        data = {'description':raw[0], 'confirmed': True, 'requirements':raw[8].splitlines() if raw[8] else []}
        if len(raw) == 14:
            for name, value in zip(('wechat_required', 'wechat_workflow', 'requires_auto_duplex', 'delivery_region', 'budget_scope'), raw[9:]):
                if name in ('wechat_required', 'requires_auto_duplex'):
                    if value not in ('', 'true', 'false'):
                        raise ValueError(name + ' 必须是true、false或未知')
                    data[name] = None if value == '' else value == 'true'
                else:
                    data[name] = (value or None) if name == 'delivery_region' else (value or 'unknown')
        for k,v in zip(NAMES,raw[1:8]):
            if k in NAMES[3:] and v not in ('', 'true', 'false'):
                raise ValueError(k + ' 必须是true、false或未知')
            # monthly_pages 允许如0–50的区间文本，统一交由web.py校验；其他数字保持原来严格整数解析。
            data[k] = (None if not v else
                       (int(v) if k == 'monthly_pages' and re.fullmatch(r'[0-9]+', v) else
                        v if k == 'monthly_pages' else
                        (v == 'true' if k in NAMES[3:] else int(v))))
        result = evaluate_input(data)
        if os.environ.get("SHOPPING_H09_TEST_DELAY_MS"):
            time.sleep(min(5, int(os.environ["SHOPPING_H09_TEST_DELAY_MS"])/1000))
        rec = result['recommendation']
        # 桌面自然语言区域显示只读型号事实；绝不将候选冒充正式推荐或成交价。
        comparison = result.get('product_comparison', {})
        preview = []
        if comparison.get('status') == 'facts_comparison_only':
            scope = {'device_delivered': '主机含运费及必要支出；额外耗材单列',
                     'device_and_extra_consumables': '包括本次额外购买耗材，耗材金额仍待核',
                     'unknown': '尚待用户确认'}[result['request']['budget_scope']]
            preview.append('预算口径：' + scope + '；收货地区：' + ('按用户已确认范围记录，未据此证明有货或包邮' if result['request']['delivery_region'] else '尚待确认'))
            case = comparison.get('case_comparison', {})
            if case.get('status') == 'limited_manual_case_comparison':
                preview.append('【同一需求的三型号取舍（执行者人工基线，待独立评审）】')
                preview.append(case['notice'])
                if case['baseline_needs_recheck']:
                    preview.append('基线获取已超过30天，以下历史比较须回源复核。')
                for row in case['models']:
                    state = ('硬条件不符合' if row['required_failed'] else
                             '先核未解决硬条件：' + features(row['required_unknown']) if row['required_unknown'] else '仅继续资料核查，预算未通过')
                    preview.append(row['name'] + '：' + state)
                    for note in row['notes']:
                        kind = '资料事实' if note['kind'] == 'source_fact' else '项目条件性解释'
                        preview.append('  ' + kind + '：' + note['text'] + '；适用：' + note['condition'] + '；反面/局限：' + note['counterpoint'])
                        for source in note['sources']:
                            preview.append('    来源：' + source['url'] + '；获取日：' + source['captured_on'] + '；资料日期：' + source['date_note'])
                preview.append('低印量局限：' + case['low_volume_interpretation'])
                for source in case['low_volume_sources']:
                    preview.append('  低印量引用：' + source['url'] + '；获取日：' + source['captured_on'] + '；' + source['date_note'])
                preview.extend('共同未知：' + text for text in case['shared_unknowns'])
            preview.append('【型号事实与零售核验（非购买推荐）】')
            for item in comparison.get('candidates', []):
                feature = '；微信小程序功能有官方资料（未实机测试）' if 'wechat_miniprogram' in item['preferred_met'] + item['required_met'] else ('；微信打印能力待核验' if any('wechat' in k for k in item['preferred_unknown'] + item['required_unknown']) else '')
                state = '硬条件不符合' if item['required_failed'] else '待核价/待复核'
                preview.append(item['name'] + '：' + state + feature)
                preview.append('  满足：' + features(item['required_met']) + '；不满足：' + features(item['required_failed']) + '；待核硬条件：' + features(item['required_unknown']))
                preview.append('  预算：未核实；主机含运费：未知；额外耗材/多年成本：未知；耐用性独立对比：未知')
                service = item.get('manufacturer_service', {})
                if service:
                    preview.append('  厂商资料：' + service.get('summary', '') + '；来源：' + service.get('source_url', '') + '；获取日：' + service.get('captured_on', '') + '（销售配置与商家售后待核）')
                included = item.get('included_consumables_reference', {})
                if included:
                    preview.append('  随机耗材线索：' + included['summary'] + '；来源：' + included['source_url'] + '；获取日：' + included['captured_on'])
                for check in item.get('retail_checks', []):
                    access = {'restricted_or_login_page': '页面受限或要求登录', 'unreachable_or_blocked': '访问失败或受阻', 'partial_public_page': '公开页信息不完整'}.get(check['access_status'], '未核实')
                    preview.append('  京东只读回查：' + access + '；缺字段：' + '、'.join(MISSING_LABELS.get(k, k) for k in check['missing_fields']) + '；链接：' + check['url'] + '；获取：' + check['retrieved_at'] + '；报价有效期：未知')
                if not item.get('retail_checks'):
                    preview.append('  零售渠道：尚无该型号已核实销售项')
                preview.append('  官方资料：' + item['official_url'] + '；获取日：' + comparison['catalog_recorded_on'])
            preview.append('任何一款均未证明符合预算或耐用性领先；缺报价/库存/销售配置时继续暂缓。')
        visible_reasons = '\n'.join((*rec['reasons'], *preview))
        output = [('status',rec['status']),('route',rec['recommended_route'] or ''),('reasons',visible_reasons),('questions','\n'.join(rec['questions'])),('unknowns','\n'.join(rec['unknowns'])),('evidence','\n'.join(e['id']+' '+e['source']+' '+e['published_on'] for e in result['evidence'])),('card_version',result['card_sha256']),('time',result['evaluated_at']),('report_json',json.dumps(result,ensure_ascii=False,indent=2))]
    except (ValueError,TypeError) as exc:
        output=[('error',str(exc))]
    for key,value in output:
        print(key+'\t'+encode(value))

if __name__ == '__main__':
    main()
