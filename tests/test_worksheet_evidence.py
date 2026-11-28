import unittest
from test_decision_worksheet import call,ws,filled
from test_cost_scenario_binding import relaxed
from test_session_decision_contract import public
from shopping_decision.cost_scenario import dependency_fingerprints

def source(**kw):
    return dict(dict(id='local1',candidate='HP M232dw',kind='quote_lead',locator='本地摘录第1段',observed_at='2020-01-01',excerpt='合成报价测试'),**kw)
class Evidence(unittest.TestCase):
    def setUp(self):self.s=relaxed();self.v=filled(self.s);self.w=ws(self.v)
    def test_import_pending(self):
        v=call(self.s,'import_source',self.w,source())
        self.assertEqual(ws(v)['sources'][0]['status'],'pending_review')
        self.assertIn('历史报价线索',v['worksheet_sources'])
        self.assertEqual(public(v)['claims'],public(self.v)['claims'])
    def test_wrong_model(self):
        self.assertIn('型号不适用',call(self.s,'import_source',self.w,source(candidate='other'))['worksheet_sources'])
    def test_forgery(self):
        with self.assertRaises(ValueError):call(self.s,'import_source',self.w,source(status='approved'))
    def test_version_withdraw(self):
        w=ws(call(self.s,'import_source',self.w,source()))
        w=ws(call(self.s,'import_source',w,source(excerpt='新版本')))
        self.assertEqual(w['sources'][0]['version'],2)
        self.assertEqual(ws(call(self.s,'withdraw_source',w,{'id':'local1'}))['sources'][0]['status'],'withdrawn')
    def test_reference_withdraw(self):
        c='HP M232dw';fid=next(iter(dependency_fingerprints(public(self.v),c)))
        p={'candidate':c,'fact_id':fid}
        w=ws(call(self.s,'bind_reference',self.w,p))
        v=call(self.s,'withdraw_reference',w,p)
        self.assertIsNone(public(v)['cost_comparison']['scenario_preference'])
        self.assertEqual(public(v)['claims'],public(self.v)['claims'])
    def test_unknown_reference(self):
        with self.assertRaises(ValueError):call(self.s,'bind_reference',self.w,{'candidate':'HP M232dw','fact_id':'invented'})

    def test_pending_conflict_not_admitted(self):
        first=call(self.s,'import_source',self.w,source(excerpt='假设报价600'))
        second=call(self.s,'import_source',ws(first),source(id='local2',excerpt='假设报价800'))
        self.assertIn('待核冲突',second['worksheet_sources'])
        self.assertEqual(public(second)['claims'],public(self.v)['claims'])
    def test_actual_gate_same_id_version_change(self):
        from unittest.mock import patch
        from test_session_decision_contract import bundle
        from shopping_decision.evidence_comparison import digest
        b=bundle(self.s)
        with patch('shopping_decision.chat_bridge._analysis',return_value={'recommendation':{'status':'research'},'verified_research_bundle':b}):
            v=filled(self.s)
            ref={'candidate':'HP M232dw','fact_id':'hp-replace-on-quality'}
            old=call(self.s,'bind_reference',ws(v),ref)
        src=next(x for x in b['sources'] if x.get('snapshot'))
        src['snapshot']['body']['version']+='; controlled new edition'
        src['snapshot']['sha256']=digest(src['snapshot']['body'])
        with patch('shopping_decision.chat_bridge._analysis',return_value={'recommendation':{'status':'research'},'verified_research_bundle':b}):
            new=call(self.s,'preview',ws(old))
        self.assertIsNotNone(public(old)['cost_comparison']['scenario_preference'])
        self.assertEqual(public(new)['cost_comparison']['reasons']['HP M232dw'],'dependency_version_changed')
        self.assertIsNone(public(new)['cost_comparison']['scenario_preference'])
        self.assertEqual(ws(old)['confirmed'],ws(new)['confirmed'])
        self.assertEqual([(x['candidate_id'],x['research_status']) for x in public(old)['assessments']],[(x['candidate_id'],x['research_status']) for x in public(new)['assessments']])
