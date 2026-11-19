"""首个真人打印机案例：公开来源理由、原案条件与R0—R5模拟改答。"""
from copy import deepcopy
import json
import subprocess
import sys
import unittest

from shopping_decision.real_printer_case import compare_case_research, RESEARCH_PATH

BASE = {
    "category": "printer", "usage": "家用",
    "budget_max_cny": 1000, "budget_scope": "unknown",
    "monthly_pages_range": [0, 50],
    "needs_color": False, "accepts_outsourced_color": True,
    "wechat_required": None, "wechat_workflow": "unknown",
    "requirements": ["预算千元内、月打印0–50页、家里黑白为主、希望支持微信打印、可靠耐用，重点比较兄弟和惠普"],
}


class RealPrinterCaseResearchTests(unittest.TestCase):
    def test_original_has_case_specific_reasons_and_no_purchase_approval(self):
        view = compare_case_research(BASE)
        self.assertEqual([x["id"] for x in view["reasons"]],
                         ["CASE-01", "CASE-02", "CASE-03", "CASE-06", "CASE-07", "CASE-08"])
        self.assertTrue(view["status"].endswith("pending_independent_review"))
        self.assertEqual(view["real_sale_identity_verified_count"], 0)
        self.assertEqual(view["regional_live_quote_count"], 0)
        comparison = view["model_comparison"]
        self.assertEqual([x["model_id"] for x in comparison["models"]],
                         ["HL-L1238W", "M232dw"])
        self.assertEqual(len(comparison["comparisons"]), 9)
        self.assertEqual(len(comparison["conditional_decisions"]), 3)
        self.assertEqual(comparison["deployment_region_scope"], "unknown")
        self.assertEqual(len(comparison["unknown_conditional_decisions"]), 3)
        self.assertFalse(comparison["purchase_recommendation_approved"])
        self.assertFalse(view["purchase_recommendation_approved"])
        self.assertFalse(view["transactions_enabled"])
        for item in view["reasons"]:
            self.assertTrue(item["counter_evidence"])
            self.assertEqual(item["actual_purchase_effect"], "none_unapproved")
            for evidence in item["evidence"]:
                self.assertTrue(evidence["source_url"].startswith("https://"))
                self.assertTrue(evidence["source_limit"])
                self.assertTrue(evidence["scope"])

    def test_wechat_preference_is_not_promoted_to_hard_requirement(self):
        view = compare_case_research(BASE)
        wechat = next(x for x in view["reasons"] if x["id"] == "CASE-02")
        self.assertIn("不自动把", wechat["reason"])
        self.assertIsNone(BASE["wechat_required"])
        self.assertIn("CASE-08", [x["id"] for x in view["reasons"]])

    def test_region_changes_only_when_deployment_region_is_explicit(self):
        mainland = compare_case_research({**BASE, "device_deployment_region": "河南省周口市鹿邑县"})
        overseas = compare_case_research({**BASE, "device_deployment_region": "Singapore"})
        self.assertEqual(mainland["model_comparison"]["deployment_region_scope"], "mainland_china")
        self.assertEqual(overseas["model_comparison"]["deployment_region_scope"], "outside_mainland_china")
        decisions = {x["id"]: x["applicability"]
                     for x in overseas["model_comparison"]["conditional_decisions"]}
        self.assertEqual(decisions["DEC-03"], "applicable")
        self.assertEqual({x["id"] for x in overseas["model_comparison"]["active_conditional_decisions"]},
                         {"DEC-03"})
        shipping_only = compare_case_research({**BASE, "delivery_region": "Singapore"})
        self.assertEqual(shipping_only["model_comparison"]["deployment_region_scope"], "unknown")
        malformed = compare_case_research({**BASE, "device_deployment_region": 123})
        self.assertEqual(malformed["model_comparison"]["deployment_region_scope"], "unknown")

    def test_edits_recompute_no_stale_reasons(self):
        state = deepcopy(BASE)
        state["requires_scan"] = True
        self.assertIn("CASE-04", [x["id"] for x in compare_case_research(state)["reasons"]])
        state["requires_scan"] = False
        state["requires_auto_duplex"] = True
        ids = {x["id"] for x in compare_case_research(state)["reasons"]}
        self.assertNotIn("CASE-04", ids)
        self.assertIn("CASE-05", ids)
        state["requires_auto_duplex"] = False
        self.assertNotIn("CASE-05", {x["id"] for x in compare_case_research(state)["reasons"]})
        state["needs_color"] = True
        ids = {x["id"] for x in compare_case_research(state)["reasons"]}
        self.assertNotIn("CASE-01", ids)
        self.assertIn("CASE-09", ids)
        state["needs_color"] = False
        state["wechat_required"] = False
        ids = {x["id"] for x in compare_case_research(state)["reasons"]}
        self.assertIn("CASE-01", ids)
        self.assertNotIn("CASE-02", ids)
        self.assertNotIn("CASE-08", ids)

    def test_missing_user_reply_is_not_inferred(self):
        view = compare_case_research({"category": "printer", "usage": "家用"})
        self.assertEqual(view["reason_count"], 0)
        self.assertFalse(view["purchase_recommendation_approved"])

    def test_source_gate_cannot_be_self_approved(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        data = json.loads(RESEARCH_PATH.read_text(encoding="utf-8"))
        data["review_status"] = "approved"
        with TemporaryDirectory() as folder:
            path = Path(folder) / "research.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid_case_research_contract"):
                compare_case_research(BASE, path=path)

    def test_real_cli_r0_to_r5_recomputes_public_research(self):
        changes = [
            {"text": "R0 原案冻结；仅复用已确认字段，微信为偏好非硬门槛",
             "answers": BASE},
            {"text": "R1 假设必须扫描", "answers": {"requires_scan": True}},
            {"text": "R2 假设扫描不需要但自动双面必须",
             "answers": {"requires_scan": False, "requires_auto_duplex": True}},
            {"text": "R2b 撤销自动双面要求", "answers": {"requires_auto_duplex": False}},
            {"text": "R3 假设家中必须彩印", "answers": {"needs_color": True}},
            {"text": "R4 恢复黑白；微信不强求，接受转存厂商App",
             "answers": {"needs_color": False, "wechat_required": False,
                         "wechat_workflow": "transfer_to_app"}},
            {"text": "R5 模拟把预算降到500元", "answers": {"budget_max_cny": 500}},
            {"text": "R5b 清空预算和微信偏好条件",
             "answers": {"budget_max_cny": None, "wechat_required": None,
                         "wechat_workflow": "unknown",
                         "requirements": ["可靠耐用，重点比较兄弟和惠普"]}},
        ]
        proc = subprocess.run(
            [sys.executable, "-m", "shopping_decision.dialogue_flow", "--real-printer-case"],
            input="".join(json.dumps(item, ensure_ascii=False) + "\n" for item in changes),
            text=True, capture_output=True, encoding="utf-8", timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(output), len(changes) + 1)
        records = [item["real_printer_case_research"] for item in output[1:]]
        ids = lambda record: {item["id"] for item in record["reasons"]}
        r0, r1, r2, r2b, r3, r4, r5, r5b = records
        self.assertEqual(ids(r0), {"CASE-01", "CASE-02", "CASE-03", "CASE-06", "CASE-07", "CASE-08"})
        self.assertIn("CASE-04", ids(r1))
        self.assertNotIn("CASE-04", ids(r2))
        self.assertIn("CASE-05", ids(r2))
        self.assertNotIn("CASE-05", ids(r2b))
        self.assertIn("CASE-01", ids(r2b))
        self.assertNotIn("CASE-01", ids(r3))
        self.assertIn("CASE-09", ids(r3))
        self.assertIn("CASE-01", ids(r4))
        self.assertNotIn("CASE-02", ids(r4))
        self.assertNotIn("CASE-08", ids(r4))
        self.assertIn("500元", next(x["reason"] for x in r5["reasons"] if x["id"] == "CASE-06"))
        self.assertNotIn("CASE-06", ids(r5b))
        self.assertNotIn("CASE-02", ids(r5b))
        self.assertNotIn("CASE-08", ids(r5b))
        for record in records:
            self.assertEqual(record["real_sale_identity_verified_count"], 0)
            self.assertFalse(record["purchase_recommendation_approved"])
            self.assertFalse(record["transactions_enabled"])


if __name__ == "__main__":
    unittest.main()
