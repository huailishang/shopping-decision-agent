import json,unittest
from shopping_decision.chat_bridge import new_dialogue,submit_message
from test_worksheet_bridge import bridge
from test_decision_worksheet import ws
from test_guided_requirements import context,task
from test_cost_scenario_binding import relaxed

class GuidePersistence(unittest.TestCase):
    def test_restore_confirmed_usage_fresh_process(self):
        s=submit_message(relaxed(),'idle_weeks_pattern','经常连续多周不用')
        before=bridge(s,'create')
        saved=ws(before)
        after=bridge(new_dialogue(),'restore',saved,{'confirm_saved_conditions':True})
        self.assertNotIn('error',after)
        self.assertEqual(task(after),task(before))
        self.assertEqual(context(after)['guide_version'],context(before)['guide_version'])
        self.assertFalse(json.loads(after['report_json'])['transactions_enabled'])
    def test_deferred_and_withdrawn_restore(self):
        for a,expected in [('暂不确定','deferred'),('撤回','withdrawn')]:
            s=submit_message(relaxed(),'idle_weeks_pattern','通常每周都会用')
            s=submit_message(s,'idle_weeks_pattern',a)
            v=bridge(s,'create')
            after=bridge(new_dialogue(),'restore',ws(v),{'confirm_saved_conditions':True})
            self.assertEqual(task(after)['answer_state'],expected)
            self.assertIsNone(task(after)['answer'])

    def test_guide_reference_is_not_a_cached_conclusion(self):
        s=submit_message(relaxed(),'idle_weeks_pattern','经常连续多周不用')
        v=bridge(s,'create');w=ws(v)
        self.assertEqual(w['guide_reference']['guide_version'],context(v)['guide_version'])
        w['guide_reference']['guide_version']='0'*64
        restored=bridge(new_dialogue(),'restore',w,{'confirm_saved_conditions':True})
        self.assertIn('guide_change_notice',restored)
        self.assertEqual(task(restored),task(v))
        self.assertEqual(ws(restored)['guide_reference']['guide_version'],context(restored)['guide_version'])
        self.assertEqual(ws(restored)['confirmed'],w['confirmed'])
        w['guide_reference']['winner']='HP'
        self.assertIn('error',bridge(new_dialogue(),'restore',w,{'confirm_saved_conditions':True}))

    def test_legacy_saved_input_migrates(self):
        s=relaxed();v=bridge(s,'create');w=ws(v)
        w.pop('guide_reference')
        restored=bridge(new_dialogue(),'restore',w,{'confirm_saved_conditions':True})
        self.assertEqual(ws(restored)['confirmed'],w['confirmed'])
        self.assertIn('guide_change_notice',restored)


    def test_decision_note_current_and_readonly(self):
        s=submit_message(relaxed(),'idle_weeks_pattern','经常连续多周不用')
        v=bridge(s,'create')
        n=json.loads(v['decision_note_json']);c=context(v)
        self.assertEqual(n['guide_version'],c['guide_version'])
        self.assertEqual(n['confirmed_requirements'],c['user_confirmed'])
        self.assertEqual(n['next_step'],v['prompt'])
        self.assertTrue(n['candidate_claims'])
        self.assertTrue(n['cognition_sources'])
        self.assertFalse(n['purchase_recommendation_approved'])
        self.assertFalse(n['transactions_enabled'])
        self.assertFalse(n['live_price_verified'])
        self.assertNotIn('decision_note_json',ws(v))
