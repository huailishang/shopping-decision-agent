"""Swing 子进程文本协议（所有值 Base64，避免 JSON 库和转义差异）。"""
import base64
import sys
import json
import re
import os
import time
from pathlib import Path
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
        argv = sys.argv[1:]
        haina_mcp_report_path = None
        if argv and argv[0] == '--haina-mcp-report':
            if len(argv) < 3:
                raise ValueError('海纳研究材料参数不完整')
            haina_mcp_report_path = Path(argv[1])
            argv = argv[2:]
        if any(value == '--haina-mcp-report' for value in argv):
            raise ValueError('海纳研究材料参数位置不正确')
        raw = [base64.b64decode(v, validate=True).decode('utf-8') for v in argv]
        if len(raw) not in (9, 14, 15):
            raise ValueError('条件数量不正确')
        data = {'description':raw[0], 'confirmed': True, 'requirements':raw[8].splitlines() if raw[8] else []}
        if len(raw) >= 14:
            for name, value in zip(('wechat_required', 'wechat_workflow', 'requires_auto_duplex', 'delivery_region', 'budget_scope'), raw[9:14]):
                if name in ('wechat_required', 'requires_auto_duplex'):
                    if value not in ('', 'true', 'false'):
                        raise ValueError(name + ' 必须是true、false或未知')
                    data[name] = None if value == '' else value == 'true'
                else:
                    data[name] = (value or None) if name == 'delivery_region' else (value or 'unknown')
        if len(raw) == 15:
            data['device_deployment_region'] = raw[14] or None
        for k,v in zip(NAMES,raw[1:8]):
            if k in NAMES[3:] and v not in ('', 'true', 'false'):
                raise ValueError(k + ' 必须是true、false或未知')
            # monthly_pages 允许如0–50的区间文本，统一交由web.py校验；其他数字保持原来严格整数解析。
            data[k] = (None if not v else
                       (int(v) if k == 'monthly_pages' and re.fullmatch(r'[0-9]+', v) else
                        v if k == 'monthly_pages' else
                        (v == 'true' if k in NAMES[3:] else int(v))))
        result = evaluate_input(data, haina_mcp_report_path=haina_mcp_report_path)
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
        case_research = result.get('real_printer_case_research')
        if isinstance(case_research, dict):
            shared = case_research.get('shared_research_snapshot', {})
            if shared.get('status') == 'research_snapshot_only_not_purchase':
                preview.append('【共享研究结果｜计算全部候选，仅展示前三项；不含购买许可】')
                preview.append('已计算候选：' + str(shared['total_candidate_count'])
                               + '；下一动作：' + str(shared['next_action']))
                for candidate in shared.get('displayed_candidates', []):
                    preview.append('  ' + str(candidate['model_id']) + '：'
                                   + str(candidate['eligibility']))
                if shared.get('hidden_candidates'):
                    preview.append('其余已计算但未展示：' + '、'.join(
                        str(item['model_id']) for item in shared['hidden_candidates']))
                for question in shared.get('necessary_user_questions', []):
                    preview.append('待本人确认：' + str(question))
            comparison = case_research.get('model_comparison', {})
            effects = case_research.get('decision_effects', {})
            if effects.get('status') == 'source_limited_development_not_independent_effect':
                preview.append('【认知增量与关键缺件｜仅型号研究，未通过独立效果验收】')
                for effect in effects.get('judgments', [])[:4]:
                    preview.append(str(effect['id']) + '：' + str(effect['claim'])
                                   + '；对判断的作用：' + str(effect['decision_effect']))
                    preview.append('  仍缺：' + '、'.join(effect.get('missing', []))
                                   + '；来源：' + '、'.join(ref.get('url', '')
                                       for ref in effect.get('source_refs', [])))
                for question in effects.get('questions', []):
                    preview.append('关键补问：' + question)
                preview.append('候选路线（不含购买资格）：' + '、'.join(
                    str(route.get('name')) + ('（条件冲突，暂停判断）'
                        if route.get('eligibility') == 'blocked_by_user_condition_conflict' else '')
                    for route in effects.get('routes', [])))
            preview.append('【公开厂家资料的两型号比较｜不是海纳数据，也不是平台在售核验】')
            for item in case_research.get('reasons', [])[:9]:
                preview.append(str(item.get('id')) + '：' + str(item.get('reason'))
                               + '；限制：' + str(item.get('counter_evidence')))
            selection = case_research.get('criteria_comparison', {})
            if selection.get('status') == 'criteria_driven_research_not_purchase':
                preview.append('【本轮条件驱动的型号资格｜依据版本：' +
                               str(selection.get('criteria_version')) + '】')
                preview.append('当前依据 SHA-256：' + str(selection.get('criteria_sha256')))
                preview.append('本轮规范化硬要求：' + str(selection.get('normalized_required', {}))
                               + '；未识别：' + str(selection.get('unresolved_hard_conditions', []))
                               + '；未建准则：' + str(selection.get('unmodeled_hard_requirements', [])))
                relation_names = {
                    'match': '符合', 'mismatch': '不符合',
                    'unknown': '未核', 'at_or_below': '不高于',
                    'above': '高于', 'below': '低于建议区间',
                    'within': '位于建议区间', 'equal': '等于建议区间',
                    'contains': '覆盖建议区间', 'overlap': '与建议区间部分重叠',
                    'workflow_unconfirmed': '微信打印流程未确认',
                    'other_workflow_unverified': 'App替代流程待实测',
                    'deployment_region_unconfirmed': '设备部署地未知，微信服务未核',
                    'deployment_outside_verified_scope': '境外微信服务缺有效适用证据',
                }
                for model in selection.get('models', []):
                    state_label = {
                        'excluded_by_hard_condition': '本轮硬条件排除',
                        'pending_hard_evidence': '存在硬条件未知，暂不能判满足',
                        'model_spec_research_only': '规格研究候选，不是购买批准',
                        'blocked_by_user_condition_conflict': '本人确认与原文硬条件冲突，暂停入选',
                    }.get(model.get('eligibility'), '研究状态待核')
                    preview.append(str(model.get('model_id')) + '：' + state_label)
                    for check in model.get('checks', []):
                        name = str(check.get('criterion_id'))
                        relation = relation_names.get(check.get('relation'), '未核')
                        preview.append('  ' + name + ' ' + relation + '；用户：' +
                                       str(check.get('user_value')) + '；型号事实：' +
                                       str(check.get('product_value')) + ' ' +
                                       str(check.get('unit')) + '；来源：' +
                                       '、'.join(check.get('source_ids', [])) + '；证据状态：' +
                                        str(check.get('evidence_state', 'unknown')) + '；局限：' +
                                       str(check.get('unknown_or_counter', '')))
                    preview.append('  地区到手价、购买资格与平台销售身份：未核，不可购买')
                for question in selection.get('questions', [])[:6]:
                    preview.append('待核：' + str(question))
                preview.append('【依据来源与适用限制】')
                for source_id, source in selection.get('source_registry', {}).items():
                    preview.append(str(source_id) + ' (' +
                                   str(source.get('type', 'unknown')) + ')：' +
                                   str(source.get('url', '')) + '；限制：' +
                                   str(source.get('limit', '')))
            for item in comparison.get('comparisons', [])[:8]:
                preview.append(str(item.get('dimension')) + '：' + str(item.get('result'))
                               + '（来源：' + '、'.join(item.get('source_ids', [])) + '）')
            for item in comparison.get('active_conditional_decisions', [])[:3]:
                preview.append('当前条件触发的取舍：' + str(item.get('when')) + ' → ' + str(item.get('model'))
                               + '；' + str(item.get('reason')) + '（未批准购买）')
            for item in comparison.get('unknown_conditional_decisions', [])[:3]:
                preview.append('条件尚未确认：' + str(item.get('when')) + '；需补：'
                               + '；'.join(item.get('conditions_before_purchase', [])))
            preview.append('部署地区范围：' + str(comparison.get('deployment_region_scope', 'unknown'))
                           + '；是否已提供部署地：' + str(comparison.get('deployment_region_provided', False)))
            preview.append('当前平台商品身份：'
                           + str(comparison.get('real_sale_identity_verified_count', 0))
                           + '；地区有效报价：'
                           + str(comparison.get('regional_live_quote_count', 0))
                           + '；购买批准：否。')
        haina_mcp = result.get('haina_mcp_research')
        if isinstance(haina_mcp, dict):
            preview.append('【海纳MCP研究材料｜显式本机文件；当前仅允许合成接线测试】')
            preview.append('材料状态：' + str(haina_mcp.get('status', 'unknown'))
                           + '；实体数：' + str(haina_mcp.get('entity_count', 0))
                           + '；平台身份核实：' + str(haina_mcp.get('platform_identity_verified_count', 0))
                           + '；有效报价：' + str(haina_mcp.get('quote_verified_count', 0)))
            if haina_mcp.get('error'):
                preview.append('材料拒绝/错误原因：' + str(haina_mcp.get('error')))
            for entity in haina_mcp.get('entities', [])[:3]:
                preview.append('实体线索：' + str(entity.get('entity_name', '未命名'))
                               + '；型号候选：' + '、'.join(entity.get('model_candidates', []))
                               + '；销售线索数：' + str(entity.get('sale_lead_count', 0)))
                for lead in entity.get('sale_leads', [])[:2]:
                    preview.append('  销售线索：' + str(lead.get('title') or '未返回商品标题')
                                   + '；身份：' + str(lead.get('identity_status'))
                                   + '；商城：' + str(lead.get('mall_hint') or '未知')
                                   + '；店铺：' + str(lead.get('seller_hint') or '未知')
                                   + '；链接域名：' + str(lead.get('link_host') or '未知')
                                   + '；供方价格线索：' + str(lead.get('supplier_price_hint') or '无')
                                   + '（未核验，不是到手价）')
                for parameter in entity.get('parameters', [])[:5]:
                    preview.append('  参数线索：' + str(parameter.get('name') or '未命名')
                                   + ' = ' + str(parameter.get('value') or parameter.get('description') or '未知')
                                   + '（供应商返回，待核）')
                for opinion in entity.get('opinion_summaries', [])[:3]:
                    preview.append('  评价摘要线索：' + str(opinion.get('attribute_name') or '未命名')
                                   + ' / ' + str(opinion.get('attribute_value') or '未知')
                                   + '（供应商聚合，非独立评测）')
            preview.append('本材料不提升平台商品ID、地区报价、预算通过或购买批准；合成内容不代表真实商品。')
        visible_reasons = '\n'.join((*rec['reasons'], *preview))
        output = [('status',rec['status']),('route',rec['recommended_route'] or ''),('reasons',visible_reasons),('questions','\n'.join(rec['questions'])),('unknowns','\n'.join(rec['unknowns'])),('evidence','\n'.join(e['id']+' '+e['source']+' '+e['published_on'] for e in result['evidence'])),('card_version',result['card_sha256']),('time',result['evaluated_at']),('report_json',json.dumps(result,ensure_ascii=False,indent=2))]
    except (ValueError,TypeError) as exc:
        output=[('error',str(exc))]
    for key,value in output:
        print(key+'\t'+encode(value))

if __name__ == '__main__':
    main()
