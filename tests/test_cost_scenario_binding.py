import unittest
from copy import deepcopy
from shopping_decision.cognition_comparison import lifecycle_cost,compare_lifecycle_costs
from shopping_decision.cost_scenario import evaluate_scenario
from test_session_decision_contract import family,answer,public,backend,bundle,render_chat

def inputs(**kw):
    return dict(dict(pages=1800,hardware=500,starter=0,toner_yield=1500,toner_price=100,separate_drum=False,maintenance=0,months=36,currency='CNY',fee_scope='hardware_consumables_maintenance',scenario_version=1),**kw)

def scenario(p,**kw):
    names=sorted(a['candidate_id'] for a in p['assessments'])
    return {'schema_version':1,'binding':{k:p['decision_binding'].get(k) for k in ('category','dialogue_version','confirmed_values_sha256','session')},
        'models':{names[0]:{'kind':'synthetic_scenario','inputs':inputs(**kw),'dependency_fact_ids':[],'dependency_fingerprints':{}},
                  names[1]:{'kind':'synthetic_scenario','inputs':inputs(hardware=550,toner_price=50),'dependency_fact_ids':[],'dependency_fingerprints':{}}}}

def relaxed():
    s=answer(answer(family(),'requires_scan','否'),'requires_auto_duplex','否')
    s=answer(s,'wechat_required','否')
    return answer(s,'budget_max_cny','撤回')

class CostBinding(unittest.TestCase):
    def test_same_basis(self):
        self.assertEqual(compare_lifecycle_costs(lifecycle_cost(**inputs()),lifecycle_cost(**inputs(hardware=550))),'a')
    def test_mismatch(self):
        for k,v in [('pages',0),('months',12),('currency','USD'),('scenario_version',2)]:
            self.assertEqual(compare_lifecycle_costs(lifecycle_cost(**inputs()),lifecycle_cost(**inputs(**{k:v}))),'incomparable')
    def test_numeric_and_unknown(self):
        for k,v in [('hardware',True),('pages',-1),('toner_yield',0),('maintenance',float('inf'))]:
            with self.assertRaises(ValueError): lifecycle_cost(**inputs(**{k:v}))
        self.assertIsNone(lifecycle_cost(**inputs(maintenance=None)))
        self.assertEqual(lifecycle_cost(**inputs(pages=1500,starter=1500))['toner_replacements'],0)
        self.assertEqual(lifecycle_cost(**inputs(pages=1501,starter=1500))['toner_replacements'],1)
    def test_flip_real_entry(self):
        s=relaxed(); p=public(render_chat(s)); a=scenario(p); b=scenario(p,starter=1500)
        views=[render_chat(deepcopy(s),cost_scenario=x) for x in (a,b)]
        names=sorted(a['models'])
        self.assertEqual([public(v)['cost_comparison']['scenario_preference'] for v in views],names[::-1])
        for v in views:self.assertIn('情景成本较低',v['result_text'])
    def test_pending_no_winner(self):
        s=family(); p=public(render_chat(s)); v=render_chat(s,cost_scenario=scenario(p))
        self.assertEqual(public(v)['cost_comparison']['status'],'hard_conditions_first')
        self.assertIsNone(public(v)['cost_comparison']['scenario_preference'])
    def test_stale(self):
        s=relaxed(); a=scenario(public(render_chat(s)))
        s=answer(s,'usage','家庭作业打印')
        v=render_chat(s,cost_scenario=a)
        self.assertEqual(public(v)['cost_comparison']['status'],'stale')
    def test_incomparable_real_entry(self):
        s=relaxed(); p=public(render_chat(s)); v=render_chat(s,cost_scenario=scenario(p,pages=0))
        self.assertEqual(public(v)['cost_comparison']['status'],'incomparable')
        self.assertIn('成本不可比',v['result_text'])

    def test_finite_bounded_money_and_units(self):
        for kw in ({"toner_price":"1e1000000"},{"hardware":"1000000000.01"},
                   {"toner_price":"0.0000001"},{"pages":10000001},{"months":1201}):
            with self.assertRaises(ValueError): lifecycle_cost(**inputs(**kw))
        self.assertEqual(lifecycle_cost(**inputs(pages=0,hardware="0.000001",maintenance=0))["total"],"0.000001")
    def test_finite_extreme_actual_entry_preserves_rule(self):
        s=family(); base=render_chat(s)
        extreme=scenario(public(base),toner_price="1e1000000")
        for v in (render_chat(s,cost_scenario=extreme),backend(s,cost_scenario=extreme)):
            cost=public(v)["cost_comparison"]
            self.assertEqual(cost["status"],"unknown")
            self.assertIn("输入或口径不合法",v["result_text"])
            self.assertIsNone(cost["scenario_preference"])
