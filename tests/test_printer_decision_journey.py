import unittest
from copy import deepcopy
from test_session_decision_contract import family,answer,public,backend,bundle,render_chat,audit,first
from test_cost_scenario_binding import scenario,relaxed
class PrinterJourney(unittest.TestCase):
    def test_family_unknown(self):
        v=render_chat(family())
        self.assertEqual(public(v)['cost_comparison']['status'],'unknown')
        self.assertFalse(audit(v)['live_price_verified'])
    def test_backend_cost_flip(self):
        s=relaxed();p=public(backend(s));a=scenario(p);b=scenario(p,starter=1500)
        aa,bb=backend(s,cost_scenario=a),backend(s,cost_scenario=b)
        self.assertNotEqual(public(aa)['cost_comparison']['scenario_preference'],public(bb)['cost_comparison']['scenario_preference'])
        self.assertIn('情景成本较低',aa['result_text'])
    def test_dependency_withdrawal(self):
        s=relaxed();b=bundle(s);p=public(backend(s,b));a=scenario(p)
        hp=next(n for n in a['models'] if 'HP' in n)
        c=next(c for c in p['claims'] if c['candidate_id']==hp and c['status']=='met' and c['supporting_fact_ids'])
        fid=c['supporting_fact_ids'][0]
        a['models'][hp]['dependency_fact_ids']=[fid]
        from shopping_decision.cost_scenario import dependency_fingerprints
        a['models'][hp]['dependency_fingerprints']={fid:dependency_fingerprints(p,hp)[fid]}
        before=backend(s,b,cost_scenario=a)
        self.assertIsNotNone(public(before)['cost_comparison']['scenario_preference'])
        b['facts']=[f for f in b['facts'] if f['id']!=fid]
        after=backend(s,b,cost_scenario=a)
        self.assertEqual(public(after)['cost_comparison']['status'],'unknown')
        self.assertEqual(audit(before)['confirmed_fields'],audit(after)['confirmed_fields'])
    def test_no_candidate_resurrection(self):
        s=answer(family(),'needs_color','是')
        v=render_chat(s,cost_scenario=scenario(public(render_chat(s))))
        self.assertIsNone(public(v)['cost_comparison']['scenario_preference'])
        self.assertIsNone(first(v))

def hard_met_bundle(s):
    b=bundle(s)
    from datetime import date,timedelta
    today=date.today()
    for i,c in enumerate(b['candidates']):
        name=c['id'] if isinstance(c,dict) else c
        for j,r in enumerate(b['requirements']):
            if r['importance']!='hard':continue
            d=r['dimension']; fid=f'synthetic-{i}-{j}'
            b['facts']=[f for f in b['facts'] if not(f['candidate_id']==name and f['dimension']==d)]
            b['sources'].append({'id':fid,'url':'https://fixture.invalid/'+fid,'type':'synthetic','allowed_use':'model_research_short_summary','scope_models':[name],'scope_region':b['region'],'captured_on':today.isoformat(),'observed_at':today.isoformat()+'T00:00:00Z','valid_until':(today+timedelta(days=1)).isoformat(),'locator':'local fixture','limitations':'synthetic only'})
            b['facts'].append({'id':fid,'candidate_id':name,'source_id':fid,'dimension':d,'unit':r['unit'],'value':500 if r['unit']=='CNY' else r['value'],'kind':'synthetic_probe','scope_models':[name],'scope_region':b['region'],'statement':'synthetic only','limitations':'not real evidence'})
    return b

class HardSatisfiedJourney(unittest.TestCase):
    def test_original_hard_constraints_controlled(self):
        s=answer(answer(family(),'requires_scan','否'),'requires_auto_duplex','否')
        b=hard_met_bundle(s);p=public(backend(s,b))
        self.assertTrue(all(a['research_status']=='eligible_for_research' for a in p['assessments']))
        a=scenario(p);c=scenario(p,starter=1500)
        v1,v2=backend(s,b,cost_scenario=a),backend(s,b,cost_scenario=c)
        self.assertEqual([public(v)['cost_comparison']['scenario_preference'] for v in (v1,v2)],sorted(a['models'],reverse=True))


class EvidenceVersionJourney(unittest.TestCase):
    def test_same_id_new_version_invalidates_cost_only(self):
        from shopping_decision.cost_scenario import dependency_fingerprints
        s=relaxed();b=bundle(s);p=public(backend(s,b));a=scenario(p)
        hp=next(n for n in a['models'] if 'HP' in n)
        fid='hp-replace-on-quality'
        a['models'][hp].update(dependency_fact_ids=[fid],dependency_fingerprints={fid:dependency_fingerprints(p,hp)[fid]})
        before=backend(s,b,cost_scenario=a)
        self.assertIsNotNone(public(before)['cost_comparison']['scenario_preference'])
        src=next(x for x in b['sources'] if x.get('snapshot'))
        from shopping_decision.evidence_comparison import digest
        src['snapshot']['body']['version']+='; new edition'
        src['snapshot']['sha256']=digest(src['snapshot']['body'])
        after=backend(s,b,cost_scenario=a)
        cost=public(after)['cost_comparison']
        self.assertEqual(cost['status'],'unknown')
        self.assertEqual(cost['reasons'][hp],'dependency_version_changed')
        self.assertEqual(audit(before)['confirmed_fields'],audit(after)['confirmed_fields'])
        self.assertEqual([(x['candidate_id'],x['research_status']) for x in public(before)['assessments']],[(x['candidate_id'],x['research_status']) for x in public(after)['assessments']])
