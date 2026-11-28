import json, unittest
from copy import deepcopy
from shopping_decision.chat_bridge import new_dialogue,submit_message,render_chat,confirmed_values
from test_cost_scenario_binding import relaxed
from test_session_decision_contract import public

def rough():
    s=new_dialogue()
    for f,a in [('category','打印机'),('usage','家里想买打印机，不懂参数')]:
        s=submit_message(s,f,a)
    return s

def context(view):return json.loads(view['cognition_context_json'])
def task(view):return context(view)['usage_research']

class GuidedRequirements(unittest.TestCase):
    def test_explicit_confirmation_changes_research_not_eligibility(self):
        s=relaxed();before=render_chat(deepcopy(s))
        s2=submit_message(deepcopy(s),'idle_weeks_pattern','经常连续多周不用')
        after=render_chat(s2)
        self.assertEqual(task(before)['answer_state'],'unanswered')
        self.assertEqual(task(after)['answer_state'],'confirmed')
        self.assertIn('连续多周不用后的恢复步骤',after['result_text'])
        self.assertEqual(task(after)['answer'],'often_long')
        self.assertFalse(task(after)['hard_requirement'])
        self.assertEqual([(a['candidate_id'],a['research_status']) for a in public(before)['assessments']],
                         [(a['candidate_id'],a['research_status']) for a in public(after)['assessments']])
        regular=render_chat(submit_message(s2,'idle_weeks_pattern','通常每周都会用'))
        self.assertNotEqual(task(after)['question'],task(regular)['question'])
        self.assertEqual(task(regular)['answer'],'usually_short')
    def test_defer_withdraw_and_reconfirm(self):
        s=submit_message(rough(),'idle_weeks_pattern','经常连续多周不用')
        s=submit_message(s,'idle_weeks_pattern','暂不确定')
        self.assertNotIn('idle_weeks_pattern',confirmed_values(s))
        self.assertEqual(task(render_chat(s))['answer_state'],'deferred')
        s=submit_message(s,'idle_weeks_pattern','通常每周都会用')
        s=submit_message(s,'idle_weeks_pattern','撤回')
        self.assertEqual(task(render_chat(s))['answer_state'],'withdrawn')
        self.assertNotIn('idle_weeks_pattern',confirmed_values(s))
    def test_reject_bad_type_and_cross_category(self):
        s=rough()
        with self.assertRaises(ValueError):submit_message(s,'idle_weeks_pattern','一定要激光')
        wrong=submit_message(s,'category','手机')
        with self.assertRaises(ValueError):submit_message(wrong,'idle_weeks_pattern','经常连续多周不用')
        s=submit_message(s,'idle_weeks_pattern','经常连续多周不用')
        s['answers']['idle_weeks_pattern']['value']=True
        with self.assertRaises(ValueError):render_chat(s)
    def test_guide_is_readonly_and_color_routes(self):
        s=rough();v=render_chat(s)
        self.assertEqual(json.loads(v['state_json']),s)
        self.assertEqual(v['prompt_field'],'needs_color')
        t=submit_message(s,'needs_color','是')
        self.assertEqual(next(r for r in context(render_chat(t))['route_basis'] if r['id']=='mono_laser')['status'],'not_fit')
        self.assertNotIn('idle_weeks_pattern',confirmed_values(t))
