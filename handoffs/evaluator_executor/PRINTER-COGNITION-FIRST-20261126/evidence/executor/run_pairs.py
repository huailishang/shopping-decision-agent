"""Same-source, same-oracle paired product-entry experiment; not a human study."""
from pathlib import Path
import json,hashlib,sys,subprocess,base64,time
from datetime import date
E=Path(__file__).resolve().parent;ROOT=E.parents[4]
sys.path.insert(0,str(ROOT))
from shopping_decision.chat_bridge import new_dialogue,submit_message,confirmed_values
def read(p):return json.loads(p.read_text(encoding='utf8'))
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return ref(p)
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def sha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def call(s,guide=False):
    argv=[sys.executable,'-X','utf8','-m','shopping_decision.chat_bridge']
    if guide:
        argv+=['--worksheet-stdin'];raw=json.dumps(dict(schema_version=1,action='guide',state=s,worksheet=None,payload={}),ensure_ascii=False).encode()
    else:
        argv += [base64.b64encode(x.encode()).decode() for x in (json.dumps(s,ensure_ascii=False),'','')];raw=None
    t=time.monotonic();p=subprocess.run(argv,cwd=ROOT,input=raw,capture_output=True,timeout=30)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
    result={k:base64.b64decode(v).decode() for k,v in (l.split('\t',1) for l in p.stdout.decode().splitlines())}
    if 'error' in result:raise RuntimeError(result['error'])
    return {'request':s,'operation':'guide' if guide else 'normal','elapsed_ms':round((time.monotonic()-t)*1000),'response':result}
def main():
    spec=read(E/'paired-reference-v1.json')
    if spec['as_of']!=date.today().isoformat():raise RuntimeError('date changed: preregister a new run')
    snapshot=read(E/'B1-shared-product-snapshot.json')
    for p,h in snapshot['sha256'].items():
        if ref(ROOT/p)['sha256']!=h:raise RuntimeError('B1 drift '+p)
    pairs=[]
    for c in spec['cases']:
        initial={'category':'printer','usage':c['usage']}
        basis={'initial_request_sha256':sha(initial),'source_set_sha256':snapshot['source_set']['sha256'],'user_profile_sha256':sha(c['oracle']),'as_of':spec['as_of'],'max_answer_turns':16,'max_read_requests':2}
        pair={'id':c['id'],'basis':basis,'reference_artifacts':[ref(E/'paired-reference-v1.json'),ref(E/'source-claims.json')]}
        for arm in ('a','b'):
            s=new_dialogue()
            for f,a in [('category','打印机'),('usage',c['usage'])]:s=submit_message(s,f,a)
            start=call(s,guide=(arm=='b'))
            guide=json.loads(start['response']['cognition_guide_json'])
            # Same oracle; direct arm receives all parameter names and may ask every field.
            # Guided arm sees same parameters organized by the guide before making choices.
            keys=list(c['oracle'])
            if arm=='b':
                primary=[d['question_field'] for d in guide['dimensions'] if d['question_field'] in keys]
                keys=list(dict.fromkeys(primary+keys))
            turns=[]
            for f in keys:
                prior=s['version'];s=submit_message(s,f,c['oracle'][f])
                turns.append(dict(field=f,answer=c['oracle'][f],prior_version=prior,version=s['version']))
            end=call(s)
            view=end['response'];r=json.loads(view['report_json']);ctx=json.loads(view['cognition_context_json'])
            route=next(x for x in ctx['route_basis'] if x['id']==c['expected_route']['id'])
            expected_known={k for k,v in c['oracle'].items() if v!='暂不确定'}
            expected_deferred={k for k,v in c['oracle'].items() if v=='暂不确定'}
            omission=sorted(expected_known-set(ctx['user_confirmed']))
            incorrect=sorted(expected_deferred-set(r['deferred_fields']))
            safety=bool(r['purchase_recommendation_approved'] or r['transactions_enabled'] or r['live_price_verified'])
            metrics={'missing_fields':omission,'missing_deferrals':incorrect,'route_correct':route['status']==c['expected_route']['status'],'idle_correct':ctx['usage_research']['answer']==c['expected_idle'],'safety_error':safety,'answer_turns':len(turns),'read_requests':2,'extra_guide_read':int(arm=='b'),'elapsed_ms':start['elapsed_ms']+end['elapsed_ms']}
            decision=(r.get('cognition_comparison') or {}).get('public') or r.get('public_decision') or {}
            # Compare business-level result (not version/order-dependent hashes).
            output={'metrics':metrics,'confirmed':ctx['user_confirmed'],'routes':ctx['route_basis'],'usage_research':ctx['usage_research'],'assessments':decision.get('assessments',[]),'next_step':view['prompt'],'unknowns':ctx['unknowns']}
            raw=put(E/(c['id']+'-'+arm+'.json'),dict(basis=basis,arm=arm,start=start,oracle_turns=turns,end=end,output=output))
            pair[arm]={'basis':basis,'output':output,'raw_artifacts':[raw]}
        a,b=pair['a']['output'],pair['b']['output']
        def errors(x):
            m=x['metrics'];return len(m['missing_fields'])+len(m['missing_deferrals'])+int(not m['route_correct'])+int(not m['idle_correct'])+int(m['safety_error'])
        ea,eb=errors(a),errors(b)
        pair['outcome']='improved' if eb<ea else 'regressed' if eb>ea else 'equal'
        pair['limitations']='固定合成oracle，直接组同样允许完整参数澄清；不测真人理解。决策正确性相同时，指南阅读是额外认知步骤，不能宣称净收益。耗时仅本机观测。'
        pairs.append(pair)
        print(c['id'],pair['outcome'],ea,eb,'turns',a['metrics']['answer_turns'],b['metrics']['answer_turns'],flush=True)
    put(E/'comparisons.json',{'schema_version':1,'pairs':pairs})
if __name__=='__main__':main()
