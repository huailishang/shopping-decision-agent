"""Swing 子进程文本协议（所有值 Base64，避免 JSON 库和转义差异）。"""
import base64
import sys
import json
import re
import os
import time
from .web import evaluate_input

NAMES = ('monthly_pages','budget_max_cny','idle_weeks','needs_color','accepts_outsourced_color','requires_wireless','requires_scan')

def encode(s):
    return base64.b64encode(str(s).encode('utf-8')).decode('ascii')

def main():
    try:
        raw = [base64.b64decode(v, validate=True).decode('utf-8') for v in sys.argv[1:]]
        if len(raw) != 9:
            raise ValueError('条件数量不正确')
        data = {'description':raw[0], 'confirmed': True, 'requirements':raw[8].splitlines() if raw[8] else []}
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
            preview.append('【官网型号事实对比（非购买推荐；未核当前价格和库存）】')
            for item in comparison.get('candidates', []):
                feature = '；微信小程序功能有官方资料' if 'wechat_miniprogram' in item['preferred_met'] else ('；微信打印能力待核验' if 'wechat_miniprogram' in item['preferred_unknown'] else '')
                state = '硬条件不符合' if item['required_failed'] else '待核价/待复核'
                preview.append(item['name'] + '：' + state + feature + '；官方资料：' + item['official_url'])
            preview.append('上述名单仅是官网型号资料；任何一款均未证明符合预算或耐用性领先。')
        visible_reasons = '\n'.join((*rec['reasons'], *preview))
        output = [('status',rec['status']),('route',rec['recommended_route'] or ''),('reasons',visible_reasons),('questions','\n'.join(rec['questions'])),('unknowns','\n'.join(rec['unknowns'])),('evidence','\n'.join(e['id']+' '+e['source']+' '+e['published_on'] for e in result['evidence'])),('card_version',result['card_sha256']),('time',result['evaluated_at']),('report_json',json.dumps(result,ensure_ascii=False,indent=2))]
    except (ValueError,TypeError) as exc:
        output=[('error',str(exc))]
    for key,value in output:
        print(key+'\t'+encode(value))

if __name__ == '__main__':
    main()
