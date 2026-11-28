import unittest
from test_decision_worksheet import ws,filled,change
from test_worksheet_bridge import bridge
from test_cost_scenario_binding import relaxed
from test_session_decision_contract import family,public,first,answer
class Journeys(unittest.TestCase):
    def test_flip(self):
        s=relaxed();v=filled(s,bridge)
        t=bridge(s,'edit',ws(v),change('Brother HL-L1238W','starter',1500))
        self.assertEqual([public(x)['cost_comparison']['scenario_preference'] for x in (v,t)],['HP M232dw','Brother HL-L1238W'])
        self.assertNotEqual(first(v),first(t))
    def test_hard_pending(self):
        v=filled(family(),bridge);self.assertIsNone(public(v)['cost_comparison']['scenario_preference'])
        self.assertEqual(v['prompt_field'],'requires_scan')
    def test_clear(self):
        s=relaxed();v=filled(s,bridge)
        t=bridge(s,'clear',ws(v),change('HP M232dw','maintenance',0))
        self.assertIsNone(public(t)['cost_comparison']['scenario_preference'])
    def test_deferred(self):
        s=answer(family(),'requires_scan','暂不确定');v=filled(s,bridge)
        self.assertIn('requires_scan',ws(v)['deferred'])
    def test_rebuild(self):
        s=relaxed();v=filled(s,bridge);t=answer(s,'usage','新场景')
        self.assertIn('error',bridge(t,'preview',ws(v)))
        self.assertIsNone(ws(bridge(t,'rebind',ws(v)))['basis']['pages'])

    def test_shared_basis_reject_mixed_override(self):
        s=relaxed();v=filled(s,bridge)
        bad=bridge(s,'edit',ws(v),change('HP M232dw','currency','USD'))
        self.assertIn('error',bad)
        v2=bridge(s,'preview',ws(v))
        self.assertEqual(public(v)['cost_comparison'],public(v2)['cost_comparison'])
    def test_summary_preserves_audit(self):
        v=bridge(family(),'create')
        self.assertIn('硬条件待核',v['result_text'])
        self.assertIn('下一步：',v['result_text'])
        self.assertEqual(v['result_text'].count('下一步：'),1)
        self.assertNotIn('命题ID',v['result_text'])
        self.assertGreater(len(v['worksheet_detail_text']),len(v['result_text']))
        self.assertIn('HP M232dw',v['worksheet_sources'])
