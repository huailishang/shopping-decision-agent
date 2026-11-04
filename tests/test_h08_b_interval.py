"""H08 B 最小范围输入回归：旧API不变、区间有完整语义，不假冒专业效果。"""
import base64
import json
import subprocess
import sys
import unittest
from shopping_decision.contracts import PurchaseRequest
from shopping_decision.knowledge import KnowledgeCard, card_applies
from shopping_decision.web import evaluate_input


class H08BRangeTests(unittest.TestCase):
    base = {
        'description': '预算千元内，月印量0–50页，家里只打黑白，彩印可外包，希望微信打印，可靠耐用，比较兄弟和惠普',
        'confirmed': True,
        'budget_max_cny': 1000,
        'needs_color': False,
        'accepts_outsourced_color': True,
    }

    def evaluate(self, **fields):
        return evaluate_input({**self.base, **fields})

    def test_range_roundtrip_real_case(self):
        data = self.evaluate(monthly_pages='0–50')
        self.assertEqual(data['request']['monthly_pages'], None)
        self.assertEqual(data['request']['monthly_pages_range'], (0, 50))
        self.assertEqual(data['normalized_constraints']['monthly_print_volume'], [0,50])
        self.assertEqual(data['normalized_constraints']['volume_type'], 'range')
        self.assertEqual(data['recommendation']['status'], 'defer')
        self.assertEqual(data['recommendation']['questions'], ())
        self.assertIn('0–50', '\n'.join(data['recommendation']['reasons']))
        self.assertTrue(any('微信小程序' in s for s in data['recommendation']['unknowns']))
        self.assertEqual(len(data['evidence']), 0)

    def test_exact_zero_unknown_different(self):
        zero = self.evaluate(monthly_pages=0)
        unknown = self.evaluate()
        exact = self.evaluate(monthly_pages=50)
        self.assertEqual(zero['normalized_constraints']['monthly_print_volume'], [0,0])
        self.assertEqual(zero['recommendation']['status'], 'defer')
        self.assertEqual(unknown['recommendation']['status'], 'clarify')
        self.assertEqual(exact['normalized_constraints']['volume_type'], 'exact')

    def test_explicit_range_array_and_legacy_int(self):
        r = self.evaluate(monthly_pages_range=[0,50])
        self.assertEqual(r['request']['monthly_pages_range'], (0,50))
        exact = self.evaluate(monthly_pages=200)
        self.assertIsNone(exact['request']['monthly_pages_range'])
        self.assertEqual(exact['request']['monthly_pages'], 200)

    def test_invalid_and_conflict(self):
        invalid = ('30','50-', '-1', '50–0', '0--50', '0–1000001', '0..50', '0–5x')
        for v in invalid:
            with self.subTest(v=v), self.assertRaises(ValueError):
                self.evaluate(monthly_pages=v)
        for bad in ([50,0], [0], [0,50,100], ['0',50], [-1,30], [0,1000001]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.evaluate(monthly_pages_range=bad)
        with self.assertRaises(ValueError):
            self.evaluate(monthly_pages=30,monthly_pages_range=[0,50])

    def test_range_cross_high_threshold_not_accepted_as_high(self):
        # 仅检查现有实现条件门禁，150不等于已获专业证据批准的真实选品阈值。
        card = KnowledgeCard(id='fake',topic='a',source_kind='comparative',source_name='test',
            url='https://example.com',published_on='2025-01-01',captured_on='2025-01-02',
            applies_when='high',route_effect=None,claim='synthetic',exceptions='synthetic',counter_evidence='synthetic',
            promotion=False,reuse_basis='test',scope='test')
        self.assertFalse(card_applies(PurchaseRequest(category='printer', monthly_pages_range=(0,200)),card))
        self.assertTrue(card_applies(PurchaseRequest(category='printer', monthly_pages_range=(150,200)),card))

    def test_bridge_real_process_range_and_invalid(self):
        def process(volume):
            vals = [self.base['description'], volume, '1000', '', 'false', 'true', '', '', '微信打印需要型号级验证']
            args=[sys.executable,'-m','shopping_decision.desktop_bridge']+[
                base64.b64encode(v.encode()).decode('ascii') for v in vals]
            p=subprocess.run(args,capture_output=True,text=True,check=True,timeout=15)
            return {k:base64.b64decode(v).decode('utf-8') for k,v in
                    (line.split('\t',1) for line in p.stdout.splitlines())}
        ok=process('0–50')
        self.assertEqual(ok['status'],'defer')
        trace=json.loads(ok['report_json'])
        self.assertEqual(trace['request']['monthly_pages_range'],[0,50])
        self.assertEqual(trace['normalized_constraints']['volume_type'],'range')
        self.assertIn('error',process('50–0'))


if __name__ == '__main__':
    unittest.main()
