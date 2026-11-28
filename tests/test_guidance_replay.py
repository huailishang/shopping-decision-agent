import json,unittest
from test_focus_guidance import state
from shopping_decision.chat_bridge import submit_message,render_chat
class ReplayDiscipline(unittest.TestCase):
    def test_follow_current_field_only_scan(self):
        s=state("扫描纸质资料存档")
        answers={"requires_scan":"是","needs_color":"否","device_deployment_region":"河南","monthly_pages_range":"0-50"}
        seen=[]
        for _ in range(4):
            v=render_chat(s);field=v["prompt_field"];self.assertIn(field,answers);self.assertNotIn(field,seen)
            seen.append(field);s=submit_message(s,field,answers[field])
        c=json.loads(render_chat(s)["cognition_context_json"])
        self.assertEqual(set(seen),set(answers))
        self.assertTrue(any(x["dimension"]=="scan" for x in c["candidate_facts"]))
    def test_idle_question_changes_research_not_answers(self):
        s=state("连续多周不用");v=render_chat(s)
        self.assertEqual(v["prompt_field"],"idle_weeks_pattern")
        after=render_chat(submit_message(s,v["prompt_field"],"经常连续多周不用"))
        c=json.loads(after["cognition_context_json"])
        self.assertIn("恢复步骤",c["usage_research"]["question"])
        self.assertNotIn("needs_color",c["user_confirmed"])
    def test_zero_pages_does_not_infer_idle(self):
        s=state("当前预计暂时没有要打印的资料")
        v=render_chat(s);self.assertEqual(v["prompt_field"],"monthly_pages_range")
        c=json.loads(render_chat(submit_message(s,v["prompt_field"],"0-0"))["cognition_context_json"])
        self.assertEqual(c["user_confirmed"]["monthly_pages_range"],[0,0])
        self.assertNotIn("idle_weeks_pattern",c["user_confirmed"])
