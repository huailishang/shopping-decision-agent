import json,unittest,tempfile
from pathlib import Path
from copy import deepcopy
from datetime import date
from unittest.mock import patch
from shopping_decision import guide_binding as gb,cognition_comparison as cog
from shopping_decision.chat_bridge import render_chat
from shopping_decision.context_builder import build_context
from test_focus_guidance import state,focus
from test_action_ranking import state as ranking_state,ROUTE,fake

class FocusLineage(unittest.TestCase):
    def test_source_new_version_invalidates_claim(self):
        s=state("扫描存档");a=focus(render_chat(deepcopy(s)))
        self.assertIn("guide-functions",a["claim_ids"])
        data=json.loads(gb.REGISTRY.read_text(encoding="utf8"))
        data["sources"]["hp-cn-home"]["revision"]=2
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"registry.json";f.write_text(json.dumps(data),encoding="utf8")
            with patch.object(gb,"REGISTRY",f):b=focus(render_chat(deepcopy(s)))
        self.assertEqual(b["field"],a["field"])
        self.assertNotEqual(b["guide_version"],a["guide_version"])
        self.assertEqual(b["claim_ids"],[])
    def test_ranked_context_same_focus(self):
        s=ranking_state();pack=cog.load_pack()
        for src in pack["sources"]:src.pop("observed_at",None)
        with patch.object(cog,"load_pack",return_value=pack),patch("shopping_decision.chat_bridge.date") as clock:
            clock.today.return_value=date(2026,11,27)
            v=render_chat(s,ranking_route=ROUTE,ranking_transport=fake,ranking_budget={"input_cap":28000})
        audit=json.loads(v["report_json"])["cognition_comparison"]["ranking_audit"]
        self.assertTrue(audit["business_accepted"],audit.get("reason"))
        self.assertEqual(audit["plan"]["packet"]["required"]["cognition_context"]["guidance_focus"],focus(v))
    def test_stale_focus_rejected(self):
        s=ranking_state();pack=cog.load_pack()
        for src in pack["sources"]:src.pop("observed_at",None)
        with patch.object(cog,"load_pack",return_value=pack):
            v=render_chat(s)
        public=json.loads(v["report_json"])["cognition_comparison"]["public"]
        context=json.loads(v["cognition_context_json"])
        context["guidance_focus"]["state_version"]+=1
        with self.assertRaisesRegex(ValueError,"invalid_guidance_focus_binding"):
            build_context(public,ROUTE,cognition_context=context,input_cap=28000)
