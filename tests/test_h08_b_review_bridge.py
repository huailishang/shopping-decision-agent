"""R1 专项：只有逐条已批准的限定主张才能进入普通调用；批准样例均为合成测试替身。"""
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from shopping_decision.web import evaluate_input


def synthetic_ledger(*, claim_updates=None, source_updates=None):
    claim = {
        "id": "SYNTHETIC-H08B-C100",
        "topic": "decision_factors",
        "claim": "测试替身：比较购机成本时还应看长期耗材成本。",
        "exceptions": "这是合成例子，不是实际商品建议。",
        "counter_evidence": "未对中国当前在售型号或价格提供证据。",
        "claim_scope": "模拟打印机长期成本比较",
        "sample_scope": "人工测试替身，无真实型号",
        "scope_level": "category_principle",
        "applies_when": "any",
        "route_effect": None,
        "approval": {
            "review_status": "reviewed",
            "permitted_uses": ["decision_support"],
            "reviewed_on": "2026-11-02",
            "recheck_on": "2026-12-31",
            "fact_audit_status": "supported_limited",
            "route_inference_review": "pending",
            "decision_support_approval": "approved",
            "approval_authority": "independent_evaluator",
            "approval_evidence_ref": "synthetic-only-reviewed-claim",
        }
    }
    if claim_updates:
        for key, val in claim_updates.items():
            if key == "approval":
                claim["approval"].update(val)
            else:
                claim[key] = val
    source = {
        "id": "SYNTHETIC-H08B-S100",
        "source_url": "https://example.org/synthetic-review",
        "source_org": "合成审查替身",
        "source_group": "synthetic-test-not-real",
        "source_kind": "comparative",
        "published_on": "2026-10-01",
        "captured_on": "2026-11-02",
        "scope": {"region": "CN"},
        "section_anchor": "synthetic test text",
        "reuse_basis": "仅测试",
        "decision_claims": [claim]
    }
    source.update(source_updates or {})
    return {"evidence": [source]}


class H08BReviewBridgeTests(TestCase):
    user = {"description": "每月0–50页，家里黑白，彩印可以去店里，想要微信打印",
            "confirmed": True, "monthly_pages": "0–50", "needs_color": False,
            "accepts_outsourced_color": True}

    def execute(self, ledger):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            path.write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
            with patch("shopping_decision.route_claims.ROUTE_LEDGER_PATH", path), \
                 patch("shopping_decision.web.ROUTE_LEDGER_PATH", path):
                return evaluate_input(self.user)

    def test_current_real_sources_not_approved(self):
        actual = evaluate_input(self.user)
        self.assertEqual(actual["recommendation"]["status"], "defer")
        self.assertEqual(actual["evidence"], [])
        self.assertEqual(actual["recommendation"]["evidence_ids"], ())
        rejected_ids = {item[0] for item in actual["rejected_evidence"]}
        self.assertIn("H08B-C04", rejected_ids)

    def test_synthetic_approved_claim_reaches_ordinary_result_with_scope_and_citation(self):
        response = self.execute(synthetic_ledger())
        rec = response["recommendation"]
        self.assertEqual(rec["status"], "compare_routes")
        self.assertIsNone(rec["recommended_route"])
        self.assertEqual(rec["evidence_ids"], ("SYNTHETIC-H08B-C100",))
        self.assertIn("合成审查替身", rec["reasons"][0])
        self.assertIn("反证", rec["reasons"][0])
        self.assertIn("模拟打印机长期成本比较", rec["reasons"][0])
        self.assertEqual(response["evidence"][0]["id"], "SYNTHETIC-H08B-C100")
        self.assertEqual(response["evidence"][0]["approval_record"], "synthetic-only-reviewed-claim")
        self.assertEqual(response["recommendation"]["live_quotes"], ())
        self.assertEqual(response["recommendation"]["product_skus"], ())
        self.assertTrue(response["research_ledger_sha256"])

    def test_unapproved_or_mismatched_claims_never_reach_result(self):
        cases = [
            ("not approved", {"approval": {"decision_support_approval": "not_granted"}}, {}),
            ("no independent signature", {"approval": {"approval_evidence_ref": ""}}, {}),
            ("user cannot self-approve", {"approval": {"approval_authority": "request_user"}}, {}),
            ("wrong use", {"approval": {"permitted_uses": ["research_index"]}}, {}),
            ("not reviewed", {"approval": {"review_status": "pending"}}, {}),
            ("no fact audit", {"approval": {"fact_audit_status": "pending"}}, {}),
            ("expired", {"approval": {"recheck_on": "2026-10-31"}}, {}),
            ("wrong scope", {}, {"scope": {"region": "US"}}),
            ("missing publication", {}, {"published_on": None}),
            ("promotion", {}, {"promotion": True}),
        ]
        for label, c, s in cases:
            with self.subTest(label=label):
                result = self.execute(synthetic_ledger(claim_updates=c, source_updates=s))
                self.assertEqual(result["recommendation"]["status"], "defer")
                self.assertEqual(result["evidence"], [])
                self.assertNotIn("SYNTHETIC-H08B-C100", result["recommendation"]["evidence_ids"])

    def test_duplicate_claim_id_cannot_replace_historical_evidence(self):
        forged = synthetic_ledger(claim_updates={"id": "CN-001"})
        with self.assertRaises(ValueError):
            self.execute(forged)

    def test_source_approved_does_not_approve_new_claim(self):
        ledger = synthetic_ledger()
        ledger["evidence"][0]["independent_approval"] = "approved"
        ledger["evidence"][0]["decision_claims"][0]["approval"]["decision_support_approval"] = "not_granted"
        result = self.execute(ledger)
        self.assertEqual(result["recommendation"]["status"], "defer")
        self.assertEqual(result["evidence"], [])


if __name__ == "__main__":
    import unittest
    unittest.main()
