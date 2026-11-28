import json,unittest,tempfile
from pathlib import Path
from shopping_decision.chat_bridge import new_dialogue
from test_decision_worksheet import ws,filled,change
from test_worksheet_bridge import bridge,raw_call
from test_cost_scenario_binding import relaxed
from test_session_decision_contract import answer,public

class Persistence(unittest.TestCase):
    def setUp(self):self.s=relaxed();self.w=ws(filled(self.s,bridge))
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'work.json';p.write_text(json.dumps(self.w),encoding='utf8')
            v=bridge(new_dialogue(),'restore',json.loads(p.read_text()),{'confirm_saved_conditions':True})
        self.assertEqual(public(v)['cost_comparison']['scenario_preference'],'HP M232dw')
        self.assertEqual(ws(v)['confirmed'],self.w['confirmed'])
    def test_inspect(self):
        v=bridge(new_dialogue(),'inspect',self.w)
        self.assertEqual(v['status'],'preview')
        self.assertNotIn('result_text',v)
    def test_no_consent(self):self.assertIn('error',bridge(new_dialogue(),'restore',self.w))
    def test_no_overwrite(self):
        self.assertIn('error',bridge(answer(self.s,'usage','另一需求'),'restore',self.w,{'confirm_saved_conditions':True}))
    def test_no_cached_conclusion(self):
        self.w['winner']='伪造'
        self.assertIn('error',bridge(new_dialogue(),'restore',self.w,{'confirm_saved_conditions':True}))
    def test_only_inputs(self):
        self.assertNotIn('history',self.w);self.assertNotIn('purchase_authorization',self.w)
        self.assertEqual(self.w['models']['HP M232dw']['values']['starter'],0)
