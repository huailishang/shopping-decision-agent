import base64
import subprocess
import sys
import unittest


class DesktopBridgeTest(unittest.TestCase):
    def run_case(self, fields):
        args = [sys.executable, '-m', 'shopping_decision.desktop_bridge'] + [base64.b64encode(s.encode()).decode('ascii') for s in fields]
        p = subprocess.run(args, capture_output=True, text=True, check=True)
        return {parts[0]: base64.b64decode(parts[1]).decode('utf-8') for line in p.stdout.splitlines() if len(parts := line.split('\t', 1)) == 2}

    def test_real_backend_and_unknown(self):
        result = self.run_case(['家庭打印', '30', '1000', '4', 'true', 'true', 'true', '', ''])
        self.assertEqual(result['status'], 'defer')
        self.assertIn('暂缓唯一推荐', result['reasons'])
        self.assertTrue(result['card_version'])
        self.assertEqual(self.run_case(['家庭打印', '', '', '', '', '', '', '', ''])['status'], 'clarify')

    def test_conflict_and_validation(self):
        result = self.run_case(['必须在家彩印', '30', '1000', '4', 'false', 'true', '', '', ''])
        self.assertEqual(result['status'], 'clarify')
        self.assertIn('error', self.run_case(['打印', '-1', '', '', '', '', '', '', '']))
        self.assertIn('error', self.run_case(['打印', '', '', '', 'nonsense', '', '', '', '']))

    def test_changed_decision_is_fresh(self):
        first = self.run_case(['打印', '30', '', '', '', '', '', '', ''])
        second = self.run_case(['打印', '30', '', '', 'false', '', '', '', ''])
        self.assertEqual(first['status'], 'clarify')
        self.assertEqual(second['status'], 'defer')
