import json,unittest
from copy import deepcopy
from datetime import date
from unittest.mock import patch
from shopping_decision import cognition_comparison as cog
from shopping_decision.chat_bridge import render_chat,submit_message
from shopping_decision.action_ranking import accept_ranking
from test_action_ranking import state,fake,ROUTE
from test_guided_requirements import context

class ContextLineage(unittest.TestCase):
    def test_actual_ranking_consumes_guide_and_refuses_stale(self):
        s=submit_message(state(),'idle_weeks_pattern','经常连续多周不用')
        pack=cog.load_pack()
        for src in pack['sources']:src.pop('observed_at',None)
        with patch.object(cog,'load_pack',return_value=pack),patch('shopping_decision.chat_bridge.date') as clock:
            clock.today.return_value=date(2026,11,27)
            v=render_chat(deepcopy(s),ranking_route=ROUTE,ranking_transport=fake,ranking_budget={'input_cap':28000})
        comp=json.loads(v['report_json'])['cognition_comparison']
        audit=comp['ranking_audit']
        self.assertTrue(audit['business_accepted'],audit.get('reason'))
        plan=audit['plan'];p=plan['packet']['required']
        self.assertEqual(p['cognition_context'],context(v))
        self.assertEqual(p['cognition_context']['usage_research']['answer'],'often_long')
        stale=deepcopy(p['cognition_context']);stale['guide_version']='older'
        with self.assertRaisesRegex(ValueError,'stale_cognition_context'):
            accept_ranking(comp['public'],plan,{'context_id':p['context_id'],'action_ids':plan['action_ids']},cognition_context=stale)
        self.assertEqual(audit['external_api_calls'],0)
    def test_required_guide_over_budget_refuses_transport(self):
        s=state();pack=cog.load_pack()
        for src in pack['sources']:src.pop('observed_at',None)
        def forbidden(_):raise AssertionError('transport called despite cap')
        with patch.object(cog,'load_pack',return_value=pack),patch('shopping_decision.chat_bridge.date') as clock:
            clock.today.return_value=date(2026,11,27)
            v=render_chat(s,ranking_route=ROUTE,ranking_transport=forbidden,ranking_budget={'input_cap':500})
        a=json.loads(v['report_json'])['cognition_comparison']['ranking_audit']
        self.assertFalse(a['business_accepted'])
        self.assertEqual(a['reason'],'required_wire_over_budget')
