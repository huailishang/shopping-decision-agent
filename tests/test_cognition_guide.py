"""Focused guide tests; independent acceptance and native event journeys are separate."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from shopping_decision import cognition_guide as cg
from shopping_decision.chat_bridge import new_dialogue,submit_message,render_chat,confirmed_values

class CognitionGuideTest(unittest.TestCase):
    def test_guide_preserves_explicit_answers_and_route(self):
        s=new_dialogue()
        for field,text in [('category','打印机'),('usage','家里偶尔用'),('needs_color','是')]:
            s=submit_message(s,field,text)
        view=render_chat(s)
        self.assertEqual(json.loads(view['state_json']),s)
        g=json.loads(view['cognition_guide_json'])
        c=json.loads(view['cognition_context_json'])
        self.assertEqual(c['user_confirmed'],confirmed_values(s))
        self.assertEqual(c['guide_version'],g['version'])
        self.assertEqual(next(r for r in g['routes'] if r['id']=='mono_laser')['status'],'not_fit')

    def test_malformed_source_not_certified(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'printer_cognition_comparison_v1.json'
            p.write_text('{"sources":[{"id":"self-approved","review_status":"approved"}],"facts":[]}',encoding='utf8')
            with patch.object(cg,'KNOWLEDGE',Path(d)):
                g=cg.build_guide({'category':'printer'},as_of=date(2026,11,27))
            self.assertFalse(any('self-approved' in c['source_ids'] for c in g['claims']))
            self.assertFalse(any(c['evidence_status']=='supported' for c in g['claims'] if c['id'] in cg.REVIEWED_EXAMPLES))

    def test_reviewed_model_claims_expire(self):
        g=cg.build_guide({'category':'printer'},as_of=date(2030,1,1))
        self.assertFalse(any(c['evidence_status']=='supported' for c in g['claims'] if c['id'] in cg.REVIEWED_EXAMPLES))

    def test_source_revision_withdrawal_does_not_change_independent_facts(self):
        from shopping_decision import guide_binding as gb
        from test_cost_scenario_binding import relaxed
        from test_session_decision_contract import public
        from copy import deepcopy
        s=submit_message(relaxed(),'idle_weeks_pattern','经常连续多周不用')
        before=render_chat(deepcopy(s))
        original=json.loads(gb.REGISTRY.read_text(encoding="utf8"))
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"registry.json"
            for row in ({"revision":1,"status":"withdrawn"},{"revision":2,"status":"active"}):
                original["sources"]["rtings-cost-method-2021"]=row
                f.write_text(json.dumps(original),encoding="utf8")
                with patch.object(gb,"REGISTRY",f):
                    after=render_chat(deepcopy(s))
                c=json.loads(after["cognition_context_json"]);old=json.loads(before["cognition_context_json"])
                self.assertNotEqual(c["guide_version"],old["guide_version"])
                self.assertEqual(c["user_confirmed"],old["user_confirmed"])
                self.assertEqual(public(after)["claims"],public(before)["claims"])
                self.assertEqual(c["usage_research"]["source_ids"],[])
                self.assertEqual(next(x for x in c["cognition_claims"] if x["id"]=="guide-cost-method")["evidence_status"],"pending")
                self.assertEqual(next(x for x in c["cognition_claims"] if x["id"]=="guide-functions")["evidence_status"],"supported")

    def test_corrupt_registry_does_not_approve_claims(self):
        from shopping_decision import guide_binding as gb
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"registry.json";f.write_text('{"schema_version":1,"schema_version":1}')
            with patch.object(gb,"REGISTRY",f):
                g=cg.build_guide({"category":"printer"})
            self.assertFalse(any(c["evidence_status"]=="supported" for c in g["claims"]))

if __name__=='__main__':
    unittest.main()
