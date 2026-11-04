"""H08 请求契约、证据门禁、HTTP 薄接口回归。"""
import json
import threading
import unittest
from datetime import date
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen, Request

from shopping_decision.evidence_policy import metadata_gate
from shopping_decision.web import Handler, build_request, evaluate_input


BASE = {'description': '给孩子打印学习资料，偶尔彩印，预算1000元', 'confirmed': True,
        'monthly_pages': 30, 'needs_color': True, 'accepts_outsourced_color': True,
        'budget_max_cny': 1000, 'idle_weeks': 4, 'requires_wireless': True,
        'requires_scan': None, 'requirements': []}


class H08WebTests(unittest.TestCase):
    def test_roundtrip_and_conservative_result(self):
        result = evaluate_input(BASE)
        self.assertEqual(result['request']['monthly_pages'], 30)
        self.assertIs(result['request']['needs_color'], True)
        self.assertIn(result['recommendation']['status'], ('defer', 'compare_routes'))
        self.assertEqual(result['evidence'], [])
        self.assertFalse(result['transactions_enabled'])
        self.assertEqual(result['engine'], 'shopping_decision.decision.decide')
        self.assertTrue(result['card_sha256'])

    def test_unknown_not_false_or_zero(self):
        req = build_request({'description': '打印资料', 'confirmed': True})
        self.assertIsNone(req.needs_color)
        self.assertIsNone(req.monthly_pages)
        self.assertEqual(evaluate_input({'description': '打印资料', 'confirmed': True})['recommendation']['status'], 'clarify')

    def test_conflict_detected_in_original_description(self):
        data = {**BASE, 'description': '必须在家彩印', 'needs_color': False}
        result = evaluate_input(data)
        self.assertEqual(result['recommendation']['status'], 'clarify')
        self.assertEqual(result['evidence'], [])

    def test_changed_fields_redecided_without_stale_records(self):
        first = evaluate_input({**BASE, 'needs_color': None})
        second = evaluate_input({**BASE, 'needs_color': False})
        self.assertEqual(first['recommendation']['status'], 'clarify')
        self.assertEqual(second['recommendation']['status'], 'defer')
        self.assertNotEqual(first['request'], second['request'])

    def test_invalid_number_and_confirmation(self):
        for v in (-1, 2.3, True, '30'):
            with self.subTest(v=v), self.assertRaises(ValueError):
                build_request({**BASE, 'monthly_pages': v})
        with self.assertRaises(ValueError):
            build_request({**BASE, 'confirmed': False})
        with self.assertRaises(ValueError):
            build_request({**BASE, 'category': 'hotel'})

    def test_publication_variants_decision_and_research(self):
        common = dict(url='https://example.org/item', region='CN', target_region='CN',
                      captured_on='2026-10-31', reviewed_on='2026-10-31',
                      recheck_on='2027-01-01', review_status='reviewed',
                      allowed_uses=('decision_support', 'research_index'),
                      today=date(2026, 11, 1), source_group='test-group')
        for value in (None, '', '未知'):
            with self.subTest(value=value):
                self.assertIn('unknown_publication', metadata_gate(**common, published_on=value, purpose='decision_support'))
                self.assertNotIn('unknown_publication', metadata_gate(**common, published_on=value, purpose='research_index'))

    def test_http_real_endpoint_and_error(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base + '/') as response:
                self.assertIn('先弄清需求'.encode(), response.read())
            req = Request(base + '/api/decide', data=json.dumps(BASE).encode(),
                          headers={'Content-Type': 'application/json'})
            with urlopen(req) as response:
                self.assertEqual(json.load(response)['request']['budget_max_cny'], 1000)
            req = Request(base + '/api/decide', data=json.dumps({**BASE, 'monthly_pages': -1}).encode(),
                          headers={'Content-Type': 'application/json'})
            with self.assertRaises(HTTPError) as exc:
                urlopen(req)
            self.assertEqual(exc.exception.code, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)


if __name__ == '__main__':
    unittest.main()
