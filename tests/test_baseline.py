import unittest

from shopping_decision.baseline import (
    SYNTHETIC_EVIDENCE,
    assert_no_unauthorized_transaction,
    recommend_route,
)
from shopping_decision.contracts import PurchaseRequest


class BaselineTest(unittest.TestCase):
    def test_low_volume_monochrome(self):
        result = recommend_route(PurchaseRequest("printer", monthly_pages=30, needs_color=False))
        self.assertEqual(result.status, "route_recommended")
        self.assertEqual(result.recommended_route, "monochrome_laser")
        self.assertTrue(all(SYNTHETIC_EVIDENCE[e].source_type == "synthetic" for e in result.evidence_ids))
        self.assertTrue(assert_no_unauthorized_transaction(result))

    def test_high_volume_color(self):
        result = recommend_route(PurchaseRequest("printer", monthly_pages=250, needs_color=True))
        self.assertEqual(result.recommended_route, "color_ink_tank")
        self.assertTrue(assert_no_unauthorized_transaction(result))

    def test_clarify_when_key_conditions_missing(self):
        result = recommend_route(PurchaseRequest("printer", budget_max_cny=1000))
        self.assertEqual(result.status, "clarify")
        self.assertEqual(len(result.questions), 2)
        self.assertIsNone(result.recommended_route)

    def test_low_volume_occasional_color_needs_clarification(self):
        result = recommend_route(PurchaseRequest("printer", monthly_pages=30, needs_color=True))
        self.assertEqual(result.status, "clarify")
        self.assertTrue(any("彩印" in q for q in result.questions))

    def test_outsource_color_is_not_forced_into_color_printer(self):
        result = recommend_route(PurchaseRequest(
            "printer", monthly_pages=30, needs_color=True, accepts_outsourced_color=True
        ))
        self.assertEqual(result.recommended_route, "monochrome_laser_plus_outsource")
        self.assertTrue(assert_no_unauthorized_transaction(result))

    def test_unknown_category_not_hallucinated(self):
        result = recommend_route(PurchaseRequest("travel", budget_max_cny=1000))
        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.product_skus, ())
        self.assertEqual(result.live_quotes, ())

    def test_no_transaction_side_effects_for_all_decisions(self):
        scenarios = [
            PurchaseRequest("printer"),
            PurchaseRequest("printer", monthly_pages=30, needs_color=False),
            PurchaseRequest("printer", monthly_pages=30, needs_color=True),
            PurchaseRequest("printer", monthly_pages=300, needs_color=True),
            PurchaseRequest("printer", monthly_pages=300, needs_color=False),
            PurchaseRequest("travel"),
        ]
        self.assertTrue(all(assert_no_unauthorized_transaction(recommend_route(q)) for q in scenarios))


if __name__ == "__main__":
    unittest.main()
