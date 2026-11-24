"""Contract-specific main-chat binding regressions (offline, no platform/model calls)."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from shopping_decision.chat_bridge import confirmed_values, render_chat, submit_message
from shopping_decision.evidence_comparison import digest
from test_publication_entry import configured, typed, analysis_with


ROOT = Path(__file__).resolve().parents[1]
FROZEN_R2 = json.loads((ROOT / "handoffs/evaluator_executor"
    / "GENERIC-PUBLIC-ENTRY-COVERAGE-20261120/evidence/evaluator-r2/chat-inputs.json")
    .read_text(encoding="utf-8"))


def rebind(bundle, state):
    bundle["dialogue_version"] = state["version"]
    bundle["confirmed_values_sha256"] = digest(confirmed_values(state))
    return bundle


class ChatClaimBindingTests(unittest.TestCase):
    def show(self, state, bundle):
        with (patch("shopping_decision.chat_bridge.date") as clock,
              patch("shopping_decision.chat_bridge._analysis",
                    return_value=analysis_with(bundle))):
            clock.today.return_value = date(2026, 11, 23)
            view = render_chat(state)
        report = json.loads(view["report_json"])
        self.assertFalse(report["purchase_recommendation_approved"])
        self.assertFalse(report["transactions_enabled"])
        self.assertFalse(report["live_price_verified"])
        self.assertNotIn("立刻下单", view["result_text"])
        return view, report["public_decision"]

    def fixture(self, name):
        case = deepcopy(FROZEN_R2[name])
        return case["state"], case["analysis"]["verified_research_bundle"]

    def statuses(self, published):
        return {c["requirement_id"]: c["status"] for c in published["claims"]} if published else {}

    def test_wrong_dimension_budget_and_order_never_relaxes_purchase(self):
        state, bundle = self.fixture("budget_on_other_dimension")
        for rows in (bundle["requirements"], list(reversed(bundle["requirements"]))):
            candidate = deepcopy(bundle)
            candidate["requirements"] = deepcopy(rows)
            view, public = self.show(state, candidate)
            self.assertNotIn("1300 ≤ 1500", view["result_text"])
            self.assertNotEqual(self.statuses(public).get("cost"), "met")
        candidate = deepcopy(bundle)
        candidate["requirements"] = [bundle["requirements"][0]]
        self.assertFalse(self.statuses(self.show(state, candidate)[1]))
        candidate["requirements"] = [deepcopy(bundle["requirements"][1])]
        candidate["requirements"][0]["dimension"] = "renamed_device_cost"
        self.assertFalse(self.statuses(self.show(state, candidate)[1]))

    def test_purchase_budget_positive_negative_and_claim_id(self):
        state = configured()
        bundle = typed(state)
        view, public = self.show(state, bundle)
        self.assertEqual(self.statuses(public)["cost"], "met")
        self.assertIn(public["claims"][0]["claim_id"], view["result_text"])
        bundle["facts"][0]["value"] = 1300
        view, public = self.show(state, bundle)
        self.assertEqual(self.statuses(public)["cost"], "failed")
        self.assertIn("1300 ≤ 1000", view["result_text"])
        bundle["requirements"][0]["value"] = 1500
        self.assertNotEqual(self.statuses(self.show(state, bundle)[1]).get("cost"), "met")

    def test_consumables_or_delivery_scope_without_total_is_pending(self):
        for scope in ("含额外耗材", "主机含运费及必要支出"):
            state = submit_message(configured(), "budget_scope", scope)
            bundle = typed(state)
            view, public = self.show(state, bundle)
            self.assertEqual(self.statuses(public)["cost"], "unknown")
            self.assertNotIn("900 ≤ 1000", view["result_text"])

    def test_mixed_quote_and_wrong_usage_region(self):
        state, bundle = self.fixture("mixed_quote_and_wrong_usage_region")
        view, public = self.show(state, bundle)
        self.assertEqual(self.statuses(public), {"cost": "met", "use": "unknown"})
        self.assertIn("900 ≤ 1000", view["result_text"])
        self.assertNotIn("条件2：根据纳入的结构化事实", view["result_text"])
        self.assertEqual([c["scope"]["region"] for c in public["claims"]],
                         ["河南", "日本"])
        self.assertFalse(public["transactions_enabled"])

    def test_feature_region_is_independent_of_quote_presence(self):
        state, bundle = self.fixture("mixed_quote_and_wrong_usage_region")
        feature = bundle["sources"][1]
        feature["scope_region"] = "日本"
        bundle["facts"][1]["scope_region"] = "日本"
        view, public = self.show(state, bundle)
        self.assertEqual(self.statuses(public), {"cost": "met", "use": "met"})
        self.assertIn("核验命题ID", view["result_text"])
        without_quote = deepcopy(bundle)
        without_quote["facts"] = [f for f in bundle["facts"] if f["kind"] != "live_quote"]
        view, public = self.show(state, without_quote)
        self.assertEqual(self.statuses(public), {"cost": "unknown", "use": "met"})
        self.assertNotIn("900 ≤ 1000", view["result_text"])
        feature["scope_region"] = "河南"
        bundle["facts"][1]["scope_region"] = "河南"
        self.assertEqual(self.statuses(self.show(state, bundle)[1]),
                         {"cost": "met", "use": "unknown"})

    def test_quote_delivery_region_exact_and_unknown_when_missing(self):
        state, bundle = self.fixture("delivery_positive")
        self.assertEqual(self.statuses(self.show(state, bundle)[1])["cost"], "met")
        bundle["sources"][0]["scope_region"] = "中国大陆"
        bundle["sources"][0]["quote_region"] = "中国大陆"
        self.assertEqual(self.statuses(self.show(state, bundle)[1])["cost"], "unknown")
        bundle["sources"][0]["scope_region"] = "河南"
        bundle["sources"][0]["quote_region"] = "河南"
        no_delivery = configured()
        rebind(bundle, no_delivery)
        self.assertEqual(self.statuses(self.show(no_delivery, bundle)[1])["cost"], "unknown")

    def test_quote_future_local_or_utc_day_is_pending(self):
        state, bundle = self.fixture("delivery_positive")
        source = bundle["sources"][0]
        for timestamp, captured in (
            ("2026-11-24T00:30:00+14:00", "2026-11-23"),
            ("2026-11-23T23:30:00-12:00", "2026-11-23"),
        ):
            source["observed_at"], source["captured_on"] = timestamp, captured
            self.assertEqual(self.statuses(self.show(state, bundle)[1])["cost"], "unknown")
        source["observed_at"] = "2026-11-22T23:30:00-12:00"
        source["captured_on"] = "2026-11-23"
        self.assertEqual(self.statuses(self.show(state, bundle)[1])["cost"], "met")

    def test_quote_capture_and_validity_order(self):
        state, bundle = self.fixture("delivery_positive")
        source = bundle["sources"][0]
        source["observed_at"] = "2026-11-19T09:00:00+08:00"
        source["captured_on"] = "2026-11-18"
        self.assertEqual(self.statuses(self.show(state, bundle)[1])["cost"], "unknown")
        source["captured_on"] = "2026-11-19"
        self.assertEqual(self.statuses(self.show(state, bundle)[1])["cost"], "met")
        source["captured_on"] = "2026-11-25"
        self.assertEqual(self.statuses(self.show(state, bundle)[1])["cost"], "unknown")
        source["captured_on"] = "2026-11-19"
        source["valid_until"] = "2026-11-18"
        self.assertEqual(self.statuses(self.show(state, bundle)[1])["cost"], "unknown")
        source["valid_until"] = "2026-11-22"
        self.assertEqual(self.statuses(self.show(state, bundle)[1])["cost"], "unknown")

    def test_invalid_second_candidate_quote_does_not_hide_valid_first(self):
        state, bundle = self.fixture("delivery_positive")
        bundle["candidates"].append({"id": "b"})
        invalid_source = deepcopy(bundle["sources"][0])
        invalid_source.update(id="s-b", observed_at="2026-11-24T08:00:00+08:00")
        bundle["sources"].append(invalid_source)
        invalid_fact = deepcopy(bundle["facts"][0])
        invalid_fact.update(id="f-b", candidate_id="b", source_id="s-b", value=800)
        bundle["facts"].append(invalid_fact)
        _, public = self.show(state, bundle)
        self.assertEqual({claim["candidate_id"]: claim["status"]
                          for claim in public["claims"]}, {"a": "met", "b": "unknown"})

    def test_shared_source_does_not_borrow_region_or_price_validity(self):
        state, bundle = self.fixture("mixed_quote_and_wrong_usage_region")
        bundle["facts"][1]["source_id"] = bundle["facts"][0]["source_id"]
        bundle["facts"][1]["scope_region"] = "日本"
        self.assertEqual(self.statuses(self.show(state, bundle)[1]),
                         {"cost": "met", "use": "unknown"})
        # An invalid quote is not allowed to invalidate otherwise valid
        # independently-sourced usage evidence in the same research package.
        independent = self.fixture("mixed_quote_and_wrong_usage_region")[1]
        independent["sources"][1]["scope_region"] = "日本"
        independent["facts"][1]["scope_region"] = "日本"
        independent["sources"][0]["valid_until"] = "2026-11-19"
        self.assertEqual(self.statuses(self.show(state, independent)[1]),
                         {"cost": "unknown", "use": "met"})


if __name__ == "__main__":
    unittest.main()
