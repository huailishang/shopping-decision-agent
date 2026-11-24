"""Regression checks for the original household's purchase-preparation flow."""

import json
from pathlib import Path
import runpy
from unittest import TestCase
from unittest.mock import patch

from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message
from shopping_decision.printer_purchase_checks import HARDWARE_ONLY


ROOT = Path(__file__).resolve().parents[1]
VERIFY = runpy.run_path(str(ROOT / "handoffs/evaluator_executor" /
                           "PRINTER-HOUSEHOLD-NEXT-ACTION-20261124/VERIFY_ACTIONS.py"))
PRIOR = runpy.run_path(str(ROOT / "handoffs/evaluator_executor" /
                          "PRINTER-CHAT-CONTEXT-20261124/VERIFY_ORIGINAL_CASE.py"))


class PrinterPurchaseChecksTests(TestCase):
    def case_state(self):
        case = json.loads(PRIOR["INPUT"].read_text(encoding="utf-8"))
        state = new_dialogue()
        for key, value in case["answers"].items():
            state = submit_message(state, key, PRIOR["answer_text"](value))
        state["research_context"] = case["research_context"]
        return state

    def test_hardware_ceiling_survives_followup_and_can_be_edited(self):
        state = submit_message(self.case_state(), "batch", "wechat_workflow：小程序\n"
                               "delivery_region：河南省周口市\nbudget_scope：仅主机硬件")
        first = render_chat(state)
        audit = json.loads(first["report_json"])
        self.assertEqual(audit["confirmed_fields"]["budget_scope"], HARDWARE_ONLY)
        self.assertEqual(audit["purchase_checks"]["quote_missing"], ["delivery_region"])
        self.assertEqual(first["prompt_field"], "delivery_region")
        self.assertIn("运费及另购耗材单列", first["result_text"])
        repeat = submit_message(state, "budget_scope", "仅主机硬件")
        self.assertEqual(repeat["history"][-1]["changed_fields"], [])
        ready = submit_message(repeat, "delivery_region", "河南省周口市川汇区")
        audit = json.loads(render_chat(ready)["report_json"])
        self.assertEqual(audit["purchase_checks"]["quote_status"], "awaiting_authoritative_quote")
        self.assertIsNone(audit["purchase_checks"]["payable_cny"])
        self.assertFalse(audit["live_price_verified"])
        reset = submit_message(ready, "budget_scope", "暂不确定")
        audit = json.loads(render_chat(reset)["report_json"])
        self.assertEqual(audit["purchase_checks"]["quote_missing"], ["budget_scope"])

    def test_v1_stays_pending_with_switch_enabled(self):
        state = submit_message(self.case_state(), "wechat_workflow", "小程序")
        with patch.dict("os.environ", {"SHOPPING_PRINTER_REVIEWED_EVIDENCE": "1"}):
            rendered = render_chat(state)
        audit = json.loads(rendered["report_json"])
        self.assertIsNone(audit["public_decision"])
        self.assertIn("待核研究", rendered["result_text"])
        self.assertIn("Brother HL-L1238W", rendered["result_text"])

    def test_path_and_category_changes(self):
        replay = VERIFY["replay"]()
        self.assertEqual(replay["transfer"]["preflight"]["wechat_step"], "verify_transfer")
        self.assertEqual(replay["optional"]["preflight"]["wechat_step"], "continue_comparison")
        self.assertEqual(replay["setup_rejected"]["preflight"]["wechat_step"], "verify_no_setup")
        self.assertIsNone(replay["switch_category"]["preflight"])
