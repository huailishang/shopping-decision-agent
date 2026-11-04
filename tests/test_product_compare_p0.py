"""P0 商品事实、硬约束三态和原桌面路径边界回归。"""
import copy
import json
import tempfile
from datetime import date
from pathlib import Path
from unittest import TestCase

from shopping_decision.product_compare import (
    compare_products, compare_printer_request, load_official_catalog,
)
from shopping_decision.web import evaluate_input, build_request


REAL_USER = {
    "description": "预算1000元内，每月0–50页，家里只打印黑白，偶尔彩印可在店里打印，想要微信打印，优先兄弟和惠普，可靠耐用",
    "confirmed": True, "monthly_pages": "0–50", "budget_max_cny": 1000,
    "needs_color": False, "accepts_outsourced_color": True,
}


class ProductComparisonP0Tests(TestCase):
    def setUp(self):
        self.catalog = load_official_catalog()

    def test_real_canonical_sources_and_unique_models(self):
        self.assertEqual(len(self.catalog["products"]), 5)
        self.assertEqual(self.catalog["market_region"], "CN")
        self.assertEqual(len({p["model_id"] for p in self.catalog["products"]}), 5)

    def test_actual_case_comparison_is_useful_but_not_purchasable(self):
        out = evaluate_input(REAL_USER)
        self.assertEqual(out["recommendation"]["status"], "defer")
        comp = out["product_comparison"]
        self.assertEqual(comp["status"], "facts_comparison_only")
        self.assertEqual(comp["searched_models"], 5)
        self.assertFalse(comp["purchase_recommendation_approved"])
        self.assertFalse(comp["transactions_enabled"])
        self.assertFalse(comp["all_prices_real_time_verified"])
        by_id = {c["model_id"]: c for c in comp["candidates"]}
        self.assertIn("wechat_miniprogram", by_id["HL-L1238W"]["preferred_met"])
        self.assertIn("wechat_miniprogram", by_id["HL-L1808W"]["preferred_met"])
        self.assertIn("wechat_miniprogram", by_id["HP-Laser-108w"]["preferred_unknown"])
        self.assertEqual(by_id["HL-L1238W"]["manufacturer_suggested_retail_cny"], 1906)
        self.assertFalse(by_id["HL-L1238W"]["manufacturer_suggested_retail_is_live_price"])
        for c in comp["candidates"]:
            self.assertEqual(c["budget_status"], "unverified_no_authorized_live_quote")
            self.assertIsNone(c["live_price_cny"])
            self.assertIsNone(c["marketplace_sku"])
            self.assertNotEqual(c["status"], "specs_matched_not_purchase_approved")
        self.assertEqual(out["evidence"], [])
        self.assertEqual(out["recommendation"]["product_skus"], ())

    def test_explicit_wireless_requirement_excludes_proven_usb_only(self):
        out = compare_products(self.catalog, category="printer",
                               required={"monochrome_print": True, "wireless": True},
                               budget_max_cny=1000)
        x = {c["model_id"]: c for c in out["candidates"]}
        self.assertIn("wireless", x["HL-L1228"]["required_failed"])
        self.assertIn("wireless", x["HP-Laser-108a"]["required_failed"])
        self.assertEqual(x["HL-L1238W"]["required_failed"], [])

    def test_absent_data_is_unknown_not_false(self):
        out = compare_products(self.catalog, category="printer",
                               required={"wechat_miniprogram": True},
                               budget_max_cny=None)
        x = {c["model_id"]: c for c in out["candidates"]}
        self.assertIn("wechat_miniprogram", x["HP-Laser-108w"]["required_unknown"])
        self.assertNotIn("wechat_miniprogram", x["HP-Laser-108w"]["required_failed"])

    def test_wechat_preference_is_not_automatic_hard_filter(self):
        out = evaluate_input(REAL_USER)["product_comparison"]
        self.assertNotIn("wechat_miniprogram", out["constraints"]["required"])
        self.assertTrue(out["constraints"]["preferred"]["wechat_miniprogram"])

    def test_source_without_url_cannot_pass_facts(self):
        data = copy.deepcopy(self.catalog)
        data["products"][0]["facts"]["wireless"]["source_url"] = None
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "bad.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_official_catalog(path)

    def test_unknown_fact_cannot_claim_verified_source(self):
        data = copy.deepcopy(self.catalog)
        data["products"][0]["facts"]["wifi6"] = {"value": None,
                                                  "source_url": "https://example.org/", "note": ""}
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "bad.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_official_catalog(path)

    def test_duplicate_model_rejected(self):
        data = copy.deepcopy(self.catalog)
        data["products"].append(copy.deepcopy(data["products"][0]))
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "dup.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_official_catalog(path)

    def test_comparator_is_category_agnostic(self):
        fake = {"source_kind": "test_fixture", "recorded_on": date.today().isoformat(),
                "products": [
                    {"category": "kettle", "model_id": "A", "brand": "test", "name": "A",
                     "official_url": "https://example.org/a",
                     "facts": {"auto_off": {"value": True, "source_url": "https://example.org/a"}}},
                    {"category": "kettle", "model_id": "B", "brand": "test", "name": "B",
                     "official_url": "https://example.org/b", "facts": {}},
                ]}
        out = compare_products(fake, category="kettle",
                               required={"auto_off": True})
        self.assertEqual(out["searched_models"], 2)
        by_id = {v["model_id"]: v for v in out["candidates"]}
        self.assertEqual(by_id["A"]["status"], "specs_matched_not_purchase_approved")
        self.assertEqual(by_id["B"]["status"], "needs_verification")

    def test_conflicting_user_statement_blocks_candidate_output(self):
        user = {**REAL_USER, "description": "必须在家彩印，但只需要黑白打印"}
        out = evaluate_input(user)
        self.assertEqual(out["recommendation"]["status"], "clarify")
        self.assertEqual(out["product_comparison"]["candidates"], [])

    def test_real_time_price_forgery_not_admitted(self):
        data = copy.deepcopy(self.catalog)
        data["products"][0]["live_price_cny"] = 399
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "bad.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_official_catalog(path)

    def test_no_side_effects_and_no_ranking_claim(self):
        out = compare_printer_request(build_request(REAL_USER))
        self.assertFalse(out["transactions_enabled"])
        self.assertFalse(out["purchase_recommendation_approved"])
        self.assertTrue(any("非质量" in t for t in out["limitations"]))
