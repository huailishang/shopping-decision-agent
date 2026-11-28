import json
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from datetime import date
from shopping_decision.context_builder import build_context
from shopping_decision.action_ranking import accept_ranking,rank_actions
from shopping_decision.chat_bridge import new_dialogue,submit_message,render_chat,confirmed_values
from shopping_decision.evidence_comparison import digest
from shopping_decision import cognition_comparison as cog
from test_context_builder import open_color,ROUTE
from test_unified_decision_actions import fixture

def fake(payload):
    ctx=json.loads(payload["input"])["required"]
    answer={"context_id":ctx["context_id"],"action_ids":[a["id"] for a in reversed(ctx["allowed_actions"])]}
    return {"http_status":200,"raw":json.dumps({"model":"mock","status":"completed","output":[{"type":"message","role":"assistant","content":[{"type":"output_text","text":json.dumps(answer)}]}]})}

def state():
    s=new_dialogue()
    for f,a in (("category","打印机"),("usage","低频家庭打印"),("needs_color","是"),
                ("monthly_pages_range","0-50"),("budget_max_cny","1000"),
                ("device_deployment_region","中国大陆河南省"),("wechat_required","必须"),
                ("wechat_workflow","小程序"),("accepts_initial_setup","接受"),
                ("requires_scan","是"),("requires_auto_duplex","否")):
        s=submit_message(s,f,a)
    return s

class RankingTests(TestCase):
    def test_valid_invalid_stale(self):
        p=open_color(); plan=build_context(p,ROUTE,input_cap=25000)
        a={"context_id":plan["packet"]["required"]["context_id"],"action_ids":plan["action_ids"][::-1]}
        ordered=accept_ranking(p,plan,a)
        self.assertNotEqual(ordered,p["next_actions"])
        for bad in (dict(a,action_ids=["x"]),dict(a,action_ids=[a["action_ids"][0]]*2),
                    dict(a,context_id="old"),dict(a,summary="立即下单")):
            with self.assertRaises(ValueError):accept_ranking(p,plan,bad)
        changed=deepcopy(p);changed["decision_binding"]["dialogue_version"]=999
        with self.assertRaisesRegex(ValueError,"stale_context"):accept_ranking(changed,plan,a)
    def test_fault_falls_back(self):
        p=open_color()
        ranked,audit=rank_actions(p,ROUTE,lambda _:{"http_status":200,"raw":"bad"},input_cap=25000)
        self.assertEqual(ranked,p["next_actions"])
        self.assertFalse(audit["business_accepted"])
        self.assertEqual(audit["external_api_calls"],0)
    def test_real_default_chat_injection(self):
        s=state();pack=cog.load_pack()
        for src in pack["sources"]: src.pop("observed_at",None)
        with patch.object(cog,"load_pack",return_value=pack),patch("shopping_decision.chat_bridge.date") as clock:
            clock.today.return_value=date(2026,11,25)
            base=render_chat(deepcopy(s))
            view=render_chat(deepcopy(s),ranking_route=ROUTE,ranking_transport=fake,ranking_budget={"input_cap":25000})
        before=json.loads(base["report_json"])["cognition_comparison"]
        after=json.loads(view["report_json"])["cognition_comparison"]
        self.assertTrue(after["ranking_audit"]["business_accepted"])
        self.assertNotEqual(before["public"]["next_actions"][0],after["public"]["next_actions"][0])
        self.assertTrue(view["prompt"].startswith("核"+after["public"]["next_actions"][0]["candidate_id"]))
    def test_real_backend_chat_injection(self):
        s=state();b=fixture("C08")
        for src in b["sources"]:src.pop("observed_at",None)
        b.update(dialogue_version=s["version"],confirmed_values_sha256=digest(confirmed_values(s)),as_of=date.today().isoformat())
        with patch("shopping_decision.chat_bridge._analysis",return_value={"recommendation":{"status":"research"},"verified_research_bundle":b}):
            base=render_chat(deepcopy(s))
            view=render_chat(deepcopy(s),ranking_route=ROUTE,ranking_transport=fake,ranking_budget={"input_cap":25000})
        x=json.loads(base["report_json"]);y=json.loads(view["report_json"])
        self.assertTrue(y["ranking_audit"]["business_accepted"])
        self.assertNotEqual(x["public_decision"]["next_actions"][0],y["public_decision"]["next_actions"][0])
        self.assertTrue(view["prompt"].startswith(y["public_decision"]["next_actions"][0]["candidate_id"]))
