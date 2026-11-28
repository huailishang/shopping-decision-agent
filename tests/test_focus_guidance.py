import json, unittest
from copy import deepcopy
from shopping_decision.chat_bridge import new_dialogue, submit_message, render_chat

def state(usage):
    return submit_message(submit_message(new_dialogue(),"category","打印机"),"usage",usage)
def focus(v):return json.loads(v["guidance_focus_json"])
class FocusGuidance(unittest.TestCase):
    def test_scan_and_duplex_different(self):
        for usage,field in (("扫描存档","requires_scan"),("需要自动双面","requires_auto_duplex"),("经常连续多周不用","idle_weeks_pattern")):
            s=state(usage);v=render_chat(deepcopy(s));f=focus(v)
            self.assertEqual(f["field"],field);self.assertEqual(v["prompt_field"],field)
            self.assertEqual(f["question"],v["prompt"])
            self.assertEqual(json.loads(v["state_json"]),s)
            self.assertNotIn(field,s["answers"])
    def test_explicit_color_changes_route(self):
        s=state("在家打印彩色照片");v=render_chat(s)
        after=render_chat(submit_message(s,v["prompt_field"],"是"))
        self.assertEqual(focus(after)["status"],"research")
        self.assertEqual(after["prompt_field"],"")
        self.assertIn("黑白",after["prompt"])
        self.assertFalse(focus(after)["transactions_enabled"])
    def test_defer_and_withdraw_not_reasked(self):
        s=state("扫描存档")
        d=submit_message(deepcopy(s),"requires_scan","暂不确定")
        self.assertNotEqual(render_chat(d)["prompt_field"],"requires_scan")
        w=submit_message(submit_message(s,"requires_scan","是"),"requires_scan","撤回")
        self.assertNotEqual(render_chat(w)["prompt_field"],"requires_scan")
        self.assertIn("requires_scan",w["withdrawn_fields"])
    def test_hardware_scope_real_state(self):
        from test_worksheet_bridge import bridge
        s=submit_message(state("只算主机"),"budget_scope","仅主机硬件")
        v=bridge(s,"guide")
        self.assertNotIn("error",v)
        self.assertEqual(json.loads(v["state_json"]),s)
