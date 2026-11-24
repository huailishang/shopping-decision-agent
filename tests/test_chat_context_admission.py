"""Offline admission checks through the real public chat boundary."""
from copy import deepcopy
from datetime import date
import json
import unittest
from unittest.mock import patch

from shopping_decision.chat_bridge import render_chat, submit_message
from test_chat_claim_binding import FROZEN_R2, rebind
from test_publication_entry import analysis_with


class ContextAdmissionTests(unittest.TestCase):
    def fixture(self, name="mixed_quote_and_wrong_usage_region"):
        case = deepcopy(FROZEN_R2[name])
        return case["state"], case["analysis"]["verified_research_bundle"]

    def render(self, state, bundle):
        with (patch("shopping_decision.chat_bridge.date") as clock,
              patch("shopping_decision.chat_bridge._analysis",
                    return_value=analysis_with(bundle))):
            clock.today.return_value = date(2026, 11, 23)
            view = render_chat(state)
        report = json.loads(view["report_json"])
        for flag in ("purchase_recommendation_approved", "transactions_enabled",
                     "live_price_verified"):
            self.assertIs(report[flag], False)
        self.assertNotIn("立刻下单", view["result_text"])
        public = report["public_decision"]
        if public:
            for flag in ("purchase_recommendation_approved", "transactions_enabled",
                         "live_price_verified", "wechat_reuse_verified",
                         "real_user_effect_verified"):
                self.assertIs(public[flag], False)
            for claim in public["claims"]:
                self.assertIn(claim["claim_id"], view["result_text"])
        else:
            self.assertIn("待核研究", view["result_text"])
            self.assertNotIn("核验命题ID", view["result_text"])
        return view, report

    def claims(self, state, bundle):
        view, report = self.render(state, bundle)
        return {(c["candidate_id"], c["requirement_id"]): c
                for c in report["public_decision"]["claims"]}

    def japan(self):
        state, bundle = self.fixture()
        bundle["sources"][1]["scope_region"] = "日本"
        bundle["facts"][1]["scope_region"] = "日本"
        return state, bundle

    def test_quote_role_and_units_cannot_change_function_region(self):
        for correct in (False, True):
            state, bundle = self.japan() if correct else self.fixture()
            for unit, value in (("CNY", 900), ("bool", True)):
                contaminated = deepcopy(bundle)
                quote = deepcopy(bundle["facts"][0])
                quote.update(id="new_quote", dimension="wechat_print",
                             unit=unit, value=value)
                contaminated["facts"].insert(0, quote)
                contaminated["requirements"].reverse()
                c = self.claims(state, contaminated)
                self.assertEqual((c["a", "cost"]["status"], c["a", "cost"]["scope"]["region"]),
                                 ("met", "河南"))
                use = c["a", "use"]
                self.assertEqual((use["status"], use["scope"]["region"]),
                                 ("met" if correct else "unknown", "日本"))
                self.assertEqual(use["supporting_fact_ids"], ["use_fact"] if correct else [])
                if correct:
                    self.assertEqual(use["source_audit"][0]["source_id"], "use_doc")

    def test_multiple_candidates_do_not_share_feature_or_quote(self):
        state, bundle = self.japan()
        bundle["candidates"].insert(0, {"id": "another"})
        source = deepcopy(bundle["sources"][0])
        source.update(id="other_source", scope_models=["another"], quote_sku="other",
                      observed_at="2026-11-24T08:00:00+08:00")
        bundle["sources"].append(source)
        fact = deepcopy(bundle["facts"][0])
        fact.update(id="other_price", candidate_id="another", source_id="other_source")
        bundle["facts"].append(fact)
        c = self.claims(state, bundle)
        self.assertEqual([c[k]["status"] for k in
                          (("a","cost"),("a","use"),("another","cost"),("another","use"))],
                         ["met", "met", "unknown", "unknown"])
        view, report = self.render(state, bundle)
        self.assertEqual([x["candidate_id"] for x in report["public_decision"]["assessments"]],
                         ["another", "a"])
        bundle["facts"] = [x for x in bundle["facts"] if x["id"] != "use_fact"]
        self.assertEqual(self.claims(state, bundle)["a","use"]["status"], "unknown")

    def test_full_structure_rejected_before_filtering(self):
        for mutate in (
            lambda b: b["requirements"][1].update(id="cost"),
            lambda b: b["sources"][0].update(id=["bad"]),
            lambda b: b["candidates"].append({"id": "a"}),
            lambda b: b["facts"].append(dict(b["facts"][0], dimension="unused")),
            lambda b: b["facts"].append(dict(b["facts"][0], id="dangling",
                                              dimension="unused", source_id="absent")),
            lambda b: b["facts"].append(dict(b["facts"][0], id="dangling",
                                              dimension="unused", candidate_id="absent")),
            lambda b: b["facts"].extend(dict(b["facts"][0], id=f"unrelated-{i}",
                                             dimension=f"other-{i}") for i in range(99)),
        ):
            state, bundle = self.japan()
            mutate(bundle)
            view, report = self.render(state, bundle)
            self.assertIsNone(report["public_decision"])
            self.assertEqual(report["research_result"]["verified_research_bundle"], bundle)

    def test_price_amount_role_and_scope(self):
        for changes in ({"value": -1}, {"value": "-0.01"}, {"value": "Infinity"},
                        {"value": True}, {"value": "NaN"}, {"kind": "discount"},
                        {"kind": "official_feature"}, {"evidence_role": "discount"}):
            state, bundle = self.fixture("delivery_positive")
            bundle["facts"][0].update(changes)
            self.assertEqual(self.claims(state, bundle)["a","cost"]["status"], "unknown")
        for amount, expected in ((900, "met"), (1300, "failed")):
            state, bundle = self.fixture("delivery_positive")
            bundle["facts"][0]["value"] = amount
            c = self.claims(state, bundle)["a","cost"]
            self.assertEqual(c["status"], expected)
            self.assertEqual(c["supporting_fact_ids"], ["f"])
            self.assertEqual(c["source_audit"][0]["source_id"], "s")
        state, bundle = self.fixture("delivery_positive")
        for answer in ("含额外耗材", "主机含运费及必要支出"):
            changed = submit_message(state, "budget_scope", answer)
            self.assertEqual(self.claims(changed, rebind(deepcopy(bundle), changed))
                             ["a","cost"]["status"], "unknown")

    def test_nonfinite_literal_bundle_is_audit_only(self):
        state, bundle = self.fixture("delivery_positive")
        bundle["facts"][0]["value"] = float("inf")
        self.assertIsNone(self.render(state, bundle)[1]["public_decision"])

    def test_insufficient_or_revoked_price_does_not_erase_other_condition(self):
        for patch_source in ({"type": "official_search_index_only"},
                             {"valid_until": "2026-11-19"}, {"revoked": True},
                             {"quote_region": "中国大陆"}):
            state, bundle = self.japan()
            bundle["sources"][0].update(patch_source)
            c = self.claims(state, bundle)
            self.assertEqual(c["a","cost"]["status"], "unknown")
            self.assertEqual(c["a","use"]["status"], "met")

    def test_changed_dialogue_does_not_publish_stale_bundle(self):
        state, bundle = self.japan()
        changed = submit_message(state, "budget_max_cny", "800")
        self.assertIsNone(self.render(changed, bundle)[1]["public_decision"])
        changed_bundle = rebind(deepcopy(bundle), changed)
        changed_bundle["requirements"][0]["value"] = 800
        c = self.claims(changed, changed_bundle)
        self.assertEqual(c["a","cost"]["status"], "failed")
        self.assertEqual(c["a","use"]["status"], "met")
