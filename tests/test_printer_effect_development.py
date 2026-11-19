"""认知增量接线：有源、有缺件、失效降级、两组公平、购买门禁。"""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.run_printer_effect_development import run, DEFAULT_CASES
from shopping_decision.printer_effect_probe import (
    derive_printer_decision_effects, pair_development_views
)
from shopping_decision.real_printer_case import compare_case_research
from shopping_decision import real_printer_case as research
from shopping_decision.selection_criteria import load_criteria, evaluate_selection


class PrinterEffectDevelopmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = __import__("json").loads(DEFAULT_CASES.read_text(encoding="utf-8"))["cases"]

    def case(self, index):
        return compare_case_research(self.samples[index]["values"])

    def test_original_has_two_grounded_issues_and_three_routes_not_checkout(self):
        result = self.case(0)
        effects = result["decision_effects"]
        names = {e["id"] for e in effects["judgments"]}
        self.assertIn("E-WECHAT-SETUP", names)
        self.assertIn("E-VOLUME-NOT-MINIMUM", names)
        self.assertIn("E-RELIABILITY-UNKNOWN", names)
        self.assertGreaterEqual(effects["supported_context_count"], 2)
        self.assertEqual(len(effects["routes"]), 3)
        self.assertEqual(len(effects["questions"]), 1)
        self.assertIn("微信打印是必须还是加分", effects["questions"][0])
        self.assertFalse(effects["purchase_recommendation_approved"])
        self.assertFalse(effects["transactions_enabled"])
        self.assertEqual(result["real_sale_identity_verified_count"], 0)

    def test_source_withdrawal_lowers_only_affected_claim(self):
        result = self.case(0)
        criteria = deepcopy(result["criteria_comparison"])
        for item in criteria["models"]:
            for check in item["checks"]:
                if check["criterion_id"] == "C-VOLUME":
                    check["evidence_state"] = "withdrawn_or_expired"
        out = derive_printer_decision_effects(
            values=self.samples[0]["values"], criteria=criteria,
            model_comparison=result["model_comparison"], wechat_preferred=True,
            reliability_required=True)
        names = {e["id"] for e in out["judgments"]}
        self.assertNotIn("E-VOLUME-NOT-MINIMUM", names)
        self.assertIn("E-WECHAT-SETUP", names)

    def test_missing_setup_source_does_not_claim_source_support(self):
        result = self.case(0)
        model_comparison = deepcopy(result["model_comparison"])
        model_comparison["sources"] = [s for s in model_comparison["sources"]
                                       if s["id"] != "R7"]
        out = derive_printer_decision_effects(
            values=self.samples[0]["values"], criteria=result["criteria_comparison"],
            model_comparison=model_comparison, wechat_preferred=True)
        self.assertNotIn("E-WECHAT-SETUP", {e["id"] for e in out["judgments"]})

    def test_color_exclusion_does_not_reactivate_hp_volume_advantage(self):
        result = self.case(2)
        self.assertNotIn("E-VOLUME-NOT-MINIMUM",
                         {e["id"] for e in result["decision_effects"]["judgments"]})
        self.assertFalse(result["criteria_comparison"]["research_eligible_models"])

    def test_no_unasked_wechat_workflow_question(self):
        result = self.case(5)
        self.assertFalse(any(e["id"] == "E-WECHAT-SETUP"
                             for e in result["decision_effects"]["judgments"]))
        self.assertFalse(result["decision_effects"]["questions"])

    def test_both_arms_share_hard_gate_and_no_dynamic_facts(self):
        for sample in self.samples:
            with self.subTest(sample=sample["id"]):
                result = compare_case_research(sample["values"])
                paired = pair_development_views(result)
                self.assertTrue(paired["same_hard_eligibility"])
                self.assertEqual(paired["direct_parameter_screen"]["questions"],
                                 paired["cognition_augmented"]["questions"])
                self.assertEqual(paired["direct_parameter_screen"]["models"][0]["checks"],
                                 paired["cognition_augmented"]["models"][0]["checks"])
                self.assertEqual(paired["newly_acquired_source_count"], 0)
                self.assertFalse(paired["incremental_decision_effect_proven"])
                self.assertFalse(paired["direct_parameter_screen"]["live_price_verified"])
                self.assertFalse(paired["purchase_recommendation_approved"])
                self.assertIsNone(paired["success_score"])
                self.assertFalse(paired["transactions_enabled"])

    def test_open_development_report_not_36_blind_gold(self):
        report = run()
        self.assertEqual(report["case_count"], 6)
        self.assertEqual(report["paired_hard_eligibility_equal_count"], 6)
        self.assertEqual(report["independent_holdout_denominator"], 0)
        self.assertFalse(report["independent_holdout_tested"])
        self.assertIsNone(report["measured_improvement"])
        self.assertEqual(report["verified_marketplace_identities"], 0)
        self.assertEqual(report["verified_regional_quotes"], 0)

    def test_current_volume_interval_and_unit_drive_claim(self):
        config, _ = load_criteria()
        config = deepcopy(config)
        config["models"][1]["facts"]["manufacturer_recommended_monthly_pages"]["value"] = [120, 980]
        config["source_registry"]["R11"]["limit"] = "synthetic interval 120-980"
        comparison = research._load_model_comparison(research.COMPARISON_PATH)
        for source in comparison["sources"]:
            if source["id"] == "R11":
                source["claim"] = "合成诊断120—980页/月，不是真实厂家变更"
        with patch.object(research, "evaluate_selection", side_effect=lambda values:
                          evaluate_selection(values, config=config, today=date(2026, 11, 16))), \
             patch.object(research, "_load_model_comparison", return_value=comparison):
            out = compare_case_research(self.samples[0]["values"])
        effect = next(e for e in out["decision_effects"]["judgments"]
                      if e["id"] == "E-VOLUME-NOT-MINIMUM")
        self.assertIn("120—980页/月", effect["claim"])
        self.assertNotIn("200—2000", effect["claim"])
        self.assertEqual(effect["current_check"]["product_value"], [120, 980])
        criteria = deepcopy(out["criteria_comparison"])
        volume = next(c for c in criteria["models"][1]["checks"] if c["criterion_id"] == "C-VOLUME")
        for value, unit in ((None, "pages_per_month"), ([120, 980], "pages_per_year")):
            with self.subTest(value=value, unit=unit):
                volume.update(product_value=value, product_unit=unit)
                effects = derive_printer_decision_effects(values=self.samples[0]["values"],
                            criteria=criteria, model_comparison=comparison)
                self.assertNotIn("E-VOLUME-NOT-MINIMUM", {e["id"] for e in effects["judgments"]})

    def test_explicit_source_validity_is_rejected_instead_of_dropped(self):
        raw = json.loads(research.COMPARISON_PATH.read_text(encoding="utf-8"))
        for fields in ({"status": "withdrawn"}, {"valid_until": "2026-11-15"},
                       {"valid_until": "bad-date"}, {"status": "active"}, {"status": None}):
            with self.subTest(fields=fields), tempfile.TemporaryDirectory() as folder:
                altered = deepcopy(raw)
                next(s for s in altered["sources"] if s["id"] == "R7").update(fields)
                path = Path(folder) / "synthetic_only.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "unsupported_model_comparison_source_validity:R7"):
                    compare_case_research(self.samples[0]["values"], comparison_path=path)
        original = self.case(0)
        altered = deepcopy(original["model_comparison"])
        next(s for s in altered["sources"] if s["id"] == "R10")["status"] = "withdrawn"
        with self.assertRaisesRegex(ValueError, "unsupported_model_comparison_source_validity:R10"):
            derive_printer_decision_effects(values=self.samples[0]["values"],
                criteria=original["criteria_comparison"], model_comparison=altered, wechat_preferred=True)

    def test_color_conflict_blocks_related_route_then_clears_without_stale_state(self):
        values = {**self.samples[0]["values"], "requirements": ["必须在家彩印", "希望微信打印"]}
        out = compare_case_research(values)["decision_effects"]
        judgment = next(e for e in out["judgments"] if e["id"] == "E-DEFER-OR-OUTSOURCE")
        route = next(r for r in out["routes"] if r["route"] == "non_purchase_alternative")
        self.assertEqual(judgment["status"], "blocked_by_user_condition_conflict")
        self.assertEqual(route["eligibility"], "blocked_by_user_condition_conflict")
        self.assertNotIn("已确认家中黑白", judgment["claim"])
        self.assertTrue(any("冲突" in q for q in out["questions"]))
        # 无关的厂家设置资料仍有据，不把冲突当全资料撤回。
        self.assertIn("E-WECHAT-SETUP", {e["id"] for e in out["judgments"]})
        clear = self.case(0)["decision_effects"]
        self.assertTrue(any(e["id"] == "E-DEFER-OR-OUTSOURCE" and "已确认家中黑白" in e["claim"]
                            for e in clear["judgments"]))

    def test_unrelated_scan_conflict_keeps_color_route_and_wechat_conflict_no_new_workflow_question(self):
        scan = compare_case_research({**self.samples[0]["values"], "requires_scan": False,
                                     "requirements": ["必须扫描"]})["decision_effects"]
        self.assertTrue(any(e["id"] == "E-DEFER-OR-OUTSOURCE"
                            and e["status"] == "user_condition_only_not_product_fact"
                            for e in scan["judgments"]))
        wechat = compare_case_research({**self.samples[0]["values"], "wechat_required": False,
                                       "requirements": ["必须微信打印"]})["decision_effects"]
        self.assertTrue(any("冲突" in q for q in wechat["questions"]))
        self.assertFalse(any("微信打印是必须还是加分" in q for q in wechat["questions"]))

    def test_review_packets_preserve_full_baseline_facts_without_cross_arm_or_gold(self):
        report = run()
        self.assertEqual(len(report["review_packets"]), 12)
        original = self.case(0)
        paired = pair_development_views(original)
        baseline = paired["direct_parameter_screen"]
        augmented = paired["cognition_augmented"]
        self.assertEqual(baseline["models"], original["criteria_comparison"]["models"])
        self.assertEqual(baseline["source_snapshot"], augmented["source_snapshot"])
        self.assertNotIn("extra_judgments", baseline)
        self.assertTrue(all("current_check" in a for a in baseline["task_output"]["answers"]))
        self.assertGreater(len(augmented["task_output"]["answers"]),
                           len(baseline["task_output"]["answers"]))
        for packet in report["review_packets"]:
            self.assertNotIn("reference", packet)
            self.assertNotIn("arm", packet)
            self.assertNotIn("cognition", packet["output"])
        self.assertTrue(all(t["baseline"]["judgment"] is None and t["cognition"]["judgment"] is None
                            for r in report["open_task_review_form"] for t in r["tasks"]))


if __name__ == "__main__":
    unittest.main()
