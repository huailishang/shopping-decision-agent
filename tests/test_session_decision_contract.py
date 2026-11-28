import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from shopping_decision.chat_bridge import new_dialogue, submit_message, render_chat

def family():
    s=new_dialogue()
    for f,a in (('category','打印机'),('usage','低频家庭打印'),('needs_color','否'),
        ('accepts_outsourced_color','是'),('monthly_pages_range','0-50'),('budget_max_cny','1000'),
        ('device_deployment_region','中国大陆河南省'),('wechat_required','必须'),
        ('wechat_workflow','小程序'),('accepts_initial_setup','接受')):
        s=submit_message(s,f,a)
    return s

def answer(s,f,a):
    return submit_message(deepcopy(s),f,a)

def audit(v):
    return json.loads(v['report_json'])

def public(v):
    a=audit(v)
    return a['cognition_comparison']['public'] if a.get('cognition_comparison') else a['public_decision']

def bundle(s):
    return deepcopy(audit(render_chat(deepcopy(s)))['cognition_comparison']['bundle'])

def backend(s,b=None,**kwargs):
    if b is None: b=bundle(s)
    with patch('shopping_decision.chat_bridge._analysis',return_value={'recommendation':{'status':'research'},'verified_research_bundle':b}):
        return render_chat(deepcopy(s),**kwargs)

def first(v):
    p=public(v)
    a=p['next_actions'][0] if p['next_actions'] else None
    if not a:return None
    c=next((c for c in p['claims'] if c['candidate_id']==a.get('candidate_id') and c['requirement_id']==a.get('requirement_id')),None)
    return (a['kind'],c['dimension'] if c else a.get('requirement_id'),None if a['kind']=='clarify' else a.get('candidate_id'))

class SessionContract(unittest.TestCase):
    def check_pair(self,s):
        a,b=render_chat(deepcopy(s)),backend(s)
        self.assertEqual(first(a),first(b))
        self.assertEqual(public(a)['decision_binding']['session'],public(b)['decision_binding']['session'])
        for v in (a,b):
            self.assertFalse(audit(v)['purchase_recommendation_approved'])
        return a,b
    def test_unanswered(self):
        a,b=self.check_pair(family())
        self.assertEqual(a['prompt_field'],'requires_scan')
        self.assertEqual(b['prompt_field'],'requires_scan')
    def test_deferred(self):
        s=answer(family(),'requires_scan','暂不确定')
        a,b=self.check_pair(s)
        for v in (a,b):
            self.assertNotEqual(v['prompt_field'],'requires_scan')
            self.assertEqual(public(v)['decision_binding']['session']['fields']['requires_scan'],'deferred')
    def test_no_scan(self):
        a,b=self.check_pair(answer(family(),'requires_scan','否'))
        self.assertNotEqual(a['prompt_field'],'requires_scan')
    def test_no_both(self):
        a,b=self.check_pair(answer(answer(family(),'requires_scan','否'),'requires_auto_duplex','否'))
        self.assertNotEqual(first(a)[0],'clarify')
    def test_revise_withdraw(self):
        s=answer(family(),'requires_scan','是')
        self.check_pair(s)
        s=answer(s,'requires_scan','撤回')
        a,b=self.check_pair(s)
        self.assertEqual(public(a)['decision_binding']['session']['fields']['requires_scan'],'withdrawn')
        self.assertNotIn('requires_scan',audit(a)['confirmed_fields'])
    def test_color_failure(self):
        a,b=self.check_pair(answer(family(),'needs_color','是'))
        self.assertTrue(all(x['research_status']=='excluded_for_research' for x in public(a)['assessments']))
        self.assertIsNone(first(a))
    def test_setup_rejection(self):
        self.check_pair(answer(family(),'accepts_initial_setup','不接受'))
