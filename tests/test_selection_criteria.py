"""2026-11-15 S0-S7 本轮反例，不更改历史评估或真实材料。"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
import json
import unittest

from shopping_decision.selection_criteria import load_criteria, evaluate_selection
from shopping_decision.real_printer_case import compare_case_research
from shopping_decision.haina_mcp_ingest import (
    _provider_price_hint, _parse_sku_entity, _entity_bucket,
    ingest_haina_mcp_bundle, SYNTHETIC_FIXTURE_PATH,
)


BASE = {
    "category": "printer", "budget_max_cny": 1000,
    "monthly_pages_range": [0, 50],
    "needs_color": False, "accepts_outsourced_color": True,
    "wechat_required": None, "wechat_workflow": "unknown",
    "requires_scan": None, "requires_auto_duplex": None,
    "requirements": ["可靠耐用，微信打印"],
}


def row(view, model):
    return next(item for item in view["models"] if item["model_id"] == model)


def check(view, model, criterion):
    return next(item for item in row(view, model)["checks"]
                if item["criterion_id"] == criterion)


class CognitionComparisonExecutionTests(unittest.TestCase):
    def test_m1_f1_color_excludes_both_even_if_scan_or_duplex(self):
        values = {**BASE, "needs_color": True, "requires_scan": True,
                  "requires_auto_duplex": True}
        view = compare_case_research(values)
        research = view["criteria_comparison"]
        self.assertEqual(set(research["excluded_models"]), {"HL-L1238W", "M232dw"})
        self.assertEqual(research["research_eligible_models"], [])
        hp_decision = next(x for x in view["model_comparison"]["conditional_decisions"]
                           if x["id"] == "DEC-01")
        self.assertEqual(hp_decision["applicability"], "not_applicable")
        self.assertTrue(hp_decision["hard_condition_override_blocked"])
        self.assertFalse(any(x["id"] == "DEC-01" for x in
                             view["model_comparison"]["active_conditional_decisions"]))
        self.assertIn("先排除", next(x["reason"] for x in view["reasons"]
                                 if x["id"] == "CASE-04"))
        restored = compare_case_research({**values, "needs_color": False})
        self.assertIn("M232dw", restored["criteria_comparison"]["research_eligible_models"])
        self.assertIn("DEC-01", [x["id"] for x in
                                 restored["model_comparison"]["active_conditional_decisions"]])

    def test_m1_conflicting_free_text_blocks_active_model_candidates(self):
        values = {**BASE, "requires_scan": True, "needs_color": False,
                  "requirements": ["必须彩色打印"]}
        view = compare_case_research(values)
        criteria = view["criteria_comparison"]
        self.assertTrue(criteria["user_condition_conflicts"])
        self.assertEqual(criteria["research_eligible_models"], [])
        self.assertEqual(criteria["pending_models"], [])
        self.assertEqual([m["eligibility"] for m in criteria["models"]],
                         ["blocked_by_user_condition_conflict"] * 2)
        self.assertEqual(view["model_comparison"]["active_conditional_decisions"], [])

    def test_m1_f2_budget_boundaries_dynamic_not_live_quote(self):
        for budget, relation in [(500, "above"), (1905, "above"), (1906, "at_or_below"),
                                 (1907, "at_or_below"), (3000, "at_or_below")]:
            with self.subTest(budget=budget):
                view = compare_case_research({**BASE, "budget_max_cny": budget})
                self.assertEqual(check(view["criteria_comparison"], "HL-L1238W",
                                       "C-BUDGET")["relation"], relation)
                summary = next(item["result"] for item in view["model_comparison"]["comparisons"]
                               if item["dimension"] == "budget")
                self.assertIn(str(budget), summary)
                self.assertNotIn("高于1000元", summary)
                self.assertFalse(view["criteria_comparison"]["verified_live_quote_count"])
                self.assertFalse(view["purchase_recommendation_approved"])
        cleared = compare_case_research({**BASE, "budget_max_cny": None})
        self.assertFalse(any(c["criterion_id"] == "C-BUDGET" for c in
                             row(cleared["criteria_comparison"], "HL-L1238W")["checks"]))
        self.assertIn("未设置预算", next(item["result"] for item in
                                  cleared["model_comparison"]["comparisons"]
                                  if item["dimension"] == "budget"))

    def test_m1_f3_interval_relation_all_cases_no_auto_rejection(self):
        cases = {(0, 50): "below", (200, 2000): "equal", (200, 300): "within",
                 (100, 3000): "contains", (1900, 2100): "overlap", (2100, 2300): "above"}
        for bounds, expected in cases.items():
            with self.subTest(bounds=bounds):
                view = compare_case_research({**BASE, "monthly_pages_range": list(bounds)})
                self.assertEqual(check(view["criteria_comparison"], "M232dw", "C-VOLUME")["relation"],
                                 expected)
                self.assertNotIn("C-VOLUME", row(view["criteria_comparison"], "M232dw")["hard_failed"])
                self.assertIn("不是最低", next(item["result"] for item in
                                            view["model_comparison"]["comparisons"]
                                            if item["dimension"] == "low_volume_fit"))
                self.assertIn(str(bounds[0]), next(item["reason"] for item in view["reasons"]
                                                   if item["id"] == "CASE-03"))

    def test_m3_configuration_changes_result_and_expiry_degrades(self):
        config, version = load_criteria()
        self.assertEqual(len(version), 64)
        changed = deepcopy(config)
        changed["models"][0]["facts"]["scan"] = {"value": True, "source_ids": ["R6"]}
        s1 = evaluate_selection({**BASE, "requires_scan": True}, config=config)
        s2 = evaluate_selection({**BASE, "requires_scan": True}, config=changed)
        self.assertIn("C-SCAN", row(s1, "HL-L1238W")["hard_unknown"])
        self.assertNotIn("C-SCAN", row(s2, "HL-L1238W")["hard_unknown"])
        self.assertNotEqual(s1["criteria_sha256"], s2["criteria_sha256"])
        expired = deepcopy(config)
        expired["models"][1]["facts"]["scan"]["valid_until"] = "2020-01-01"
        s3 = evaluate_selection({**BASE, "requires_scan": True}, config=expired,
                                today=date(2026, 11, 15))
        self.assertIn("C-SCAN", row(s3, "M232dw")["hard_unknown"])
        self.assertEqual(check(s3, "M232dw", "C-SCAN")["evidence_state"], "withdrawn_or_expired")

    def test_m3_facts_and_rules_are_not_self_authorizing_or_executable(self):
        config, _ = load_criteria()
        for mutation in ("approval", "operator", "unattributed", "new_source", "script_field"):
            altered = deepcopy(config)
            if mutation == "approval":
                altered["purchase_recommendation_approved"] = True
            if mutation == "operator":
                altered["criteria"][0]["op"] = "__import__('os').system"
            if mutation == "unattributed":
                altered["models"][0]["facts"]["color_print"]["source_ids"] = []
            if mutation == "new_source":
                altered["criteria"][0]["source_ids"] = ["fabricated"]
            if mutation == "script_field":
                altered["criteria"][0]["python"] = "__import__('os').system('echo unsafe')"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                evaluate_selection(BASE, config=altered)

    def test_m3_small_phone_field_reuse_is_synthetic_only(self):
        # 只替换字段描述与两个假商品，无手机品牌、联网或新引擎。
        fake = {
            "schema_version": 1, "config_version": "synthetic-phone-contract-v1",
            "status": "executor_source_checked_pending_independent_review",
            "captured_on": "2026-11-15",
            "source_registry": {"TEST": {"url": "https://example.org/synthetic",
                                          "limit": "合成测试占位，无真实市场证据"}},
            "criteria": [
                {"id": "STORAGE", "why": "存储下限", "kind": "hard",
                 "activation": "provided", "op": "number_le", "user_field": "max_weight_g",
                 "product_field": "weight_g", "unit": "g", "unknown": "重量未知", "source_ids": ["TEST"]},
                {"id": "FEATURE", "why": "功能要求", "kind": "hard",
                 "activation": "true_only", "op": "boolean_equal",
                 "user_field": "needs_feature", "product_field": "feature",
                 "unit": "boolean", "unknown": "功能未知", "source_ids": ["TEST"]},
            ],
            "models": [
                {"model_id": "synthetic-A", "brand": "synthetic", "wechat_setup": "not applicable",
                 "facts": {"weight_g": {"value": 200, "unit": "g", "source_ids": ["TEST"]},
                           "feature": {"value": True, "source_ids": ["TEST"]}}},
                {"model_id": "synthetic-B", "brand": "synthetic", "wechat_setup": "not applicable",
                 "facts": {"weight_g": {"value": None, "source_ids": []},
                           "feature": {"value": False, "source_ids": ["TEST"]}}},
            ],
            "purchase_recommendation_approved": False, "transactions_enabled": False,
        }
        v = evaluate_selection({"max_weight_g": 200, "needs_feature": True}, config=fake)
        self.assertEqual(row(v, "synthetic-A")["eligibility"], "model_spec_research_only")
        self.assertEqual(row(v, "synthetic-B")["eligibility"], "excluded_by_hard_condition")
        at_boundary = check(v, "synthetic-A", "STORAGE")
        self.assertEqual(at_boundary["relation"], "at_or_below")
        with self.assertRaises(ValueError):
            evaluate_selection({"max_weight_g": "200"}, config=fake)
        mismatched = deepcopy(fake)
        mismatched["models"][0]["facts"]["weight_g"]["unit"] = "kg"
        x = evaluate_selection({"max_weight_g": 200}, config=mismatched)
        self.assertEqual(check(x, "synthetic-A", "STORAGE")["relation"], "incomparable_unit")
        self.assertIn("STORAGE", row(x, "synthetic-A")["hard_unknown"])
        self.assertFalse(v["purchase_recommendation_approved"])

    def test_m1_f4_large_prices_bad_values_do_not_crash(self):
        for bad in (10**10000, True, -1, -1.4, float("inf"), float("-inf"), float("nan"), 3.5e99):
            with self.subTest(type=type(bad).__name__):
                self.assertIsNone(_provider_price_hint(bad))
        for bad in ("NaN", "Infinity", "-1", "not_a_price", "1e999", "9"*1000):
            self.assertIsNone(_provider_price_hint(bad))
        self.assertEqual(_provider_price_hint("¥899"), "¥899")
        self.assertEqual(_provider_price_hint(399), "399")
        self.assertEqual(_provider_price_hint(399.9), "399.9")

    def test_m1_f4_bad_one_synthetic_price_preserves_good_neighbor(self):
        bundle = json.loads(SYNTHETIC_FIXTURE_PATH.read_text(encoding="utf-8"))
        products = bundle["calls"][0]["payload"]["data"][0]["sku_result"]["sku_list"]
        products[0]["sku_products"][0]["final_price"] = 10**10000
        result = ingest_haina_mcp_bundle(bundle, now=datetime(2026, 11, 16,
                                                               tzinfo=timezone.utc))
        self.assertEqual(result["status"], "synthetic_mcp_report_ingested")
        entities = [e for e in result["entities"] if e["sale_leads"]]
        prices = [lead["supplier_price_hint"] for entity in entities
                  for lead in entity["sale_leads"]]
        self.assertIn("¥909", prices)
        self.assertIn(None, prices)
        self.assertEqual(result["platform_identity_verified_count"], 0)
        self.assertFalse(result["purchase_recommendation_approved"])

    def test_m1_f5_empty_sku_is_not_a_sale_lead(self):
        bucket = _entity_bucket({}, "兄弟 HL-L1238W", "兄弟 HL-L1238W",
                                "2026-11-15T00:00:00+00:00")
        rejected = _parse_sku_entity(bucket, {"sku_result": {
            "spu_id": "", "sku_count": 0, "sku_list": []}},
            "兄弟 HL-L1238W", 1, 1, "2026-11-15T00:00:00+00:00")
        self.assertEqual(rejected, 0)
        self.assertEqual(len(bucket["sale_leads"]), 0)
        self.assertEqual(bucket["sku_empty_result_count"], 1)


if __name__ == "__main__":
    unittest.main()
