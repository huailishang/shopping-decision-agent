import base64
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
import runpy
from shopping_decision.web import evaluate_input


class H09Repairs(unittest.TestCase):
    def test_compound_requirements_not_dropped_with_approved_test_fixture(self):
        fixture = runpy.run_path('tests/test_h05.py')['fixture']()
        for description in ('只打黑白，必须自动双面打印', '只打黑白；必须扫描；必须自动双面', '不需要彩色，但必须自动双面打印'):
            with self.subTest(description=description), patch('shopping_decision.decision.load_cards', return_value=fixture), patch('shopping_decision.web.load_cards', return_value=fixture):
                result = evaluate_input({'description': description, 'confirmed': True, 'monthly_pages': 200, 'needs_color': False})
                self.assertNotEqual(result['recommendation']['status'], 'route_recommended')
                self.assertTrue(any('必须自动双面' in s for s in result['recommendation']['unknowns']))

    def test_bridge_transmits_complete_audit(self):
        fields = ['只打黑白，必须自动双面打印', '200', '1000', '4', 'false', 'false', 'true', '', '']
        cmd = [sys.executable, '-m', 'shopping_decision.desktop_bridge'] + [base64.b64encode(x.encode()).decode() for x in fields]
        result = subprocess.run(cmd, text=True, capture_output=True, check=True)
        data = {a: base64.b64decode(b).decode('utf-8') for a,b in (line.split('\t', 1) for line in result.stdout.splitlines())}
        audit = json.loads(data['report_json'])
        for key in ('request','recommendation','rejected_evidence','rejected_inputs','evidence','evaluated_at','card_sha256','engine'):
            self.assertIn(key, audit)
        self.assertEqual(audit['recommendation']['status'], data['status'])
        self.assertIn('必须自动双面', '\n'.join(audit['recommendation']['unknowns']))


if __name__ == '__main__':
    unittest.main()
