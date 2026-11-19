"""独立验收G1-G3已知反例的执行者回归保护；全部为离线合成扰动。"""
from copy import deepcopy
from datetime import date
import unittest
from unittest.mock import patch

from shopping_decision.dialogue_flow import apply_turn, compare_dialogue, new_dialogue
from shopping_decision.real_printer_case import compare_case_research
from shopping_decision.selection_criteria import evaluate_selection, load_criteria

BASE = {
    "category": "printer", "usage": "家用",
    "needs_color": False, "accepts_outsourced_color": True,
    "monthly_pages_range": [0, 50], "budget_max_cny": 1000,
    "requirements": ["希望微信打印", "可靠耐用"],
}


def model(view, name):
    return next(x for x in view["criteria_comparison"]["models"] if x["model_id"] == name)


def check(view, name, criterion):
    return next(x for x in model(view, name)["checks"] if x["criterion_id"] == criterion)


def compare_altered(config, values):
    with patch("shopping_decision.real_printer_case.evaluate_selection",
               side_effect=lambda current: evaluate_selection(
                   current, config=config, today=date(2026, 11, 15))):
        return compare_case_research(values)


class G123RepairRegressionTests(unittest.TestCase):
    def test_g1_scan_conflict_propagates_and_can_be_cleared(self):
        values = {**BASE, "requires_scan": False, "requires_auto_duplex": False,
                  "requirements": ["必须扫描"]}
        state = apply_turn(new_dialogue(), values, raw_text="合成原文必须扫描但确认不需要")
        self.assertEqual(compare_dialogue(state)["status"], "condition_conflict")
        research = compare_case_research(values)
        self.assertFalse(research["criteria_comparison"]["research_eligible_models"])
        self.assertFalse(research["model_comparison"]["active_conditional_decisions"])
        self.assertTrue(research["criteria_comparison"]["user_condition_conflicts"])
        cleared = compare_case_research({**values, "requirements": []})
        self.assertFalse(cleared["criteria_comparison"]["user_condition_conflicts"])
        self.assertTrue(cleared["criteria_comparison"]["research_eligible_models"])

    def test_g1_recognized_raw_scan_requirement_without_slot_is_not_lost(self):
        view = compare_case_research({**BASE, "requires_scan": None,
                                      "requires_auto_duplex": False,
                                      "requirements": ["必须扫描"]})
        self.assertEqual(check(view, "M232dw", "C-SCAN")["relation"], "match")
        self.assertEqual(model(view, "HL-L1238W")["eligibility"], "pending_hard_evidence")
        self.assertIn("requires_scan", view["criteria_comparison"]["normalized_from_requirement_text"])

    def test_g1_raw_miniprogram_and_unmodeled_wireless_fail_closed(self):
        wechat = compare_case_research({
            **BASE, "wechat_required": None, "wechat_workflow": "unknown",
            "requirements": ["必须微信小程序打印"], "device_deployment_region": "日本",
        })
        self.assertTrue(all(model(wechat, name)["eligibility"] == "pending_hard_evidence"
                            for name in ("M232dw", "HL-L1238W")))
        self.assertIn("wechat_required", wechat["criteria_comparison"]["normalized_from_requirement_text"])
        wireless = compare_case_research({
            **BASE, "requirements": ["必须无线打印"], "requires_wireless": None,
            "requires_scan": False, "requires_auto_duplex": False,
        })
        self.assertFalse(wireless["criteria_comparison"]["research_eligible_models"])
        self.assertEqual(wireless["criteria_comparison"]["unmodeled_hard_requirements"], ["wireless"])
        self.assertEqual(len(wireless["criteria_comparison"]["pending_models"]), 2)

    def test_g1r1_equivalent_wechat_hard_workflows_and_revocation(self):
        # 同一原话已识别硬要求，不依赖第二个勾选槽位。
        cases = (
            ("必须微信打印", "unknown", None, "workflow_unconfirmed"),
            ("必须微信小程序打印", "miniprogram", "日本", "deployment_outside_verified_scope"),
            ("必须微信打印", "transfer_to_app", None, "other_workflow_unverified"),
        )
        for raw, workflow, region, relation in cases:
            with self.subTest(raw=raw, workflow=workflow):
                values = {**BASE, "requirements": [raw],
                          "wechat_workflow": workflow,
                          "device_deployment_region": region,
                          "requires_scan": False, "requires_auto_duplex": False}
                implicit = compare_case_research({**values, "wechat_required": None})
                explicit = compare_case_research({**values, "wechat_required": True})
                left, right = implicit["criteria_comparison"], explicit["criteria_comparison"]
                self.assertEqual(left["normalized_required"], right["normalized_required"])
                self.assertEqual(left["research_eligible_models"], [])
                self.assertEqual(left["pending_models"], right["pending_models"])
                self.assertEqual(len(left["pending_models"]), 2)
                self.assertFalse(any(
                    d["model"] in ("M232dw", "HL-L1238W")
                    for d in implicit["model_comparison"]["active_conditional_decisions"]))
                for name in ("M232dw", "HL-L1238W"):
                    self.assertEqual(check(implicit, name, "C-WECHAT")["relation"], relation)
                    self.assertEqual(check(explicit, name, "C-WECHAT")["relation"], relation)
                self.assertFalse(implicit["purchase_recommendation_approved"])
                self.assertFalse(implicit["transactions_enabled"])

        # 明确否定但保留原话时属于冲突；原话和确认同步撤销后恢复。
        values = {**BASE, "requirements": ["必须微信打印"],
                  "wechat_workflow": "transfer_to_app",
                  "requires_scan": False, "requires_auto_duplex": False}
        conflict = compare_case_research({**values, "wechat_required": False})
        self.assertTrue(conflict["criteria_comparison"]["user_condition_conflicts"])
        self.assertFalse(conflict["criteria_comparison"]["research_eligible_models"])
        cleared = compare_case_research({**values, "requirements": [], "wechat_required": False})
        self.assertFalse(cleared["criteria_comparison"]["user_condition_conflicts"])
        self.assertEqual(len(cleared["criteria_comparison"]["research_eligible_models"]), 2)
        for name in ("M232dw", "HL-L1238W"):
            self.assertFalse(any(c["criterion_id"] == "C-WECHAT" for c in
                                 model(cleared, name)["checks"]))
        self.assertFalse(cleared["purchase_recommendation_approved"])

    def test_g1_unknown_hard_requirement_stays_pending_not_recommended(self):
        values = {**BASE, "requirements": ["必须A3幅面"],
                  "requires_scan": False, "requires_auto_duplex": False}
        view = compare_case_research(values)
        self.assertFalse(view["criteria_comparison"]["research_eligible_models"])
        self.assertEqual(len(view["criteria_comparison"]["pending_models"]), 2)
        self.assertFalse(view["model_comparison"]["active_conditional_decisions"])
        self.assertTrue(any("A3" in q for q in view["criteria_comparison"]["questions"]))

    def test_g2_withdrawn_scan_downgrades_all_relevant_explanations(self):
        original, _ = load_criteria()
        changed = deepcopy(original)
        changed["models"][1]["facts"]["scan"]["status"] = "withdrawn"
        view = compare_altered(changed, {**BASE, "requires_scan": True})
        self.assertEqual(check(view, "M232dw", "C-SCAN")["relation"], "unknown")
        self.assertEqual(model(view, "M232dw")["eligibility"], "pending_hard_evidence")
        self.assertFalse(any(d["id"] == "DEC-01" for d in
                             view["model_comparison"]["active_conditional_decisions"]))
        self.assertIn("撤回", next(d["reason"] for d in view["model_comparison"]["conditional_decisions"]
                                  if d["id"] == "DEC-01"))
        self.assertIn("撤回", next(d["result"] for d in view["model_comparison"]["comparisons"]
                                  if d["dimension"] == "scan_copy"))
        self.assertIn("撤回", next(d["reason"] for d in view["reasons"] if d["id"] == "CASE-04"))
        restored = compare_case_research({**BASE, "requires_scan": True})
        self.assertTrue(any(d["id"] == "DEC-01" for d in
                            restored["model_comparison"]["active_conditional_decisions"]))

    def test_g2_expired_price_must_not_assert_current_relation(self):
        original, _ = load_criteria()
        changed = deepcopy(original)
        changed["models"][0]["facts"]["manufacturer_suggested_retail_cny"]["valid_until"] = "2026-11-14"
        view = compare_altered(changed, {**BASE, "requires_scan": False,
                                         "requires_auto_duplex": False})
        self.assertEqual(check(view, "HL-L1238W", "C-BUDGET")["relation"], "unknown")
        snippets = [
            next(x["result"] for x in view["model_comparison"]["comparisons"] if x["dimension"] == "budget"),
            next(x["reason"] for x in view["reasons"] if x["id"] == "CASE-06"),
            next(x["reason"] for x in view["model_comparison"]["conditional_decisions"] if x["id"] == "DEC-02"),
        ]
        self.assertTrue(all("过期" in x and "1906元不高于" not in x
                            and "1906元高于" not in x for x in snippets))

    def test_g2_withdrawn_monthly_volume_preserves_user_confirmation(self):
        original, _ = load_criteria()
        changed = deepcopy(original)
        changed["models"][1]["facts"]["manufacturer_recommended_monthly_pages"]["status"] = "withdrawn"
        view = compare_altered(changed, BASE)
        self.assertEqual(check(view, "M232dw", "C-VOLUME")["relation"], "unknown")
        snippets = [
            next(x["result"] for x in view["model_comparison"]["comparisons"] if x["dimension"] == "low_volume_fit"),
            next(x["reason"] for x in view["reasons"] if x["id"] == "CASE-03"),
        ]
        self.assertTrue(all("0—50" in x and "已确认" in x
                            and "本轮月印量未确认" not in x for x in snippets))

    def test_g3_miniprogram_deployment_region_does_not_use_delivery_region(self):
        for region in (None, "日本", "新加坡"):
            with self.subTest(region=region):
                view = compare_case_research({
                    **BASE, "wechat_required": True, "wechat_workflow": "miniprogram",
                    "device_deployment_region": region, "delivery_region": "中国大陆",
                })
                self.assertEqual(len(view["criteria_comparison"]["pending_models"]), 2)
                self.assertFalse(view["criteria_comparison"]["research_eligible_models"])
                # DEC-03是跨地区风险提示，可保持活跃；不得将任何具体机型称为可用候选。
                self.assertFalse(any(
                    decision["model"] in ("HL-L1238W", "M232dw")
                    for decision in view["model_comparison"]["active_conditional_decisions"]))
                for name in ("HL-L1238W", "M232dw"):
                    self.assertNotEqual(check(view, name, "C-WECHAT")["relation"], "match")
        mainland = compare_case_research({
            **BASE, "wechat_required": True, "wechat_workflow": "miniprogram",
            "device_deployment_region": "中国大陆",
        })
        for name in ("HL-L1238W", "M232dw"):
            self.assertEqual(check(mainland, name, "C-WECHAT")["relation"], "match")
            self.assertFalse(check(mainland, name, "C-WECHAT")["regional_service_verified"])
        self.assertFalse(mainland["purchase_recommendation_approved"])


if __name__ == "__main__":
    unittest.main()
