"""真实打印机案例接线前的T1/P2时区溢出回归（仅离线合成证据）。"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from shopping_decision.sale_configuration_evidence import assess_sale_evidence_report
from tests.test_p0_9_b_evidence import sample, report, MODELS


class RealPrinterT1Tests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.good = sample(self.now)

    def assess(self, *rows):
        return assess_sale_evidence_report(report(*rows), now=self.now, known_models=MODELS)

    def test_bad_withdrawal_and_use_loss_cannot_crash_or_revoke(self):
        for change in ({"review_status": "withdrawn"}, {"permitted_uses": ["local_parse"]}):
            for swapped in (False, True):
                with self.subTest(change=change, swapped=swapped):
                    bad = deepcopy(self.good)
                    bad.update(change)
                    bad["review_valid_until"] = "9999-12-31T23:59:59-00:01"
                    rows = (bad, self.good) if swapped else (self.good, bad)
                    out = self.assess(*rows)
                    self.assertEqual((out["accepted_rows"], out["rejected_count"]), (1, 1))
                    self.assertEqual(out["rejected"][0]["reason"],
                                     "review_withdrawn_or_unconfirmed" if "review_status" in change
                                     else "required_local_uses_not_evidenced")
                    # 表层拒绝原因是状态/用途；完整事件校验必须额外拒绝超界日期。
                    self.assertEqual(out["configurations"][0]["status"], "synthetic_field_binding_test_only")
                    self.assertFalse(out["transactions_enabled"])

    def test_bad_observation_timezone_overflow_rejects_row_only(self):
        bad = deepcopy(self.good)
        bad["observed_at"] = "9999-12-31T23:59:59-00:01"
        out = self.assess(bad, self.good)
        self.assertEqual((out["accepted_rows"], out["rejected_count"]), (1, 1))
        self.assertEqual(out["rejected"][0]["reason"], "source_observation_invalid")
        self.assertEqual(out["configurations"][0]["status"], "synthetic_field_binding_test_only")

    def test_valid_future_and_equivalent_timezone_and_legal_withdrawal(self):
        future = deepcopy(self.good)
        future["review_valid_until"] = "9999-12-31T23:59:59+00:01"
        out = self.assess(future)
        self.assertEqual(out["accepted_rows"], 1)
        self.assertEqual(out["configurations"][0]["review_valid_until"],
                         "9999-12-31T23:58:59+00:00")
        revoked = deepcopy(self.good)
        revoked["review_status"] = "withdrawn"
        revoked["observed_at"] = datetime.fromisoformat(self.good["observed_at"]).astimezone(
            timezone(timedelta(hours=5, minutes=45))).isoformat()
        out2 = self.assess(revoked, self.good)
        self.assertEqual(out2["configurations"][0]["status"],
                         "synthetic_same_source_invalidated_requires_review")

    def test_cli_bad_event_does_not_crash_all_rows(self):
        bad = deepcopy(self.good)
        bad["review_status"] = "withdrawn"
        bad["review_valid_until"] = "9999-12-31T23:59:59-00:01"
        with TemporaryDirectory() as d:
            fixture = Path(d) / "sale.json"
            fixture.write_text(json.dumps(report(self.good, bad), ensure_ascii=False), encoding="utf-8")
            turn = {"text": "原案合成输入", "answers": {"category": "printer",
                    "usage": "家用", "needs_color": False,
                    "monthly_pages_range": [0, 50], "budget_max_cny": 1000,
                    "wechat_required": True}}
            proc = subprocess.run(
                [sys.executable, "-m", "shopping_decision.dialogue_flow",
                 "--sale-evidence-report", str(fixture)],
                input=json.dumps(turn, ensure_ascii=False) + "\n", capture_output=True,
                text=True, encoding="utf-8", timeout=40)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        outputs = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertGreaterEqual(len(outputs), 2)
        evidence = outputs[-1]["sale_configuration_evidence"]
        self.assertEqual((evidence["accepted_rows"], evidence["rejected_count"]), (1, 1))
        self.assertTrue(any(e["status"] == "synthetic_field_binding_test_only"
                            for e in evidence["configurations"]))
        self.assertFalse(evidence["purchase_recommendation_approved"])
        self.assertFalse(evidence["transactions_enabled"])


if __name__ == "__main__":
    unittest.main()
