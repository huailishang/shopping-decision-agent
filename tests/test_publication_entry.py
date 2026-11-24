"""Actual main-chat publication tests: only gate output is allowed as verified text."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from shopping_decision.chat_bridge import (new_dialogue, submit_message, render_chat,
                                           confirmed_values)
from shopping_decision.evidence_comparison import digest
from test_model_comparison import bundle
from scripts.audit_model_history_readonly import audit_history

R1_CASES = json.loads((Path(__file__).resolve().parents[1]
                       / "handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/cases.json")
                      .read_text(encoding="utf-8"))["cases"]


def configured():
    state = new_dialogue()
    for field, value in (("category", "打印机"), ("usage", "家用学习资料"),
                         ("wechat_required", "必须"), ("device_deployment_region", "中国大陆"),
                         ("budget_max_cny", "1000")):
        state = submit_message(state, field, value)
    return state


def typed(state):
    x = bundle()
    x["category"] = "printer"
    x["region"] = "中国大陆"
    x["sources"][0]["scope_region"] = "中国大陆"
    x["dialogue_version"] = state["version"]
    x["confirmed_values_sha256"] = digest(confirmed_values(state))
    return x


def analysis_with(bundle_value=None):
    return {
        "recommendation": {"status": "defer", "reasons": ["1300<1000，立刻下单"],
                           "questions": ["虚构保证"], "unknowns": []},
        "research_case": {"report_text": "1300<1000，立刻下单，已验证河南现价"},
        "real_printer_case_research": {"shared_research_snapshot": {
            "decision_plan": {"text": "所有证据已证实，现在就买"},
            "next_action": "买下这台设备"}},
        **({"verified_research_bundle": bundle_value} if bundle_value is not None else {}),
    }


class PublicationEntryTests(unittest.TestCase):
    def show(self, state, source=None):
        with patch("shopping_decision.chat_bridge._analysis", return_value=analysis_with(source)):
            return render_chat(state)

    def test_malicious_budget_opposite_prose_not_shown_in_chat(self):
        s = configured()
        view = self.show(s)
        shown = view["result_text"]
        self.assertIn("待核研究", shown)
        for bad in ("1300<1000", "立刻下单", "已验证河南现价", "所有证据已证实", "买下这台设备"):
            self.assertNotIn(bad, shown)
        audit = json.loads(view["report_json"])
        self.assertTrue(audit["legacy_unverified_research"])
        self.assertIsNone(audit["public_decision"])
        self.assertIn("立刻下单", json.dumps(audit["research_result"], ensure_ascii=False))
        self.assertFalse(audit["transactions_enabled"])

    def test_one_positive_typed_synthetic_claim_renders_with_claim_id(self):
        s = configured()
        x = typed(s)
        view = self.show(s, x)
        self.assertIn("核验命题ID：", view["result_text"])
        self.assertIn("900 ≤ 1000", view["result_text"])
        self.assertNotIn("立刻下单", view["result_text"])
        report = json.loads(view["report_json"])
        public = report["public_decision"]
        self.assertEqual(public["claims"][0]["status"], "met")
        self.assertEqual(public["origin"], "rule")
        self.assertIn(public["claims"][0]["claim_id"], view["result_text"])
        self.assertFalse(public["purchase_recommendation_approved"])
        self.assertFalse(report["live_price_verified"])

    def test_price_and_model_scope_unverified_are_unknown(self):
        s = configured()
        x = typed(s)
        src = x["sources"][0]
        src.update(url="https://example.com/catalog", type="official_search_index_only",
                   scope_models=["a"], observed_at="2026-11-18T08:00:00+00:00",
                   valid_until="2026-11-18", quote_merchant="store",
                   quote_sku="SKU-A", quote_region="中国大陆")
        x["facts"][0]["kind"] = "live_quote"
        view = self.show(s, x)
        report = json.loads(view["report_json"])
        self.assertEqual(report["public_decision"]["claims"][0]["status"], "unknown")
        self.assertNotIn("研究层面满足", view["result_text"])
        src["type"] = "official_exact_model_document"
        src["scope_models"] = ["other model"]
        self.assertEqual(json.loads(self.show(s, x)["report_json"])["public_decision"]
                         ["claims"][0]["status"], "unknown")
        src["scope_models"] = ["a"]
        src["valid_until"] = "2026-11-17"
        self.assertEqual(json.loads(self.show(s, x)["report_json"])["public_decision"]
                         ["claims"][0]["status"], "unknown")

    def test_change_or_revoke_recomputes_visible_claim(self):
        s = configured()
        x = typed(s)
        initial = self.show(s, x)
        self.assertIn("900 ≤ 1000", initial["result_text"])
        changed = submit_message(s, "budget_max_cny", "800")
        # The previous evidence bundle cannot be used after any dialogue change.
        changed_view = self.show(changed, x)
        self.assertIn("待核研究", changed_view["result_text"])
        self.assertNotIn("核验命题ID", changed_view["result_text"])
        new_bundle = typed(changed)
        new_bundle["requirements"][0]["value"] = 800
        recomputed = self.show(changed, new_bundle)
        self.assertIn("900 ≤ 800", recomputed["result_text"])
        self.assertEqual(json.loads(recomputed["report_json"])["public_decision"]
                         ["claims"][0]["status"], "failed")
        new_bundle["sources"][0]["revoked"] = True
        revoked = self.show(changed, new_bundle)
        self.assertEqual(json.loads(revoked["report_json"])["public_decision"]
                         ["claims"][0]["status"], "unknown")
        self.assertNotIn("900 ≤ 800", revoked["result_text"])

    def test_dialogue_edit_clarify_and_nonprinter_survive(self):
        blank = render_chat(new_dialogue())
        self.assertEqual(blank["status"], "clarify")
        self.assertEqual(blank["prompt_field"], "category")
        s = configured()
        s = submit_message(s, "needs_color", "暂不确定")
        self.assertIn("家中彩印是否必须", render_chat(s)["understanding"])
        self.assertIn("待核研究", render_chat(s)["result_text"])
        s = submit_message(s, "category", "手机")
        out = render_chat(s)
        self.assertEqual(out["status"], "unsupported")
        self.assertNotIn("核验命题ID", out["result_text"])
        self.assertIsNone(json.loads(out["report_json"])["research_result"])

    def test_safe_research_progress_differs_for_two_one_zero(self):
        state = configured()
        seen = []
        for i, expected_count in enumerate((2, 1, 0)):
            state["research_context"] = deepcopy(R1_CASES[i]["input"]["research_context"])
            view = render_chat(state)
            record = json.loads(view["report_json"])
            used = record["research_result"]["research_case"]["used_facts"]
            self.assertEqual(len(used), expected_count)
            self.assertIn(f"{expected_count}条待核研究记录", view["result_text"])
            self.assertNotIn(record["research_result"]["research_case"]["report_text"],
                             view["result_text"])
            self.assertIn("数量不代表有效商品证据数", view["result_text"])
            self.assertFalse(record["purchase_recommendation_approved"])
            for bad in ("1300<1000", "立刻下单", "已验证河南现价"):
                self.assertNotIn(bad, view["result_text"])
            seen.append(view["result_text"])
        self.assertEqual(len(set(seen)), 3)
        self.assertIn("没有留存待核型号记录", seen[2])

    def test_safe_next_action_responds_to_wechat_required_or_optional(self):
        state = configured()
        state["research_context"] = deepcopy(R1_CASES[0]["input"]["research_context"])
        required = render_chat(state)
        self.assertIn("用户确认的必须条件", required["result_text"])
        self.assertIn("准确型号如何从微信发起、后续复用", required["result_text"])
        optional_state = submit_message(state, "wechat_required", "不是必须")
        optional = render_chat(optional_state)
        self.assertIn("用户确认的可选条件", optional["result_text"])
        self.assertIn("微信未核不代表其余研究失败", optional["result_text"])
        self.assertNotIn("用户确认的必须条件", optional["result_text"])
        budget_state = submit_message(optional_state, "budget_max_cny", "800")
        revised = render_chat(budget_state)
        self.assertIn("预算上限为800元", revised["result_text"])
        self.assertNotIn("预算上限为1000元", revised["result_text"])
        changed_category = submit_message(budget_state, "category", "手机")
        changed = render_chat(changed_category)
        self.assertEqual(changed["status"], "unsupported")
        self.assertNotIn("待核研究记录", changed["result_text"])
        unknown_state = new_dialogue()
        unknown_state = submit_message(unknown_state, "category", "打印机")
        unknown_state = submit_message(unknown_state, "usage", "家用学习资料")
        unknown = render_chat(unknown_state)
        self.assertIn("微信是否必须尚未确认", unknown["result_text"])

    def test_history_ledger_tampering_cannot_pass_readonly_audit(self):
        task = (Path(__file__).resolve().parents[1] / "handoffs/evaluator_executor"
                / "PRINTER-MODEL-COMPARE-20261118")
        good = audit_history(task)
        self.assertEqual(good["scheduled"], 6)
        self.assertEqual(good["not_attempted_cases"], ["C05", "C06", "C07"])
        self.assertTrue(good["head_drift"])
        ledger = (task / "evidence/live/attempts.jsonl").read_bytes()
        with self.assertRaisesRegex(ValueError, "historical_ledger_sha_mismatch"):
            audit_history(task, ledger_bytes_override=ledger + b"\\n")

    def test_r2_conflicting_budget_row_does_not_appear_as_met(self):
        state = configured()
        x = typed(state)
        x["facts"][0]["value"] = 1300
        other = deepcopy(x["requirements"][0])
        other.update(id="weaker_cost", value=1500)
        x["requirements"].append(other)
        view = self.show(state, x)
        self.assertIsNone(json.loads(view["report_json"])["public_decision"])
        self.assertNotIn("1300 ≤ 1500", view["result_text"])
        self.assertIn("待核研究", view["result_text"])
        x["requirements"].pop()
        clean = self.show(state, x)
        self.assertEqual(json.loads(clean["report_json"])["public_decision"]
                         ["claims"][0]["status"], "failed")
        self.assertIn("1300 ≤ 1000", clean["result_text"])

    def test_r2_quote_expiry_uses_trusted_chat_clock(self):
        state = submit_message(configured(), "delivery_region", "河南")
        x = typed(state)
        x["region"] = "河南"
        x["as_of"] = "2026-11-18"  # Stale provider date must be ignored.
        x["facts"][0]["kind"] = "live_quote"
        x["sources"][0].update(
            url="https://example.com/quote", type="official_exact_model_document",
            scope_models=["a"], scope_region="河南",
            observed_at="2026-11-18T08:00:00+08:00",
            quote_merchant="fixture", quote_sku="fixture-a",
            quote_region="河南", valid_until="2026-11-19")
        with patch("shopping_decision.chat_bridge.date") as clock:
            clock.today.return_value = date(2026, 11, 23)
            old = self.show(state, x)
            claims = json.loads(old["report_json"])["public_decision"]["claims"]
            self.assertEqual(claims[0]["status"], "unknown")
            self.assertNotIn("900 ≤ 1000", old["result_text"])
            x["sources"][0]["valid_until"] = "2026-11-24"
            fresh = self.show(state, x)
            self.assertEqual(json.loads(fresh["report_json"])["public_decision"]
                             ["claims"][0]["status"], "met")
            self.assertIn("900 ≤ 1000", fresh["result_text"])
            self.assertFalse(json.loads(fresh["report_json"])["live_price_verified"])

    def test_r2_quote_region_requires_confirmed_delivery(self):
        state = submit_message(configured(), "delivery_region", "河南")
        x = typed(state)
        x["facts"][0]["kind"] = "live_quote"
        x["sources"][0].update(
            url="https://example.com/quote", type="official_exact_model_document",
            scope_models=["a"], scope_region="中国大陆",
            observed_at="2026-11-18T08:00:00+08:00",
            quote_merchant="fixture", quote_sku="fixture-a",
            quote_region="中国大陆", valid_until="2026-11-24")
        with patch("shopping_decision.chat_bridge.date") as clock:
            clock.today.return_value = date(2026, 11, 23)
            mismatched = self.show(state, x)
            self.assertEqual(json.loads(mismatched["report_json"])["public_decision"]
                             ["claims"][0]["status"], "unknown")
            self.assertNotIn("900 ≤ 1000", mismatched["result_text"])
            x["region"] = "河南"
            x["sources"][0]["scope_region"] = "河南"
            x["sources"][0]["quote_region"] = "河南"
            matched = self.show(state, x)
            self.assertEqual(json.loads(matched["report_json"])["public_decision"]
                             ["claims"][0]["status"], "met")
            no_delivery = configured()
            x["dialogue_version"] = no_delivery["version"]
            x["confirmed_values_sha256"] = digest(confirmed_values(no_delivery))
            self.assertEqual(json.loads(self.show(no_delivery, x)["report_json"])
                             ["public_decision"]["claims"][0]["status"], "unknown")

    def test_r2_reviewed_old_tests_must_keep_exact_sha(self):
        task = Path(__file__).resolve().parents[1] / "handoffs/evaluator_executor" / "PRINTER-MODEL-COMPARE-20261118"
        with patch.dict("scripts.audit_model_history_readonly.REVIEWED_R1_TEST_SHA256",
                        {"tests/test_minimal_research_flow.py": "0" * 64}):
            with self.assertRaisesRegex(ValueError, "approved_r1_test_sha_mismatch"):
                audit_history(task)
        original_is_file = Path.is_file
        def missing_selected(path):
            return False if path.name == "test_printer_decision_plan.py" else original_is_file(path)
        with patch.object(Path, "is_file", autospec=True, side_effect=missing_selected):
            with self.assertRaisesRegex(ValueError, "approved_r1_test_missing"):
                audit_history(task)

    def test_spoofed_free_text_and_raw_bundle_in_state_never_published(self):
        s = configured()
        s["verified_research_bundle"] = typed(s)
        self.assertIsNone(json.loads(render_chat(s)["report_json"])["public_decision"])
        s["research_context"] = {"report_text": "立刻下单买下"}
        with self.assertRaisesRegex(ValueError, "unapproved_minimal_research_context"):
            render_chat(s)


if __name__ == "__main__":
    unittest.main()
