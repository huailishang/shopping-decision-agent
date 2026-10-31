"""H06 事实审查与独立许可分离：本测试的模拟批准不构成真实授权。"""
import json
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path
from shopping_decision.contracts import PurchaseRequest
from shopping_decision.decision import decide
from shopping_decision.knowledge import load_cards, card_qualification

ROOT=Path(__file__).resolve().parent.parent
NOW=date(2026,10,31)

class SourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards=load_cards()
        cls.audit=json.loads((ROOT/"knowledge/printer_source_audit.json").read_text(encoding="utf-8"))

    def test_every_card_has_executor_audit_and_no_recommendation_license(self):
        self.assertEqual(len(self.cards),13)
        self.assertEqual({x.id for x in self.cards},{x["card_id"] for x in self.audit["cards"]})
        for c in self.cards:
            self.assertIn(c.fact_audit_status,("supported_limited","supported_after_rewrite"))
            self.assertTrue(c.fact_audit_anchor)
            self.assertEqual(c.fact_audit_role,"executor")
            self.assertEqual(c.fact_audit_on,"2026-10-31")
            self.assertEqual(c.decision_support_approval,"not_granted")
            self.assertEqual(c.review_status,"pending")
            self.assertEqual(c.permitted_uses,("research_index",))

    def test_groups_are_not_counted_as_independent_cards(self):
        self.assertEqual(self.audit["cards_count"],13)
        self.assertEqual(self.audit["source_url_count"],5)
        self.assertEqual(self.audit["source_group_count"],4)
        self.assertEqual(len({x.source_group for x in self.cards}),4)

    def test_rewritten_four_cards_with_source_limit(self):
        rewritten=[c for c in self.cards if c.fact_audit_status=="supported_after_rewrite"]
        self.assertEqual({c.id for c in rewritten},{"CN-006","CN-008","CN-009","CN-010"})
        self.assertTrue(all(c.fact_audit_limit for c in rewritten))

    def test_manufacturer_faq_must_not_directly_vote_for_laser(self):
        for cid in ("CN-008","CN-009"):
            c=next(x for x in self.cards if x.id==cid)
            self.assertIsNone(c.route_effect)
        self.assertEqual(next(c for c in self.cards if c.id=="CN-011").source_kind,"regulator")

    def test_fact_verified_does_not_mean_decision_authorized(self):
        req=PurchaseRequest("printer",monthly_pages=200,needs_color=False)
        status=decide(req,cards=self.cards,today=NOW)
        self.assertEqual(status.recommendation.status,"defer")
        self.assertIn("missing_independent_decision_approval",str(status.rejected_evidence))

    def test_fake_metadata_approval_without_independent_reference_still_fails(self):
        req=PurchaseRequest("printer",monthly_pages=200,needs_color=False)
        c=next(x for x in self.cards if x.id=="CN-001")
        spoof=replace(c,review_status="reviewed",permitted_uses=("decision_support",),
                      reviewed_on="2026-10-31",recheck_on="2027-10-31",
                      route_inference_review="reviewed",decision_support_approval="approved")
        self.assertIn("missing_independent_decision_approval",card_qualification(req,spoof,today=NOW))

    def test_newer_sources_do_not_bypass_audit_and_plans_are_not_results(self):
        candidates=self.audit["new_source_candidates"]
        self.assertEqual(len(candidates),3)
        self.assertTrue(all(x["status"]!="approved" for x in candidates))
        self.assertIn("not_results",candidates[1]["status"])
        self.assertIn("not_primary_confirmed",candidates[2]["status"])
        self.assertEqual(self.audit["acceptance"]["decision_support_permit_count"],0)

if __name__=="__main__": unittest.main()
