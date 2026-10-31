"""H03：仅检验按需研究规划，不能作为跨品类实际推荐准确率证明。"""
import json
import unittest
from datetime import date
from pathlib import Path

from shopping_decision.research_router import (
    ROUTE_TOPICS, EvidenceIndexEntry, plan_research
)

TODAY = date(2026, 10, 31)

def reviewed(category="空气净化器", topic="category_map", *, region="CN",
             reviewed_on="2026-10-01", recheck_on="2027-01-01",
             state="reviewed", source_url="https://source.example.org/evidence"):
    return EvidenceIndexEntry(
        evidence_id=category + "_" + topic,
        category=category, topic=topic,
        source_url=source_url, source_group="synthetic-group",
        region=region, reviewed_on=reviewed_on, recheck_on=recheck_on,
        state=state,
    )

class OnDemandResearchTests(unittest.TestCase):
    def test_no_category_asks_clarification(self):
        p = plan_research("   ", today=TODAY)
        self.assertEqual(p.status, "clarify")
        self.assertFalse(p.source_routes)

    def test_unknown_category_does_not_require_prebuilt_profile(self):
        p = plan_research("保温杯", today=TODAY)
        self.assertEqual(p.status, "research")
        self.assertEqual(p.missing_topics, ROUTE_TOPICS)
        self.assertFalse(p.reusable_ids)

    def test_any_category_can_reuse_verified_metadata(self):
        items = tuple(reviewed(topic=t) for t in ROUTE_TOPICS)
        p = plan_research("空气净化器", index=items, today=TODAY)
        self.assertEqual(p.status, "reuse")
        self.assertEqual(len(p.reusable_ids), 3)
        self.assertFalse(p.missing_topics)

    def test_time_expired_requires_recheck_not_reuse(self):
        item = reviewed(recheck_on="2026-09-30")
        p = plan_research("空气净化器", index=(item,), today=TODAY)
        self.assertEqual(p.status, "review_required")
        self.assertIn(item.evidence_id, p.recheck_ids)
        self.assertNotIn(item.evidence_id, p.reusable_ids)

    def test_region_mismatch_requires_recheck(self):
        item = reviewed(region="HK")
        p = plan_research("空气净化器", index=(item,), today=TODAY)
        self.assertIn(item.evidence_id, p.recheck_ids)
        self.assertIn("category_map", p.missing_topics)

    def test_unverified_or_disputed_is_not_accepted(self):
        for state in ("unverified", "disputed"):
            with self.subTest(state=state):
                item = reviewed(state=state)
                p = plan_research("空气净化器", index=(item,), today=TODAY)
                self.assertFalse(p.reusable_ids)
                self.assertIn(item.evidence_id, p.recheck_ids)

    def test_bad_date_or_invalid_url_blocks_reuse(self):
        for item in (reviewed(reviewed_on="unknown"),
                     reviewed(source_url="http://source.example.org/evidence"),
                     reviewed(reviewed_on="2026-12-01")):
            with self.subTest(item=item):
                p=plan_research("空气净化器", index=(item,), today=TODAY)
                self.assertFalse(p.reusable_ids)

    def test_product_stage_only_adds_products_topics(self):
        items=tuple(reviewed(topic=t) for t in ROUTE_TOPICS)
        p=plan_research("空气净化器", stage="product", index=items, today=TODAY)
        self.assertEqual(p.missing_topics, ("model_specs", "independent_comparison"))
        self.assertNotIn("live_price", p.missing_topics)

    def test_checkout_never_treats_cached_price_as_live(self):
        items=tuple(reviewed(topic=t) for t in ROUTE_TOPICS + ("model_specs", "independent_comparison", "live_price"))
        p=plan_research("空气净化器", stage="checkout", index=items, today=TODAY)
        self.assertEqual(p.status, "live_verification")
        self.assertEqual(p.live_check_topics, ("live_price", "availability", "seller_terms"))
        self.assertNotIn("空气净化器_live_price", p.reusable_ids)
        self.assertTrue(any(t=="live_price" for t,_ in p.source_routes))

    def test_other_categories_cannot_share_category_evidence(self):
        items=tuple(reviewed(category="打印机", topic=t) for t in ROUTE_TOPICS)
        p=plan_research("空调", index=items, today=TODAY)
        self.assertEqual(p.missing_topics, ROUTE_TOPICS)
        self.assertFalse(p.reusable_ids)

    def test_source_directory_is_index_not_download(self):
        root=Path(__file__).resolve().parent.parent
        data=json.loads((root/"knowledge/source_directory.json").read_text(encoding="utf-8"))
        roles=data["source_roles"]
        self.assertGreaterEqual(len(roles), 7)
        self.assertTrue(all("authority_scope" in x and "license_note" in x and "freshness" in x for x in roles))

if __name__=="__main__":
    unittest.main()
