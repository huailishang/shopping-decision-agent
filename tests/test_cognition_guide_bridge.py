import json,unittest
from test_worksheet_bridge import bridge
from test_guided_requirements import rough,context,task
from shopping_decision.chat_bridge import render_chat,submit_message

class GuideBridge(unittest.TestCase):
    def test_same_normal_and_subprocess(self):
        s=submit_message(rough(),'idle_weeks_pattern','经常连续多周不用')
        v=bridge(s,'guide')
        self.assertNotIn('error',v)
        self.assertEqual(json.loads(v['state_json']),s)
        self.assertEqual(context(v),context(render_chat(s)))
    def test_reject_extra_inputs(self):
        s=rough()
        for p in ({'review_status':'approved'},{'guide_id':'evil'},{'idle_weeks_pattern':'often_long'}):
            self.assertIn('error',bridge(s,'guide',p=p))
        self.assertIn('error',bridge(s,'guide',w={}))
