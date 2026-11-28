"""Frozen scope/control/delivery audit. control_results.cases=[{case_id,arm}].
arm uses the preceding frozen MEASUREMENT replay schema. Three new journey
rows contain scenario_id and replay (same event schema), ending in actual
candidate scan/auto_duplex facts or usage_research with explicit idle answer.
"""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,subprocess,sys
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2];OLD=ROOT/'handoffs/evaluator_executor/PRINTER-FOCUSED-GUIDANCE-20261127'
sys.path.insert(0,str(ROOT))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def imported(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['scope','controls','delivery']);a=ap.parse_args();b=load(TASK/'BASELINE.json');errors=[]
    def need(value,message):
        if not value:errors.append(message)
    if a.phase=='scope':
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();index=subprocess.check_output(['git','diff','--cached','--binary','--no-ext-diff'],cwd=ROOT)
        need(head==b['baseline_head'],'HEAD changed');need(hashlib.sha256(index).hexdigest()==b['index_sha256'],'index changed')
        for name,digest in b['protected_sha256'].items():
            p=ROOT/name;need(p.is_file() and sha(p)==digest,'protected changed: '+name)
    elif a.phase=='controls':
        data=load(TASK/'evidence/executor/control_results.json');refs={c['case_id']:c for c in load(OLD/'evidence/executor/replay-reference-v2.json')['cases']}
        checker=imported('old_frozen_measurement',OLD/'VERIFY_MEASUREMENT.py');sem=imported('old_frozen_replayer',OLD/'evidence/executor/paired_replay.py')
        oldpairs={p['case_id']:p for p in load(OLD/'evidence/executor/comparisons.json')['pairs']}
        need(len(data['cases'])==24 and {x['case_id'] for x in data['cases']}==set(refs),'exact 24 controls')
        for row in data['cases']:
            cid=row['case_id'];arm=row['arm'];r=refs[cid];metrics=checker.inspect(arm,r);raw=load(ROOT/arm['replay']['path'])
            need(arm['basis']==oldpairs[cid]['b']['basis'],cid+' baseline/source/resource differs')
            responses=[e for e in raw['events'] if e['type']=='response'];view=load(ROOT/responses[-1]['response_artifact']['path'])
            need(metrics['completed'] and all(sem.semantic(view,r).values()),cid+' target not completed')
            first=load(ROOT/responses[0]['response_artifact']['path']);prior=load(ROOT/oldpairs[cid]['b']['replay']['path']);priorfirst=load(ROOT/next(e for e in prior['events'] if e['type']=='response')['response_artifact']['path'])
            need(json.loads(first['cognition_guide_json'])['sources']==json.loads(priorfirst['cognition_guide_json'])['sources'],cid+' source projections differ')
        errors.extend(checker.errors)
        journeys=load(TASK/'evidence/executor/journeys.json')['cases'];need(len(journeys)==3 and {r['scenario_id'] for r in journeys}=={'P01','P02','P03'},'three disclosed full journeys')
        expected={'P01':('requires_scan',True),'P02':('requires_auto_duplex',True),'P03':('idle_weeks_pattern','often_long')}
        from shopping_decision.chat_bridge import submit_message
        for row in journeys:
            raw=load(ROOT/row['replay']['path']);need(sha(ROOT/row['replay']['path'])==row['replay']['sha256'],'journey hash')
            current=raw['initial_state'];view=None
            for e in raw['events']:
                if e['type']=='response':
                    view=load(ROOT/e['response_artifact']['path']);need(e['request']['state']==current and json.loads(view['state_json'])==current,'journey injection')
                    stdout=(ROOT/e['stdout_artifact']['path']).read_text(encoding='utf8');need({k:base64.b64decode(v).decode() for k,v in (l.split('\t',1) for l in stdout.splitlines())}==view,'journey raw/decoded')
                elif e['type']=='answer':
                    need(view is not None and view['prompt_field']==e['field'],'journey answer not current');current=submit_message(current,e['field'],e['answer']);view=None
            need(view is not None,'missing terminal');ctx=json.loads(view['cognition_context_json']);field,value=expected[row['scenario_id']]
            need(ctx['user_confirmed'].get(field)==value,'missing explicit target')
            if field=='idle_weeks_pattern':need(ctx['usage_research']['status']=='research_required','no idle research')
            else:need(any(c['dimension']=={'requires_scan':'scan','requires_auto_duplex':'auto_duplex'}[field] for c in ctx['candidate_facts']),'no model evidence/next research')
            need(bool(view['prompt']),'no concrete next step')
    else:
        process=load(TASK/'evidence/executor/process.json');need(process.get('inherited_prior_unknown') is True,'lost prior unknown')
        need(process.get('budget_debit_seconds',float('inf'))<=43200,'12h budget');need(process.get('repair_rounds',99)<=2,'round limit')
        entries=[json.loads(l) for l in (TASK/'evidence/executor/activity.jsonl').read_text(encoding='utf8').splitlines() if l.strip()]
        need(bool(entries) and entries[0].get('event')=='start','missing contemporaneous start');need(any(x.get('event')=='end' for x in entries),'missing end')
        for u in process.get('unknown_segments',[]):need(u.get('independent_bound_artifacts') and u.get('upper_bound_seconds') is not None,'unverifiable upper bound')
        for name in ['REPORT.md','CONTROL_REPLAY.md','USAGE.md']:need((TASK/name).is_file(),'missing '+name)
        for item in load(TASK/'evidence/executor/manifest.json')['artifacts']:need(sha(ROOT/item['path'])==item['sha256'],'handoff hash '+item['path'])
    print(json.dumps(dict(phase=a.phase,errors=errors,limit='machine checks do not certify semantic relevance, timestamps or absence of external calls'),ensure_ascii=False));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
