"""Frozen checks on real product projections, not a parallel model-context helper."""
import json
from VERIFY_GUIDE import rough,bridge,guide,confirmed_values
from shopping_decision.chat_bridge import render_chat

def context(v,g,s):
    assert 'cognition_context_json' in v,'missing product cognition context'
    c=json.loads(v['cognition_context_json'])
    assert c['schema_version']==1
    assert c['guide_id']==g['guide_id'] and c['guide_version']==g['version']
    assert c['user_confirmed']==confirmed_values(s),'source/model overwrote user confirmation'
    for k in ('cognition_claims','route_basis','candidate_facts','unknowns'):assert isinstance(c[k],list),k
    assert c['cognition_claims'],'guide evidence missing from product context'
    ids={x['id'] for x in g['sources']}
    for claim in c['cognition_claims']:
        assert isinstance(claim,dict) and isinstance(claim.get('source_ids'),list),'untraceable cognition claim'
        assert set(claim['source_ids'])<=ids,'context references unrelated sources'
    return c
def main():
    rows=[]
    for name,s in [('coarse-novice',rough()),('explicit-color',rough(True))]:
        try:
            via=bridge(s);g=guide(via);c=context(via,g,s)
            normal=render_chat(s);ng=guide(normal);nc=context(normal,ng,s)
            assert (g['guide_id'],g['version'])==(ng['guide_id'],ng['version'])
            assert c==nc,'guide subprocess and normal chat context differ'
            rows.append(dict(id=name,passed=True,guide_id=g['guide_id'],guide_version=g['version'],context=c))
        except Exception as exc:rows.append(dict(id=name,passed=False,error=repr(exc)))
    print(json.dumps({'cases':rows,'passed':sum(x['passed'] for x in rows),'total':len(rows),'real_model_calls':0,'limit':'packet parity does not prove live model quality; actual ranking consumption and negative receipts are additionally required'},ensure_ascii=False,indent=2))
    return int(not all(x['passed'] for x in rows))
if __name__=='__main__':raise SystemExit(main())
