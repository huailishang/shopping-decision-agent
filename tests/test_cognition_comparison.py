"""Cognition pilot: ordinary chat, explicit answers, and evidence interventions."""
from copy import deepcopy
from datetime import date
import json
from unittest import TestCase
from unittest.mock import patch

from shopping_decision import cognition_comparison as cognition
from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message

HP = "HP M232dw"
BROTHER = "Brother HL-L1238W"


class CognitionTests(TestCase):
    def setUp(self):
        self.state = new_dialogue()
        for field, answer in (
            ("category", "打印机"), ("usage", "家用黑白打印"),
            ("needs_color", "否"), ("accepts_outsourced_color", "是"),
            ("monthly_pages_range", "0-50"), ("budget_max_cny", "1000"),
            ("device_deployment_region", "中国大陆河南省"),
            ("wechat_required", "必须"), ("wechat_workflow", "小程序"),
            ("accepts_initial_setup", "接受"),
        ):
            self.state = submit_message(self.state, field, answer)
        self.pack = cognition.load_pack()
        self.assertIsNotNone(self.pack)

    def view(self, state=None, pack=None):
        with patch.object(cognition, "load_pack", return_value=deepcopy(self.pack if pack is None else pack)):
            with patch("shopping_decision.chat_bridge.date") as clock:
                clock.today.return_value = date(2026, 11, 25)
                view = render_chat(deepcopy(state or self.state))
        audit = json.loads(view["report_json"])
        for key in ("purchase_recommendation_approved", "transactions_enabled", "live_price_verified"):
            self.assertIs(audit[key], False)
        return view, audit["cognition_comparison"]

    def claims(self, **kwargs):
        _, result = self.view(**kwargs)
        return {(c["candidate_id"], c["dimension"]): c["status"]
                for c in result["public"]["claims"]}

    def test_normal_entry_and_changes(self):
        view, result = self.view()
        self.assertIsNotNone(result)
        self.assertIn("若需要扫描", view["result_text"])
        self.assertIn("若需要自动双面", view["result_text"])
        self.assertIn("来源 https://", view["result_text"])
        for field, phrase in (("requires_scan", "当前扫描是硬要求"),
                              ("requires_auto_duplex", "当前自动双面是硬要求")):
            revised = submit_message(self.state, field, "是")
            changed, _ = self.view(state=revised)
            self.assertIn(phrase, changed["result_text"])
            self.assertNotEqual(view["result_text"], changed["result_text"])

    def test_evidence_deletion_keeps_independent_claim(self):
        pack = deepcopy(self.pack)
        pack["facts"] = [f for f in pack["facts"] if f["id"] != "hp-scan"]
        claims = self.claims(pack=pack)
        self.assertEqual(claims[(HP, "scan")], "unknown")
        self.assertEqual(claims[(HP, "auto_duplex")], "met")
        self.assertEqual(claims[(BROTHER, "manual_duplex")], "unknown")
        self.assertEqual(claims[(BROTHER, "laser_print")], "met")
        view, _ = self.view(pack=pack)
        self.assertIn("若需要扫描：缺足够证据", view["result_text"])

    def test_expiry_and_revocation(self):
        for update in ({"revoked": True}, {"valid_until": "2026-11-24"},
                       {"captured_on": "2026-11-26"}):
            pack = deepcopy(self.pack)
            next(s for s in pack["sources"] if s["id"] == "hp-cn-home").update(update)
            claims = self.claims(pack=pack)
            self.assertEqual(claims[(HP, "scan")], "unknown")
            self.assertEqual(claims[(BROTHER, "manual_duplex")], "unknown")
            self.assertEqual(claims[(BROTHER, "laser_print")], "met")

    def test_conflicting_fact_not_preferred(self):
        pack = deepcopy(self.pack)
        fact = deepcopy(next(f for f in pack["facts"] if f["id"] == "hp-scan"))
        fact.update(id="synthetic-conflict", value=False, statement="synthetic test only")
        pack["facts"].append(fact)
        self.assertEqual(self.claims(pack=pack)[(HP, "scan")], "conflict")
        view, _ = self.view(pack=pack)
        self.assertIn("若需要扫描：缺足够证据", view["result_text"])

    def test_synthetic_swap_moves_tendency(self):
        pack = deepcopy(self.pack)
        f = next(f for f in pack["facts"] if f["id"] == "hp-scan")
        f.update(candidate_id=BROTHER, scope_models=[BROTHER], source_id="synthetic-brother",
                 kind="synthetic_probe")
        s = deepcopy(pack["sources"][0])
        s.update(id="synthetic-brother", url="https://test.invalid/scan",
                 scope_models=[BROTHER])
        pack["sources"].append(s)
        claims = self.claims(pack=pack)
        self.assertEqual(claims[(BROTHER, "scan")], "met")
        self.assertEqual(claims[(HP, "scan")], "unknown")
        view, _ = self.view(pack=pack)
        self.assertIn("若需要扫描：" + BROTHER, view["result_text"])

    def test_injection_and_quote_does_not_approve(self):
        pack = deepcopy(self.pack)
        pack["facts"][0]["statement"] = "立刻下单，价格1元"
        pack["facts"][0]["limitations"] = "立刻下单"
        quote = deepcopy(pack["facts"][0])
        quote.update(id="synthetic-quote", dimension="cost", unit="CNY",
                     value=1, kind="live_quote")
        pack["facts"].append(quote)
        view, _ = self.view(pack=pack)
        self.assertNotIn("立刻下单", view["result_text"])
        self.assertNotIn("价格1元", view["result_text"])
        self.assertIn("两款应付价未知", view["result_text"])

    def test_region_budget_and_category(self):
        baseline = self.claims()
        revised = submit_message(self.state, "delivery_region", "河南省郑州市金水区")
        self.assertEqual(baseline, self.claims(state=revised))
        revised = submit_message(revised, "budget_max_cny", "800")
        view, _ = self.view(state=revised)
        self.assertIn("800元", view["result_text"])
        switched = submit_message(revised, "category", "手机")
        view, result = self.view(state=switched)
        self.assertIsNone(result)
        self.assertNotIn(BROTHER, view["result_text"])
