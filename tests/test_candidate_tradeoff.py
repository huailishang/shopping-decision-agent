"""Candidate eligibility, scenario arithmetic and normal chat integration."""
from copy import deepcopy
from datetime import date
import json
from unittest import TestCase
from unittest.mock import patch
from shopping_decision import cognition_comparison as cog
from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message

HP = "HP M232dw"
BROTHER = "Brother HL-L1238W"

class CandidateTradeoffTests(TestCase):
    def setUp(self):
        self.pack = cog.load_pack()
        self.assertIsNotNone(self.pack)
        self.state = new_dialogue()
        for field, answer in (("category","打印机"),("usage","低频家庭打印"),
            ("needs_color","否"),("accepts_outsourced_color","是"),
            ("monthly_pages_range","0-50"),("budget_max_cny","1000"),
            ("device_deployment_region","中国大陆河南省"),("wechat_required","必须"),
            ("wechat_workflow","小程序"),("accepts_initial_setup","接受"),
            ("requires_scan","否"),("requires_auto_duplex","否")):
            self.state = submit_message(self.state,field,answer)

    def view(self, state=None, pack=None):
        with patch.object(cog,"load_pack",return_value=deepcopy(self.pack if pack is None else pack)):
            with patch("shopping_decision.chat_bridge.date") as clock:
                clock.today.return_value = date(2026,11,25)
                view = render_chat(deepcopy(self.state if state is None else state))
        audit = json.loads(view["report_json"])
        for key in ("purchase_recommendation_approved","transactions_enabled","live_price_verified"):
            self.assertIs(audit[key],False)
        return view,audit["cognition_comparison"]

    def color_state(self):
        return submit_message(submit_message(self.state,"needs_color","是"),"requires_scan","是")

    def test_real_hard_color_excludes_both(self):
        view,res = self.view(self.color_state())
        self.assertEqual({r["state"] for r in res["decision"]["candidates"]},{"excluded_for_research"})
        self.assertEqual(res["decision"]["next_action"]["kind"],"stop")
        self.assertEqual(res["public"]["next_actions"],[])
        self.assertEqual(view["prompt"],res["decision"]["next_action"]["text"])
        self.assertNotIn("HP M232dw在该维度有依据，可优先核查",view["result_text"])

    def test_withdraw_color_only_maintains_other_facts(self):
        pack=deepcopy(self.pack)
        pack["facts"]=[f for f in pack["facts"] if f["id"]!="hp-mono"]
        view,res=self.view(self.color_state(),pack)
        rows={r["model"]:r for r in res["decision"]["candidates"]}
        self.assertEqual(rows[HP]["state"],"pending_evidence")
        self.assertEqual(rows[BROTHER]["state"],"excluded_for_research")
        self.assertIn("scan",rows[HP]["supported"])
        self.assertEqual(res["decision"]["next_action"]["candidates"],[HP])
        self.assertEqual(res["decision"]["next_action"]["dimension"],"color_print")
        self.assertEqual(view["prompt"],res["decision"]["next_action"]["text"])

    def test_color_conflict_not_failed(self):
        pack=deepcopy(self.pack)
        f=deepcopy(next(f for f in pack["facts"] if f["id"]=="hp-mono"))
        f.update(id="synthetic-color-conflict",value=True,kind="synthetic_probe")
        pack["facts"].append(f)
        _,res=self.view(self.color_state(),pack)
        rows={r["model"]:r for r in res["decision"]["candidates"]}
        self.assertIn("color_print",rows[HP]["pending"])
        self.assertNotIn("color_print",rows[HP]["failed"])

    def test_cost_scenario_and_real_inputs(self):
        view,res=self.view()
        cost=res["decision"]["cost_scenario"]
        self.assertEqual(cost["pages"],[0,1800])
        self.assertTrue(cost["assumption_only"])
        b=cost["models"][BROTHER]
        self.assertTrue(b["separate_drum"])
        self.assertEqual(b["replacement_yield"],1500)
        self.assertEqual([x["at_max_pages"] for x in b["example_replacements"]],[2,1])
        self.assertIsNone(b["starter"])
        self.assertTrue(cost["models"][HP]["starter_included"])
        self.assertIsNone(cost["models"][HP]["starter"])
        self.assertIn("翻转条件",view["result_text"])
        self.assertIn("当前不要求扫描：该额外功能不构成当前选型必要性",view["result_text"])
        self.assertIn("137A/137X",view["result_text"])

    def test_cost_yield_withdrawal_and_synthetic_change(self):
        pack=deepcopy(self.pack)
        f=next(f for f in pack["facts"] if f["id"]=="brother-tn118-yield")
        f.update(value=600,kind="synthetic_probe",statement="仅合成变化")
        _,res=self.view(pack=pack)
        b=res["decision"]["cost_scenario"]["models"][BROTHER]
        self.assertEqual([x["at_max_pages"] for x in b["example_replacements"]],[3,2])
        f["revoked"]=True
        _,res=self.view(pack=pack)
        self.assertIsNone(res["decision"]["cost_scenario"]["models"][BROTHER]["replacement_yield"])
        self.assertEqual(res["decision"]["cost_scenario"]["models"][BROTHER]["drum_yield"],10000)

    def test_arithmetic_boundaries(self):
        self.assertEqual(cog.replacement_count(1500,1500,1500),0)
        self.assertEqual(cog.replacement_count(1501,1500,1500),1)
        self.assertEqual(cog.replacement_count(0,0,1500),0)
        for bad in ((1,0,0),(True,0,1),(-1,0,1)):
            with self.assertRaises(ValueError):
                cog.replacement_count(*bad)

    def test_region_does_not_hide_comparison(self):
        _,a=self.view()
        changed=submit_message(self.state,"delivery_region","河南省郑州市金水区")
        _,b=self.view(changed)
        self.assertEqual(a["decision"]["cost_scenario"],b["decision"]["cost_scenario"])
        self.assertEqual([r["state"] for r in a["decision"]["candidates"]],
                         [r["state"] for r in b["decision"]["candidates"]])

    def test_cost_gate_does_not_publish_quote(self):
        pack=deepcopy(self.pack)
        f=deepcopy(pack["facts"][0])
        f.update(id="synthetic-bad-price",dimension="cost",unit="CNY",value=1,kind="live_quote",statement="现在下单")
        pack["facts"].append(f)
        view,res=self.view(pack=pack)
        self.assertNotIn("现在下单",view["result_text"])
        self.assertTrue(all(c["status"]=="unknown" for c in res["public"]["claims"] if c["dimension"]=="cost"))
