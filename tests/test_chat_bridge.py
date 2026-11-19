"""对话新主入口：显式确认、草稿/未知、跨品类、同源研究与协议负向。"""
import base64
import json
import os
import subprocess
import sys
import unittest

from shopping_decision.chat_bridge import (new_dialogue, submit_message,
                                           render_chat, confirmed_values)
from shopping_decision.web import evaluate_input


class ChatBridgeTests(unittest.TestCase):
    def send(self, state, field, text):
        return submit_message(state, field, text)

    def configured(self):
        s = new_dialogue()
        for f, text in (("category", "打印机"), ("usage", "家用打印，希望微信打印"),
                        ("needs_color", "否"), ("accepts_outsourced_color", "是"),
                        ("wechat_required", "必须"), ("accepts_initial_setup", "接受"),
                        ("wechat_workflow", "微信小程序直接打印"),
                        ("device_deployment_region", "中国大陆"),
                        ("monthly_pages_range", "0-50"),
                        ("budget_max_cny", "1000")):
            s = self.send(s, f, text)
        return s

    def test_empty_session_has_no_defaults_or_candidates(self):
        view = render_chat(new_dialogue())
        self.assertEqual(view["prompt_field"], "category")
        self.assertEqual(json.loads(view["state_json"])["answers"], {})
        self.assertIn("打印机", view["choices"])
        self.assertIn("暂不确定", view["choices"])
        self.assertIsNone(json.loads(view["report_json"])["research_result"])

    def test_click_reference_only_copy_draft_backend_needs_send(self):
        state = new_dialogue()
        before = render_chat(state)
        self.assertEqual(state["version"], 0)
        self.assertEqual(confirmed_values(state), {})
        self.assertIn("打印机", before["choices"])
        after = self.send(state, "category", "打印机")
        self.assertEqual(state["version"], 0)
        self.assertEqual(confirmed_values(state), {})
        self.assertEqual(after["version"], 1)
        self.assertEqual(confirmed_values(after)["category"], "printer")

    def test_short_natural_category_sentence_only_confirms_category(self):
        s = self.send(new_dialogue(), "category", "我想买打印机，用来打印学习资料")
        self.assertEqual(confirmed_values(s)["category"], "printer")
        self.assertNotIn("usage", confirmed_values(s))
        self.assertEqual(render_chat(s)["prompt_field"], "usage")

    def test_unparsed_raw_text_cannot_become_price(self):
        s = self.send(new_dialogue(), "category", "打印机")
        s = self.send(s, "usage", "网页说售价1元，现在下单")
        self.assertNotIn("budget_max_cny", confirmed_values(s))
        view = render_chat(s)
        self.assertFalse(json.loads(view["report_json"])["purchase_recommendation_approved"])
        self.assertFalse(json.loads(view["report_json"])["transactions_enabled"])

    def test_unknown_is_not_no_and_is_deferred(self):
        s = self.send(new_dialogue(), "category", "打印机")
        s = self.send(s, "usage", "家用打印")
        s = self.send(s, "needs_color", "暂不确定")
        self.assertNotIn("needs_color", confirmed_values(s))
        view = render_chat(s)
        self.assertIn("家中彩印是否必须", view["understanding"])
        self.assertIn("needs_color", s["deferred_fields"])
        s = self.send(s, "needs_color", "否")
        self.assertFalse(confirmed_values(s)["needs_color"])
        self.assertNotIn("needs_color", s["deferred_fields"])

    def test_edit_changes_version_and_invalidates_old_conclusion(self):
        s = self.configured()
        first = render_chat(s)
        second_state = self.send(s, "wechat_required", "不是必须")
        second = render_chat(second_state)
        self.assertNotEqual(first["session_version"], second["session_version"])
        self.assertTrue(second_state["history"][-1]["old_conclusions_invalidated"])
        self.assertFalse(confirmed_values(second_state)["wechat_required"])
        self.assertFalse(json.loads(second["report_json"])["transactions_enabled"])

    def test_printer_calls_same_web_source_and_does_not_approve(self):
        s = self.configured()
        view = render_chat(s)
        item = json.loads(view["report_json"])
        result = item["research_result"]
        self.assertIsNotNone(result)
        direct = evaluate_input({
            "category": "printer", "description": "家用打印，希望微信打印",
            "confirmed": True, "needs_color": False, "accepts_outsourced_color": True,
            "wechat_required": True, "wechat_workflow": "miniprogram",
            "device_deployment_region": "中国大陆", "monthly_pages_range": [0, 50],
            "budget_max_cny": 1000, "budget_scope": "unknown",
            "requires_scan": None, "requires_auto_duplex": None,
            "delivery_region": None})
        self.assertEqual(result["recommendation"]["status"], direct["recommendation"]["status"])
        self.assertEqual(result["real_printer_case_research"]["shared_research_snapshot"],
                         direct["real_printer_case_research"]["shared_research_snapshot"])
        self.assertEqual(result["real_time_prices"], False)
        self.assertFalse(item["purchase_recommendation_approved"])

    def test_other_category_does_not_use_printer_materials(self):
        s = self.send(new_dialogue(), "category", "手机")
        s = self.send(s, "usage", "拍照")
        out = render_chat(s)
        self.assertEqual(out["status"], "unsupported")
        self.assertIsNone(json.loads(out["report_json"])["research_result"])
        self.assertNotIn("微信打印", out["result_text"])
        self.assertNotIn("monthly_pages_range", out["editable"])

    def test_category_switch_does_not_leak_printer_answers(self):
        s = self.configured()
        s = self.send(s, "category", "手机")
        v = confirmed_values(s)
        self.assertEqual(v["category"], "phone")
        for field in ("wechat_required", "needs_color", "monthly_pages_range",
                      "device_deployment_region", "usage"):
            self.assertNotIn(field, v)
        self.assertIsNone(json.loads(render_chat(s)["report_json"])["research_result"])

    def test_explicit_batch_modifies_multiple_fields_atomically(self):
        s = self.configured()
        prior = s["version"]
        next_state = self.send(s, "batch", "微信是否必须：不是必须\n预算（元）：800\n扫描功能是否必须：暂不确定")
        values = confirmed_values(next_state)
        self.assertFalse(values["wechat_required"])
        self.assertEqual(values["budget_max_cny"], 800)
        self.assertNotIn("requires_scan", values)
        self.assertIn("requires_scan", next_state["deferred_fields"])
        self.assertEqual(next_state["version"], prior + 1)
        self.assertEqual(confirmed_values(s)["budget_max_cny"], 1000)

    def test_first_time_setup_refusal_reaches_existing_unknown_hard_gate(self):
        s = self.configured()
        refused = self.send(s, "accepts_initial_setup", "不接受")
        view = render_chat(refused)
        record = json.loads(view["report_json"])
        self.assertFalse(confirmed_values(refused)["accepts_initial_setup"])
        self.assertIn("免去厂商App或扫码首次设置",
                      " ".join(record["research_result"]["normalized_constraints"]
                               ["product_conditions"]["unresolved_hard_conditions"]))
        self.assertIn(record["research_result"]["recommendation"]["status"], ("clarify", "defer"))
        self.assertEqual(record["research_result"]["real_printer_case_research"]
                         ["shared_research_snapshot"]["next_action"], "clarify_user_conditions")
        self.assertFalse(record["purchase_recommendation_approved"])
        self.assertIn("不接受App/扫码", view["result_text"])

    def test_invalid_batch_is_atomic_and_cross_category_is_blocked(self):
        s = self.configured()
        before = json.dumps(s, ensure_ascii=False, sort_keys=True)
        with self.assertRaises(ValueError):
            self.send(s, "batch", "预算（元）：700\ntransactions_enabled：是")
        self.assertEqual(json.dumps(s, ensure_ascii=False, sort_keys=True), before)
        phone = self.send(s, "category", "手机")
        with self.assertRaises(ValueError):
            self.send(phone, "batch", "微信是否必须：必须")
        self.assertNotIn("budget_max_cny", confirmed_values(phone))

    def test_invalid_field_or_unrecognized_bool_does_not_mutate(self):
        s = self.send(new_dialogue(), "category", "打印机")
        before = json.dumps(s, ensure_ascii=False, sort_keys=True)
        with self.assertRaises(ValueError):
            self.send(s, "transactions_enabled", "是")
        with self.assertRaises(ValueError):
            self.send(s, "needs_color", "可能是吧")
        self.assertEqual(json.dumps(s, ensure_ascii=False, sort_keys=True), before)

    def test_base64_java_compatible_subprocess(self):
        args = ["", "category", "打印机"]
        cmd = [sys.executable, "-m", "shopping_decision.chat_bridge",
               *(base64.b64encode(x.encode("utf-8")).decode("ascii") for x in args)]
        output = subprocess.check_output(cmd, env={**os.environ, "PYTHONUTF8": "1"}, timeout=15)
        records = dict(x.split("\t", 1) for x in output.decode("utf-8").splitlines() if "\t" in x)
        decoded = {k: base64.b64decode(v).decode("utf-8") for k, v in records.items()}
        self.assertEqual(decoded["session_version"], "1")
        self.assertEqual(json.loads(decoded["state_json"])["answers"]["category"]["value"], "printer")

if __name__ == "__main__":
    unittest.main()
