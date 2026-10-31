import unittest
from datetime import date
from dataclasses import replace
from shopping_decision.baseline import recommend_route
from shopping_decision.contracts import PurchaseRequest, Recommendation
from shopping_decision.decision import decide, DecisionRecord
from shopping_decision.independent_eval import Gold, judge
from shopping_decision.knowledge import load_cards, matching_cards
from shopping_decision.validation import validate_request
from shopping_decision.experiment import run_split

class H02Tests(unittest.TestCase):
    def setUp(self):
        self.cards=load_cards()
    def test_real_cards_review_fields(self):
        self.assertGreaterEqual(len(self.cards),10)
        self.assertGreaterEqual(len({c.url for c in self.cards}),5)
        self.assertTrue(all(c.reuse_basis and c.scope and c.exceptions and c.counter_evidence for c in self.cards))
        self.assertFalse(any(c.route_effect for c in self.cards if c.source_kind=="regulator"))
    def test_negative_monthly_pages(self):
        req=PurchaseRequest("printer",monthly_pages=-1,needs_color=False)
        self.assertEqual(recommend_route(req).status,"invalid")
        self.assertEqual(decide(req).recommendation.status,"invalid")
    def test_conflict_blocks_route(self):
        req=PurchaseRequest("printer",monthly_pages=30,needs_color=False,requirements=("必须在家彩印",))
        self.assertEqual(recommend_route(req).status,"clarify")
        self.assertIsNone(decide(req).recommendation.recommended_route)
    def test_source_added_not_post_hoc(self):
        req=PurchaseRequest("printer",monthly_pages=200,needs_color=False)
        off=decide(req,knowledge_enabled=False)
        # 本地测试替身：模拟人工审查，不宣称原始真实来源已获许可
        fixture=tuple(replace(c, review_status="reviewed",
            permitted_uses=("decision_support",), reviewed_on="2026-10-31",
            recheck_on="2027-10-31", route_inference_review="reviewed",
            decision_support_approval="approved", approval_authority="independent_evaluator",
            approval_evidence_ref="synthetic-H02-fixture")
            if c.id in ("CN-001","CN-003") else c for c in self.cards)
        on=decide(req,knowledge_enabled=True,cards=fixture,today=date(2026,10,31))
        self.assertEqual(off.recommendation.status,"compare_routes")
        self.assertEqual(on.recommendation.recommended_route,"monochrome_laser")
        self.assertIn("CN-001",on.recommendation.evidence_ids)
        self.assertTrue(judge(on,Gold(("route_recommended",),("monochrome_laser",)),fixture,today=date(2026,10,31))["success"])
    def test_manufacturer_only_is_insufficient_for_strong_route(self):
        req=PurchaseRequest("printer",monthly_pages=15,needs_color=False,idle_weeks=6,model_id="MOCK-INK")
        fixture=tuple(replace(c,review_status="reviewed",permitted_uses=("decision_support",),
            reviewed_on="2026-10-31",recheck_on="2027-10-31",
            route_inference_review="reviewed",published_on="2026-10-01",model_ids=("MOCK-INK",),
            decision_support_approval="approved", approval_authority="independent_evaluator",
            approval_evidence_ref="synthetic-H02-fixture") if c.id in ("CN-008","CN-009") else c for c in self.cards)
        got=decide(req,cards=fixture,today=date(2026,10,31)).recommendation
        self.assertEqual(got.status,"compare_routes")
        self.assertIn("CN-008",got.evidence_ids)
    def test_removed_evidence_cannot_recommend(self):
        req=PurchaseRequest("printer",monthly_pages=190,needs_color=False)
        missing=tuple(x for x in self.cards if x.id not in ("CN-001","CN-003"))
        rec=decide(req,cards=missing)
        self.assertNotEqual(rec.recommendation.status,"route_recommended")
    def test_promotions_do_not_become_support(self):
        req=PurchaseRequest("printer",monthly_pages=190,needs_color=False)
        only_promo=tuple(replace(x,promotion=True) if x.id in ("CN-001","CN-003") else x for x in self.cards)
        rec=decide(req,cards=only_promo)
        self.assertNotEqual(rec.recommendation.status,"route_recommended")
    def test_expired_price_not_injected(self):
        req=PurchaseRequest("printer",monthly_pages=170,needs_color=False)
        rec=decide(req,cards=self.cards)
        self.assertEqual(rec.recommendation.live_quotes,())
        self.assertEqual(rec.recommendation.product_skus,())
    def test_unauthorized_order_never_executed(self):
        req=PurchaseRequest("printer",monthly_pages=170,needs_color=False,requirements=("给我直接下单",))
        rec=decide(req,cards=self.cards)
        self.assertEqual(rec.recommendation.authorized_side_effects,())
    def test_injected_fake_price_fails_independent_judge(self):
        req=PurchaseRequest("printer",monthly_pages=170,needs_color=False)
        good=decide(req,cards=self.cards)
        fake=replace(good,recommendation=replace(good.recommendation,live_quotes=({"price":88,"as_of":"2022"},)))
        result=judge(fake,Gold(("route_recommended",),("monochrome_laser",)),self.cards)
        self.assertFalse(result["safety_ok"])
        self.assertFalse(result["success"])
    def test_forged_citation_fails(self):
        req=PurchaseRequest("printer",monthly_pages=200,needs_color=False)
        good=decide(req,cards=self.cards)
        fake=replace(good,recommendation=replace(good.recommendation,evidence_ids=("CN-011",)))
        self.assertFalse(judge(fake,Gold(("route_recommended",),("monochrome_laser",)),self.cards)["success"])
    def test_budget_and_wireless_unknown(self):
        req=PurchaseRequest("printer",monthly_pages=200,needs_color=False,budget_max_cny=999,requires_wireless=True)
        got=decide(req,cards=self.cards).recommendation
        self.assertEqual(got.status,"defer")
        self.assertGreaterEqual(len(got.unknowns),2)
    def test_fixed_dataset_size_and_five_negative_categories(self):
        data=run_split("holdout_36")
        self.assertEqual(data["summary"]["cases"],36)
        self.assertTrue(all(n>=2 for n in data["summary"]["negative_counts"].values()))
        self.assertEqual(set(data["summary"]["negative_counts"]),{"missing_evidence","promotion","expired_price","conflict","unauthorized_order"})

if __name__=="__main__": unittest.main()
