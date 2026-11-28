import json,unittest
from test_focus_guidance import state,focus
from test_worksheet_bridge import bridge
from shopping_decision.chat_bridge import render_chat,submit_message

class FocusBridge(unittest.TestCase):
    def test_same_projection(self):
        s=state("扫描存档");v=bridge(s,"guide");normal=render_chat(s)
        self.assertEqual(focus(v),focus(normal))
        self.assertEqual(focus(v),json.loads(v["cognition_context_json"])["guidance_focus"])
        self.assertEqual(focus(v),json.loads(v["decision_note_json"])["guidance_focus"])
        self.assertEqual(v["guidance_focus_text"],focus(v)["explanation"])
    def test_restore_recomputes_not_cached(self):
        from shopping_decision.chat_bridge import new_dialogue
        s=state("连续多周不用");s=submit_message(s,"idle_weeks_pattern","经常连续多周不用")
        v=bridge(s,"create");w=json.loads(v["worksheet_json"])
        self.assertNotIn("guidance_focus",w)
        fresh=bridge(new_dialogue(),"restore",w,{"confirm_saved_conditions":True})
        self.assertNotIn("error",fresh)
        self.assertEqual(focus(fresh)["state_version"],json.loads(fresh["state_json"])["version"])
        self.assertNotEqual(focus(fresh)["field"],"idle_weeks_pattern")
    def test_reject_injected_focus(self):
        s=state("扫描存档")
        v=bridge(s,"guide",p={"guidance_focus":{"field":"budget_scope"}})
        self.assertIn("error",v)

    def test_unsupported_category_does_not_offer_hidden_question(self):
        from shopping_decision.chat_bridge import new_dialogue
        s=submit_message(new_dialogue(),"category","手机")
        v=bridge(s,"guide");normal=render_chat(s)
        self.assertEqual(focus(v),focus(normal))
        self.assertEqual(focus(v)["status"],"unsupported")
        self.assertIsNone(focus(v)["field"])
        self.assertEqual(v["prompt_field"],"")
        self.assertEqual(v["choices"],"")
        self.assertEqual(json.loads(v["state_json"]),s)
