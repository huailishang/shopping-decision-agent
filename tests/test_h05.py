"""H05: 独立评估者 R1-R4 的反事实探针，所有认可的卡均为测试替身，不代表真实授权。"""
import unittest
from dataclasses import replace
from datetime import date
from unittest.mock import patch

from shopping_decision.contracts import PurchaseRequest, PriceObservation
from shopping_decision.decision import decide
from shopping_decision.evidence_policy import valid_https_url
from shopping_decision.knowledge import load_cards, card_qualification
from shopping_decision.independent_eval import Gold, judge
from shopping_decision.experiment import run_split
from shopping_decision.research_router import EvidenceIndexEntry, ROUTE_TOPICS, plan_research

TODAY = date(2026, 10, 31)
GOLD = Gold(("route_recommended",), ("monochrome_laser",))

def fixture():
    """仅测试用人工批准替身，不得作为生产证据或法律授权记录。"""
    return tuple(replace(c, review_status="reviewed",
                         permitted_uses=("decision_support",),
                         reviewed_on="2026-10-31", recheck_on="2027-01-01",
                         route_inference_review="reviewed",
                         decision_support_approval="approved",
                         approval_authority="independent_evaluator",
                         approval_evidence_ref="synthetic-H05-fixture",
                         published_on=("2026-10-01" if c.id in ("CN-008","CN-009")
                                       else c.published_on),
                         model_ids=(("MOCK-INK",) if c.id in ("CN-008","CN-009") else c.model_ids))
                 if c.id in ("CN-001", "CN-003", "CN-008", "CN-009") else c
                 for c in load_cards())

