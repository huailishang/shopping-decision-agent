"""Replay six sampled original trajectories using each arm's own runtime."""
from independent_checks import *

def main():
    comparisons=load(EX/'comparisons.json');cases=['T03','T08','T10','T15','T16','T18'];out=[]
    for cid in cases:
        pair=next(p for p in comparisons['pairs'] if p['case_id']==cid)
        for arm in ['a','b']:
            folder=HERE/'sample-reruns'/cid/arm;folder.mkdir(parents=True,exist_ok=False)
            trace=load(ROOT/pair[arm]['replay']['path']);checks=[]
            with tempfile.TemporaryDirectory(prefix='eval-replay-') as d:
                base=Path(d);populate(base,current=arm=='b')
                for i,e in enumerate(trace['events']):
                    if e['type']!='response':continue
                    r=e['request'];v=call(base,folder,str(i),r['state'],r['action'],r['worksheet'],r['payload']);old=load(ROOT/e['response_artifact']['path'])
                    checks.append(dict(event=i,prompt_matches=v['prompt_field']==old['prompt_field'] and v['prompt']==old['prompt'],
                        state_matches=obj(v,'state_json')==obj(old,'state_json'),
                        source_matches=obj(v,'cognition_guide_json')['sources']==obj(old,'cognition_guide_json')['sources'],
                        candidate_matches=obj(v,'cognition_context_json')['candidate_facts']==obj(old,'cognition_context_json')['candidate_facts'],safe=safe(v)))
            row=dict(case_id=cid,arm=arm,checks=checks,passed=all(all(v for k,v in r.items() if k!='event') for r in checks));out.append(row)
            print(cid,arm,row['passed'],flush=True)
    # Exercise the actual comparison predicate against independently changed input/source/resource values.
    module_path=EX/'paired_replay.py';spec=importlib.util.spec_from_file_location('original_replayer',module_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    common=copy.deepcopy(comparisons['pairs'][0]['basis']);changed=copy.deepcopy(common);changed['source_set_sha256']='0'*64
    limited=copy.deepcopy(common);limited['limits']['max_product_calls']-=1
    mutations=dict(same=module.comparable(common,common),source_rejected=not module.comparable(common,changed),resource_rejected=not module.comparable(common,limited))
    save(HERE/'six-pair-rerun-results.json',dict(cases=out,comparability_mutations=mutations,all_passed=all(r['passed'] for r in out) and all(mutations.values())))
if __name__=='__main__':main()
