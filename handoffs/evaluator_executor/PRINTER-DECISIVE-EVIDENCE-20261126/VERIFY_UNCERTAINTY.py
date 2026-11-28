"""Frozen public-protocol checks, using a simple independent arithmetic oracle."""
from copy import deepcopy
import json,sys
from VERIFY_ACTION import bridge,filled,ws,change,relaxed,public,family

def variable(cid,field,low,high):return dict(candidate=cid,field=field,low=low,high=high)
def analyze(s,w,variables):
    v=bridge(s,'analyze_uncertainty',w,{'variables':variables})
    if 'error' in v:raise AssertionError('analysis unavailable: '+v['error'])
    if 'uncertainty_json' not in v:raise AssertionError('missing uncertainty_json')
    p=json.loads(v['uncertainty_json'])
    assert p['schema_version']==1 and p['assumption_only'] is True
    for k in ('status','current_preference','robust_preference','factors','next_action'):assert k in p,k
    assert isinstance(p['factors'],list)
    assert isinstance(p['next_action'],dict)
    for k in ('kind','candidate','field','description'):assert k in p['next_action'],k
    for x in variables:assert any(all(row.get(k)==x[k] for k in ('candidate','field','low','high')) for row in p['factors']),x
    assert json.loads(v['report_json'])['purchase_recommendation_approved'] is False
    return v,p

def main():
    rows=[];s=relaxed();v=filled(s);w=ws(v)
    def check(name,fn):
        try:result=fn();rows.append(dict(id=name,passed=True,observed=result))
        except Exception as exc:rows.append(dict(id=name,passed=False,error=repr(exc)))
    def maintenance():
        _,p=analyze(s,w,[variable('HP M232dw','maintenance',0,100)])
        assert p['status']=='sensitive' and p['robust_preference'] is None
        assert p['next_action']['candidate']=='HP M232dw' and p['next_action']['field']=='maintenance'
        return p
    def stable():
        _,p=analyze(s,w,[variable('HP M232dw','maintenance',0,40)])
        assert p['status']=='robust' and p['robust_preference']=='HP M232dw'
        return p
    def adjacent():
        result=[]
        # This oracle does not call the production cost function.
        for x in ('49.999999','50','50.000001'):
            from decimal import Decimal
            hp=Decimal(650)+Decimal(x);brother=Decimal(700)
            expected='HP M232dw' if hp<brother else 'Brother HL-L1238W' if hp>brother else None
            point=bridge(s,'edit',w,change('HP M232dw','maintenance',x))
            _,p=analyze(s,ws(point),[variable('HP M232dw','maintenance',x,x)])
            assert p['robust_preference']==expected,(x,p)
            assert public(point)['cost_comparison']['scenario_preference']==expected
            result.append({'value':x,'expected':expected,'analysis':p})
        return result
    def staircase():
        result=[]
        for x,expected in [(299,'HP M232dw'),(300,'Brother HL-L1238W')]:
            # ceil((1800-starter)/1500) pieces, not fractional cartridges.
            total=500+((max(0,1800-x)+1499)//1500)*100
            assert total==(700 if x==299 else 600)
            point=bridge(s,'edit',w,change('Brother HL-L1238W','starter',x))
            _,p=analyze(s,ws(point),[variable('Brother HL-L1238W','starter',x,x)])
            assert p['robust_preference']==expected
            result.append(p)
        return result
    def hard():
        st=family();iv=filled(st)
        _,p=analyze(st,ws(iv),[variable('HP M232dw','maintenance',0,40)])
        assert p['status']=='hard_conditions_first' and p['robust_preference'] is None
        return p
    def shared_pages():
        changes=[change(None,'pages',1)]
        for cid,h,y in [('Brother HL-L1238W',0,10),('HP M232dw',1,12)]:
            changes += [change(cid,'hardware',h),change(cid,'toner_yield',y),change(cid,'toner_price',10)]
        point=bridge(s,'edit_many',w,{'changes':changes})
        # At pages 1 and 13 Brother is cheaper, but at 11 HP is cheaper.
        oracle=[(n,10*((n+9)//10),1+10*((n+11)//12)) for n in (1,11,13)]
        assert [a<b for _,a,b in oracle]==[True,False,True]
        _,p=analyze(s,ws(point),[variable(None,'pages',1,13)])
        assert p['status'] in ('sensitive','incomplete') and p['robust_preference'] is None,p
        return {'oracle':oracle,'analysis':p}
    def bad():
        results=[]
        for arr in [[variable('HP M232dw','maintenance',100,0)],[variable('other','maintenance',0,10)],[variable(None,'pages',False,10)],[variable('HP M232dw','maintenance',0,'1e1000000')],[variable('HP M232dw','maintenance',0,10)]*2]:
            got=bridge(s,'analyze_uncertainty',w,{'variables':arr})
            safe='error' in got
            if not safe and 'uncertainty_json' in got:safe=json.loads(got['uncertainty_json']).get('status')=='invalid'
            assert safe,got
            results.append(got)
        assert public(bridge(s,'preview',w))['cost_comparison']==public(v)['cost_comparison']
        return results
    for name,fn in [('maintenance-target',maintenance),('bounded-stability',stable),('exact-tie-adjacent',adjacent),('integer-replacement-step',staircase),('shared-pages-endpoint-trap',shared_pages),('hard-priority',hard),('bad-range-recovery',bad)]:check(name,fn)
    print(json.dumps({'cases':rows,'passed':sum(x['passed'] for x in rows),'total':len(rows),'external_calls':0},ensure_ascii=False,indent=2))
    return int(not all(x['passed'] for x in rows))
if __name__=='__main__':raise SystemExit(main())
