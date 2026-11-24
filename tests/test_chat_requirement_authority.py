"""Confirmed user conditions through the actual chat publication boundary."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

from shopping_decision.chat_bridge import render_chat, submit_message, confirmed_values
from shopping_decision.evidence_comparison import digest, SAFE_FLAGS

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = runpy.run_path(str(ROOT / "handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124/evidence/evaluator/replay_session_conditions.py"))

class RequirementAuthorityTests(unittest.TestCase):
    def case(self):
        state, bundle = FIXTURES["cases"]()["positive_control"]
        return deepcopy(state), deepcopy(bundle)

    def show(self, state, bundle):
        bundle["dialogue_version"] = state["version"]
        bundle["confirmed_values_sha256"] = digest(confirmed_values(state))
        with (patch("shopping_decision.chat_bridge._analysis", return_value={
                "recommendation": {"status": "defer"}, "verified_research_bundle": bundle}),
              patch("shopping_decision.chat_bridge.date") as clock):
            clock.today.return_value = date(2026, 11, 23)
            view = render_chat(state)
        public = json.loads(view["report_json"])["public_decision"]
        self.assertIsNotNone(public)
        for flag in SAFE_FLAGS:
            self.assertIs(public[flag], False)
        self.assertTrue(all(c["claim_id"] in view["result_text"] for c in public["claims"]))
        return {c["dimension"]: c for c in public["claims"]}, public["assessments"][0]["research_status"]

    def test_softening_does_not_hide_negative_wechat(self):
        state, bundle = self.case()
        bundle["requirements"][1]["importance"] = "soft"
        bundle["facts"][1]["value"] = False
        claims, status = self.show(state, bundle)
        self.assertEqual(claims["wechat_print"]["status"], "failed")
        self.assertEqual(claims["cost"]["status"], "met")
        self.assertEqual(status, "excluded_for_research")

    def test_omission_and_missing_fact_still_pending(self):
        state, bundle = self.case()
        bundle["requirements"].pop()
        bundle["facts"].pop()
        claims, status = self.show(state, bundle)
        self.assertEqual(claims["wechat_print"]["status"], "unknown")
        self.assertEqual(claims["cost"]["status"], "met")
        self.assertEqual(status, "pending_evidence")

    def test_specific_transfer_not_generic_or_miniprogram(self):
        state, bundle = self.case()
        state = submit_message(state, "wechat_workflow", "转App")
        bundle["facts"].append(dict(bundle["facts"][1], id="mini", dimension="wechat_miniprogram"))
        claims, status = self.show(state, bundle)
        self.assertEqual(claims["wechat_transfer_to_app"]["status"], "unknown")
        self.assertEqual(status, "pending_evidence")
        bundle["facts"].append(dict(bundle["facts"][1], id="transfer", dimension="wechat_transfer_to_app"))
        claims, status = self.show(state, bundle)
        self.assertEqual(claims["wechat_transfer_to_app"]["supporting_fact_ids"], ["transfer"])
        self.assertEqual(status, "eligible_for_research")

    def test_optional_and_withdrawal_remove_stale_hard_requirement(self):
        state, bundle = self.case()
        state = submit_message(state, "wechat_workflow", "小程序")
        bundle["facts"][1]["value"] = False
        for response in ("不是必须", "暂不确定"):
            changed = submit_message(deepcopy(state), "wechat_required", response)
            claims, status = self.show(changed, deepcopy(bundle))
            self.assertNotIn("wechat_print", claims)
            self.assertNotIn("wechat_miniprogram", claims)
            self.assertEqual(status, "eligible_for_research")
        switched = submit_message(state, "category", "手机")
        self.assertIsNone(json.loads(render_chat(switched)["report_json"])["public_decision"])

    def test_scan_required_missing_matched_and_withdrawn(self):
        state, bundle = self.case()
        state = submit_message(state, "requires_scan", "是")
        claims, status = self.show(state, bundle)
        self.assertEqual(claims["scan"]["status"], "unknown")
        self.assertEqual(status, "pending_evidence")
        bundle["facts"].append(dict(bundle["facts"][1], id="scan-fact", dimension="scan"))
        claims, status = self.show(state, bundle)
        self.assertEqual(claims["scan"]["supporting_fact_ids"], ["scan-fact"])
        self.assertEqual(status, "eligible_for_research")
        bundle["facts"][-1]["value"] = False
        claims, status = self.show(state, bundle)
        self.assertEqual(status, "excluded_for_research")
        changed = submit_message(state, "requires_scan", "否")
        claims, status = self.show(changed, bundle)
        self.assertNotIn("scan", claims)
        self.assertEqual(status, "eligible_for_research")

    def test_unmapped_initial_setup_requirement_cannot_be_invented(self):
        state, bundle = self.case()
        state = submit_message(state, "accepts_initial_setup", "不接受")
        bundle["facts"].append(dict(bundle["facts"][1], id="unmapped",
                                    dimension="initial_setup_without_app_or_scan"))
        claims, status = self.show(state, bundle)
        self.assertEqual(claims["initial_setup_without_app_or_scan"]["status"], "unknown")
        self.assertEqual(status, "pending_evidence")

if __name__ == "__main__":
    unittest.main()