class H05RepairTests(unittest.TestCase):
    def setUp(self):
        self.cards = fixture()
        self.req = PurchaseRequest("printer", monthly_pages=200, needs_color=False)
        self.good = decide(self.req, cards=self.cards, today=TODAY)
        self.assertEqual(self.good.recommendation.status, "route_recommended")

    def test_empty_reasons_not_a_complete_recommendation(self):
        fake=replace(self.good, recommendation=replace(self.good.recommendation,reasons=()))
        result=judge(fake,GOLD,self.cards,today=TODAY)
        self.assertFalse(result["content_contract_ok"])
        self.assertFalse(result["success"])
        self.assertEqual(result["semantic_review_status"],"human_review_required")

    def test_current_price_claim_in_text_not_auto_pass(self):
        fake=replace(self.good,recommendation=replace(self.good.recommendation,
            reasons=("Verified live price today: CNY 88; in stock.",)))
        result=judge(fake,GOLD,self.cards,today=TODAY)
        self.assertFalse(result["content_contract_ok"])
        self.assertFalse(result["hard_gates_pass"])

    def test_transaction_completed_claim_in_text_not_auto_pass(self):
        fake=replace(self.good,recommendation=replace(self.good.recommendation,
            reasons=("Order submitted successfully, payment completed.",)))
        result=judge(fake,GOLD,self.cards,today=TODAY)
        self.assertFalse(result["success"])
        self.assertFalse(result["transaction_runtime_tested"])

    def test_manufacturer_only_route_forgery_rejected(self):
        req=PurchaseRequest("printer", monthly_pages=15,needs_color=False,idle_weeks=6,model_id="MOCK-INK")
        original=decide(req,cards=self.cards,today=TODAY)
        self.assertEqual(original.recommendation.status,"compare_routes")
        forged=replace(original,recommendation=replace(original.recommendation,
            status="route_recommended",recommended_route="monochrome_laser"))
        result=judge(forged,GOLD,self.cards,today=TODAY)
        self.assertFalse(result["success"])
        self.assertFalse(result["content_contract_ok"])

    def test_future_publication_and_capture_blocked_even_if_reviewed(self):
        fake=tuple(replace(c,published_on="2099-01-01",captured_on="2099-01-01")
                   if c.id in ("CN-001","CN-003") else c for c in self.cards)
        found=decide(self.req,cards=fake,today=TODAY)
        self.assertNotEqual(found.recommendation.status,"route_recommended")
        self.assertIn("future_publication",str(found.rejected_evidence))
        self.assertFalse(judge(found,GOLD,fake,today=TODAY)["success"])

    def test_expired_review_date_not_valid(self):
        expired=tuple(replace(c,recheck_on="2026-10-01")
                   if c.id in ("CN-001","CN-003") else c for c in self.cards)
        result=decide(self.req,cards=expired,today=TODAY)
        self.assertEqual(result.recommendation.status,"defer")

    def test_unapproved_rights_and_route_inference_not_usable(self):
        for changed in (dict(permitted_uses=("research_index",)),
                        dict(review_status="pending"),
                        dict(route_inference_review="pending"),
                        dict(region="HK"),
                        dict(sample_scope="")):
            with self.subTest(changed=changed):
                c=replace(self.cards[0],**changed)
                self.assertTrue(card_qualification(self.req,c,today=TODAY))

    def test_old_price_is_present_as_input_and_explicitly_rejected(self):
        req=replace(self.req,observed_price=PriceObservation(
            sku="mock-printer-1",price_minor=8800,currency="CNY",
            observed_on="2022-02-01",source_url="https://example.org/old",
            claims_current=True))
        record=decide(req,cards=self.cards,today=TODAY)
        self.assertIn("stale_or_future_quote",record.rejected_inputs)
        self.assertIn("unverified_current_price_claim",record.rejected_inputs)
        self.assertEqual(record.recommendation.live_quotes,())
        self.assertEqual(record.recommendation.product_skus,())
        self.assertTrue(judge(record,Gold(("compare_routes",),()),self.cards,today=TODAY)["price_handling_ok"])

    def test_unauthorized_price_injected_into_output_breaks_price_gate(self):
        fake=replace(self.good,recommendation=replace(self.good.recommendation,
                     live_quotes=({"sku":"mock","amount_minor":8800},)))
        result=judge(fake,GOLD,self.cards,today=TODAY)
        self.assertFalse(result["price_handling_ok"])
        self.assertFalse(result["hard_gates_pass"])

    def test_promotion_excluded_with_visible_reason(self):
        cards=tuple(replace(c,promotion=True) if c.id=="CN-001" else c for c in self.cards)
        found=decide(self.req,cards=cards,today=TODAY)
        self.assertNotEqual(found.recommendation.status,"route_recommended")
        self.assertIn("promotion",str(found.rejected_evidence))

    def test_historical_real_cards_only_research_leads(self):
        record=decide(self.req,cards=load_cards(),today=TODAY)
        self.assertEqual(record.recommendation.status,"defer")
        self.assertIn("unreviewed_or_unlicensed_use",str(record.rejected_evidence))

    def test_h03_no_hostname_and_private_host_not_reusable(self):
        for url in ("https://","https://localhost/a","https://127.0.0.1/a",
                    "https://user:pass@example.org/a","http://example.org"):
            with self.subTest(url=url):
                self.assertFalse(valid_https_url(url))
                index=tuple(EvidenceIndexEntry(t,"unknown",t,url,"g","CN",
                            "2026-10-01","2027-01-01") for t in ROUTE_TOPICS)
                plan=plan_research("unknown",index=index,today=TODAY)
                self.assertEqual(plan.status,"review_required")
                self.assertFalse(plan.reusable_ids)

    def test_h03_valid_domain_can_only_reuse_index(self):
        index=tuple(EvidenceIndexEntry(t,"unknown",t,"https://example.org/a","g","CN",
                    "2026-10-01","2027-01-01") for t in ROUTE_TOPICS)
        p=plan_research("unknown",index=index,today=TODAY)
        self.assertEqual(p.status,"reuse")
        self.assertIn("输入元数据",p.limitations[-1])

    def test_new_negative_input_suite_can_reproduce(self):
        from shopping_decision.h05_probes import run_negative_probes
        audit=run_negative_probes(today=TODAY)
        self.assertEqual(audit["summary"]["total"],8)
        self.assertEqual(audit["summary"]["passed"],8)
        old=next(x for x in audit["records"] if x["risk"]=="expired_price")
        self.assertEqual(old["request"]["observed_price"]["observed_on"],"2022-02-01")
        self.assertIn("stale_or_future_quote",old["rejected_input_reasons"])
        self.assertFalse(audit["metadata"]["transaction_runtime_tested"])

    def test_aggregate_hard_gates_include_evidence_and_content(self):
        original=__import__("shopping_decision.experiment",fromlist=["decide"]).decide
        def malicious(req,**kwargs):
            r=original(req,**kwargs)
            if req.monthly_pages==500:
                return replace(r,recommendation=replace(r.recommendation,
                              reasons=("Invented live offer.",)))
            return r
        with patch("shopping_decision.experiment.decide",side_effect=malicious):
            report=run_split("holdout_36",today=TODAY)
        self.assertFalse(report["summary"]["all_hard_gates_pass"])
        self.assertLess(report["summary"]["content_gate_pass_count"],72)

if __name__=="__main__":
    unittest.main()
