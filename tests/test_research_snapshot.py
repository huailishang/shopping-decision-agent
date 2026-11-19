"""新研究接口的通用性与保护检查：都是合成契约测试，不是第二品类推荐。"""
import copy
import unittest
from datetime import date

from shopping_decision.research_snapshot import compare_research_snapshot
from shopping_decision.selection_criteria import load_criteria


class ResearchSnapshotContractTests(unittest.TestCase):
    def setUp(self):
        self.config, _ = load_criteria()
        self.values = {
            "category": "printer",
            "needs_color": False,
            "accepts_outsourced_color": True,
            "monthly_pages_range": [0, 50],
            "budget_max_cny": 1000,
            "wechat_required": True,
            "wechat_workflow": "miniprogram",
            "device_deployment_region": None,
        }

    def test_default_all_candidates_and_read_only(self):
        result = compare_research_snapshot(self.values)
        self.assertEqual(result["total_candidate_count"], len(self.config["models"]))
        self.assertFalse(result["purchase_recommendation_approved"])
        self.assertFalse(result["transactions_enabled"])
        self.assertEqual(result["verified_live_quote_count"], 0)
        self.assertEqual(len(result["all_candidates"]), len(self.config["models"]))
        self.assertTrue(result["criteria_sha256"])
        self.assertTrue(result["evidence_missing"])

    def test_renamed_models_and_source_ids_are_data_not_code(self):
        original = compare_research_snapshot(self.values, config=self.config)
        config = copy.deepcopy(self.config)
        for row in config["models"]:
            row["model_id"] = "ALT-" + row["model_id"]
        source_id = next(iter(config["source_registry"]))
        config["source_registry"]["ALT-SOURCE"] = config["source_registry"].pop(source_id)
        for rule in config["criteria"]:
            rule["source_ids"] = ["ALT-SOURCE" if x == source_id else x
                                  for x in rule["source_ids"]]
        for model in config["models"]:
            model["source_ids"] = ["ALT-SOURCE" if x == source_id else x
                                   for x in model.get("source_ids", [])]
            for fact in model["facts"].values():
                fact["source_ids"] = ["ALT-SOURCE" if x == source_id else x
                                      for x in fact["source_ids"]]
        changed = compare_research_snapshot(self.values, config=config)
        self.assertEqual({x["model_id"].removeprefix("ALT-"): x["eligibility"]
                          for x in changed["all_candidates"]},
                         {x["model_id"]: x["eligibility"]
                          for x in original["all_candidates"]})
        self.assertEqual(changed["total_candidate_count"], original["total_candidate_count"])

    def test_order_add_remove_and_display_limit_not_evaluation_limit(self):
        config = copy.deepcopy(self.config)
        config["models"] = list(reversed(config["models"]))
        reversed_result = compare_research_snapshot(self.values, config=config)
        self.assertEqual(reversed_result["all_candidates"][0]["model_id"],
                         config["models"][0]["model_id"])
        for i in (3, 4):
            added = copy.deepcopy(config["models"][0])
            added["model_id"] = "MODEL-" + str(i)
            config["models"].append(added)
        result = compare_research_snapshot(self.values, config=config)
        self.assertEqual(result["total_candidate_count"], 4)
        self.assertEqual(len(result["displayed_candidates"]), 3)
        self.assertEqual(len(result["hidden_candidates"]), 1)
        self.assertEqual(result["hidden_candidates"][0]["model_id"], "MODEL-4")
        config["models"] = config["models"][1:]
        removed = compare_research_snapshot(self.values, config=config)
        self.assertEqual(removed["total_candidate_count"], 3)

    def test_neutral_category_without_wechat_placeholder(self):
        neutral = {
            "schema_version": 1, "config_version": "synthetic-neutral-1",
            "status": "executor_source_checked_pending_independent_review",
            "category": "kettle", "captured_on": "2026-11-15",
            "market_scope": "synthetic contract only",
            "source_registry": {"SRC-NEUTRAL": {
                "type": "synthetic", "group": "synthetic",
                "url": "https://example.com/synthetic-contract-only",
                "checked_on": "2026-11-15", "limit": "not real product evidence"}},
            "criteria": [{
                "id": "NEUTRAL-LID", "why": "synthetic property",
                "user_field": "requires_lid", "product_field": "lid",
                "op": "boolean_equal", "activation": "true_only", "kind": "hard",
                "unit": "boolean", "source_ids": ["SRC-NEUTRAL"],
                "unknown": "synthetic property unknown"}],
            "models": [{
                "model_id": "K-1", "brand": "synthetic",
                "source_ids": ["SRC-NEUTRAL"], "facts": {
                    "lid": {"value": True, "unit": "boolean",
                            "source_ids": ["SRC-NEUTRAL"]}}},
                {"model_id": "K-2", "brand": "synthetic",
                 "facts": {"lid": {"value": None, "unit": "boolean",
                                   "source_ids": []}}}],
            "purchase_recommendation_approved": False,
            "transactions_enabled": False,
        }
        result = compare_research_snapshot({"category": "kettle", "requires_lid": True},
                                           config=neutral, today=date(2026, 11, 16))
        self.assertEqual(result["total_candidate_count"], 2)
        self.assertEqual(result["all_candidates"][0]["eligibility"], "model_spec_research_only")
        self.assertEqual(result["all_candidates"][1]["eligibility"], "pending_hard_evidence")
        self.assertEqual(result["all_candidates"][0]["checks"][0]["criterion_id"], "NEUTRAL-LID")
        self.assertFalse(any("微信" in str(row) or "印量" in str(row)
                             for row in result["judgments"]))

    def test_withdrawn_fact_and_units_never_become_positive(self):
        config = copy.deepcopy(self.config)
        for model in config["models"]:
            for fact in model["facts"].values():
                if fact.get("value") is not None:
                    fact["status"] = "withdrawn"
        result = compare_research_snapshot(self.values, config=config)
        self.assertFalse(result["judgments"])
        self.assertEqual(result["verified_platform_identity_count"], 0)

    def test_invalid_source_or_unsigned_candidate_is_rejected(self):
        config = copy.deepcopy(self.config)
        config["models"][0]["facts"]["color_print"]["source_ids"] = ["FAKE-SOURCE"]
        with self.assertRaises(ValueError):
            compare_research_snapshot(self.values, config=config)

    def test_r1_rejects_both_cross_category_directions(self):
        with self.assertRaisesRegex(ValueError, "category_mismatch"):
            compare_research_snapshot({**self.values, "category": "kettle"})
        neutral = copy.deepcopy(self.config)
        neutral["category"] = "kettle"
        with self.assertRaisesRegex(ValueError, "category_mismatch"):
            compare_research_snapshot(self.values, config=neutral)
        valid = compare_research_snapshot(self.values)
        self.assertEqual(valid["category"], "printer")
        self.assertEqual(valid["category_binding"], "material_explicit")

    def test_r1_legacy_without_category_cannot_masquerade_as_a_category(self):
        old = copy.deepcopy(self.config)
        old.pop("category")
        inputs = {k: v for k, v in self.values.items() if k != "category"}
        result = compare_research_snapshot(inputs, config=old)
        self.assertIsNone(result["category"])
        self.assertEqual(result["category_binding"], "legacy_unscoped")
        with self.assertRaisesRegex(ValueError, "unscoped_legacy_selection_category"):
            compare_research_snapshot(self.values, config=old)
        # An older caller with no category can still use an explicitly scoped file.
        self.assertEqual(compare_research_snapshot(inputs)["category"], "printer")

    def test_r2_unanswered_deployment_is_a_user_action(self):
        result = compare_research_snapshot(self.values)
        self.assertEqual(result["next_action"], "clarify_user_conditions")
        self.assertTrue(any("部署" in q for q in result["necessary_user_questions"]))
        self.assertTrue(any(q["field"] == "device_deployment_region" and q["kind"] == "user_input"
                            for q in result["question_items"]))

    def test_r2_answered_region_is_evidence_problem_not_repeat_question(self):
        result = compare_research_snapshot({**self.values, "device_deployment_region": "日本",
                                            "budget_scope": "device_delivered"})
        self.assertFalse(any("尚未确认" in q for q in result["necessary_user_questions"]))
        self.assertEqual(result["next_action"], "verify_missing_hard_model_evidence")
        self.assertTrue(any(q["field"] == "regional_wechat_service"
                            and q["kind"] == "external_evidence"
                            for q in result["question_items"]))

    def test_r2_conflict_is_user_clarification(self):
        from shopping_decision.real_printer_case import compare_case_research
        result = compare_case_research({**self.values, "requirements": ["必须在家打印彩色"]})
        snap = result["shared_research_snapshot"]
        self.assertEqual(snap["next_action"], "resolve_user_condition_conflict")
        self.assertTrue(any(q["kind"] == "user_conflict" for q in snap["question_items"]))
        self.assertTrue(snap["necessary_user_questions"])

    def test_r2_missing_product_fact_does_not_create_user_question(self):
        config = copy.deepcopy(self.config)
        for model in config["models"]:
            model["facts"]["color_print"]["status"] = "withdrawn"
        values = {"category": "printer", "needs_color": True}
        result = compare_research_snapshot(values, config=config)
        self.assertEqual(result["next_action"], "verify_missing_hard_model_evidence")
        self.assertFalse(result["necessary_user_questions"])
        self.assertFalse(result["judgments"])
        self.assertFalse(result["transactions_enabled"])


    def test_r2_unknown_region_markers_are_unanswered(self):
        from shopping_decision.selection_criteria import is_unanswered_device_deployment_region
        for marker in (None, "", "   ", "未知", "待确认", " 未确认 ",
                       "不清楚", "unknown", " UNKNOWN ", "ＴＢＤ"):
            with self.subTest(region=marker):
                self.assertTrue(is_unanswered_device_deployment_region(marker))
                result = compare_research_snapshot({
                    **self.values, "budget_scope": "device_delivered",
                    "device_deployment_region": marker,
                })
                self.assertEqual(result["next_action"], "clarify_user_conditions")
                self.assertTrue(any(q["field"] == "device_deployment_region"
                                    and q["kind"] == "user_input"
                                    for q in result["question_items"]))
                self.assertFalse(result["purchase_recommendation_approved"])

    def test_r2_unmapped_real_place_is_not_treated_as_non_answer(self):
        from shopping_decision.selection_criteria import is_unanswered_device_deployment_region
        for region in ("日本", "中国大陆", "悉尼", "Copenhagen"):
            with self.subTest(region=region):
                self.assertFalse(is_unanswered_device_deployment_region(region))
                result = compare_research_snapshot({
                    **self.values, "budget_scope": "device_delivered",
                    "device_deployment_region": region,
                })
                self.assertFalse(any(q["field"] == "device_deployment_region"
                                     and q["kind"] == "user_input"
                                     for q in result["question_items"]))
                self.assertFalse(result["transactions_enabled"])


if __name__ == "__main__":
    unittest.main()
