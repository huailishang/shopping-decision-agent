"""Independent compound holdouts; writes raw process I/O, never changes product."""
from pathlib import Path
import base64, copy, hashlib, json, subprocess, sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_session_decision_contract import family,answer,public,first
from test_cost_scenario_binding import relaxed
from test_decision_worksheet import req,ws,change

OUT=Path(__file__).resolve().parent/'holdouts-v2'
OUT.mkdir(exist_ok=True)
results=[]; serial=0
def bridge(s,a,w=None,p=None):
    global serial
    serial+=1
    raw=json.dumps(req(s,a,w,p),ensure_ascii=False).encode()
    run=subprocess.run([sys.executable,'-X','utf8','-m','shopping_decision.chat_bridge','--worksheet-stdin'],input=raw,capture_output=True,cwd=ROOT,timeout=30)
    stem=OUT/f'{serial:03d}-{a}'
    stem.with_suffix('.request.json').write_bytes(raw)
    stem.with_suffix('.stdout.txt').write_bytes(run.stdout)
    stem.with_suffix('.stderr.txt').write_bytes(run.stderr)
    assert run.returncode==0,run.stderr.decode(errors='replace')
    return {k:base64.b64decode(v).decode() for k,v in (x.split('\t',1) for x in run.stdout.decode().splitlines())}
def filled(s):
    w=ws(bridge(s,'create')); edits=[change(None,'pages',1800),change(None,'months',36)]
    for cid,h,p in [('Brother HL-L1238W',500,100),('HP M232dw',550,50)]:
        edits += [change(cid,k,v) for k,v in dict(hardware=h,starter=0,toner_yield=1500,toner_price=p,separate_drum=False,maintenance=0).items()]
    return bridge(s,'edit_many',w,{'changes':edits})
def record(name,fn):
    start=serial
    try:
        observed=fn();results.append(dict(id=name,passed=True,observed=observed,calls=[start+1,serial]))
    except Exception as exc:
        results.append(dict(id=name,passed=False,error=repr(exc),calls=[start+1,serial]))
def h1():
    s=answer(answer(answer(family(),'requires_scan','暂不确定'),'requires_auto_duplex','是'),'accepts_initial_setup','不接受')
    v=filled(s);p=public(v)
    assert p['cost_comparison']['scenario_preference'] is None
    assert 'requires_scan' in ws(v)['deferred']
    assert not json.loads(v['report_json'])['purchase_recommendation_approved']
    return {'first':first(v),'assessments':p['assessments'],'prompt':v['prompt']}
def h2():
    s=relaxed();v=filled(s);w=ws(v)
    src=dict(id='holdout',candidate='HP M232dw',kind='quote_lead',locator='合成非实时价',observed_at='2020-01-01',excerpt='旧报价，不可购买')
    v=bridge(s,'import_source',w,src)
    from shopping_decision.chat_bridge import new_dialogue
    v=bridge(new_dialogue(),'restore',ws(v),{'confirm_saved_conditions':True})
    s2=json.loads(v['state_json']);s2=answer(s2,'device_deployment_region','中国大陆北京市')
    reject=bridge(s2,'preview',ws(v)); assert 'error' in reject
    new=bridge(s2,'rebind',ws(v)); assert ws(new)['basis']['pages'] is None
    assert not ws(new)['sources']; np=public(new)
    assert np is None or np['cost_comparison'].get('scenario_preference') is None
    return {'restore_source':v['worksheet_sources'],'stale_error':reject,'new_cost':np['cost_comparison'] if np else None,'note':'region change may safely leave the comparison unavailable'}
def h3():
    s=relaxed();v=filled(s);w=ws(v)
    src=dict(id='rev',candidate='HP M232dw',kind='manufacturer_excerpt',locator='合成第1段',observed_at='2026-11-26',excerpt='v1')
    v=bridge(s,'import_source',w,src);v=bridge(s,'withdraw_source',ws(v),{'id':'rev'})
    src['excerpt']='v2';v=bridge(s,'import_source',ws(v),src)
    v=bridge(s,'edit',ws(v),change(None,'pages',3600))
    assert ws(v)['sources'][0]['version']==2 and ws(v)['sources'][0]['status']=='pending_review'
    assert public(v)['claims']==public(filled(s))['claims']
    return {'source':ws(v)['sources'],'cost':public(v)['cost_comparison']}
def h4():
    s=relaxed();v=filled(s);w=ws(v)
    for val in ('1000000000.000001','0.0000001','-0.1'):
        assert 'error' in bridge(s,'edit',w,change('HP M232dw','maintenance',val))
    ok=bridge(s,'edit',w,change('HP M232dw','maintenance','0.000001'))
    assert public(ok)['cost_comparison']['scenario_preference']=='HP M232dw'
    bad=copy.deepcopy(ws(ok));bad['authorization']=True;bad['winner']='HP M232dw'
    assert 'error' in bridge(s,'restore',bad)
    recovered=bridge(s,'preview',ws(ok)); assert public(recovered)['cost_comparison']==public(ok)['cost_comparison']
    return {'cost':public(ok)['cost_comparison'],'prompt':ok['prompt']}
def h5():
    s=relaxed();a=filled(s);b=bridge(s,'edit',ws(a),change('HP M232dw','maintenance',100))
    assert [public(v)['cost_comparison']['scenario_preference'] for v in (a,b)]==['HP M232dw','Brother HL-L1238W']
    observed={'before':{'result':a['result_text'],'prompt':a['prompt']},'after':{'result':b['result_text'],'prompt':b['prompt']},'changed':{'candidate':'HP M232dw','field':'maintenance','before':0,'after':100}}
    (OUT/'maintenance-flip.json').write_text(json.dumps(observed,ensure_ascii=False,indent=2),encoding='utf8')
    assert '维护' in b['prompt'], 'maintenance-only flip asks about starter yield/toner instead of decisive maintenance assumption'
    return observed
for name,fn in [('H01-defer-duplex-setup',h1),('H02-restore-region-expired',h2),('H03-source-revision-volume',h3),('H04-bounds-forgery-recover',h4),('H05-maintenance-decisive-action',h5)]:record(name,fn)
summary={'at':datetime.now(timezone.utc).isoformat(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results,'passed':sum(x['passed'] for x in results),'total':len(results),'real_external_calls':0}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
raise SystemExit(int(summary['passed']!=summary['total']))
