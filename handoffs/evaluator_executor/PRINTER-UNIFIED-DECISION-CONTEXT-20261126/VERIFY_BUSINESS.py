"""Frozen evaluator cross-consumer probes. Old evidence is read-only."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sys
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))
from shopping_decision import cognition_comparison as cog
from shopping_decision.chat_bridge import new_dialogue, submit_message, render_chat, confirmed_values
from shopping_decision.claim_gate import publish_checked_comparison
from shopping_decision.evidence_comparison import digest

OLD = ROOT / 'handoffs/evaluator_executor/PRINTER-CANDIDATE-TRADEOFF-20261125/evidence/executor/model/web-gpt-20261125'

def inspect_public(public, bundle):
    reqs = {r['id']: r for r in bundle['requirements']}
    states = {a['candidate_id']: a['research_status'] for a in public['assessments']}
    excluded = {c for c,s in states.items() if s == 'excluded_for_research'}
    survivors = set(states) - excluded
    actions = public['next_actions']
    checks = {
        'no_actions_for_excluded_candidates': all(a['candidate_id'] not in excluded for a in actions),
        'all_excluded_ends_candidate_actions': bool(survivors) or not actions,
    }
    open_hard = {(c['candidate_id'],c['requirement_id']) for c in public['claims']
                 if c['candidate_id'] in survivors and c['status'] in ('unknown','conflict')
                 and reqs[c['requirement_id']]['importance']=='hard'}
    if open_hard:
        checks['open_hard_condition_is_first'] = bool(actions) and (
            actions[0]['candidate_id'],actions[0]['requirement_id']) in open_hard
    return checks

def main():
    results = {}
    for case in ('C01','C08','C12','C08_SHORT'):
        bundle=json.loads((OLD/case/'request.json').read_text(encoding='utf8'))
        response=json.loads((OLD/case/'response.json').read_text(encoding='utf8'))
        for origin in ('rule','manual','model'):
            pub=publish_checked_comparison(bundle,response if origin=='model' else None,origin=origin)
            checks=inspect_public(pub,bundle)
            if case=='C12':
                checks['withdrawn_hp_color_is_first'] = bool(pub['next_actions']) and (
                    pub['next_actions'][0]['candidate_id']=='HP M232dw' and
                    next(r for r in bundle['requirements'] if r['id']==pub['next_actions'][0]['requirement_id'])['dimension']=='color_print')
            results[case+':'+origin]={'checks':checks,'public':pub}
        if case=='C08':
            invalid=deepcopy(bundle)
            for source in invalid['sources']:
                source.pop('observed_at',None)
            pub=publish_checked_comparison(invalid)
            results['missing_source_time']={'checks':{
                'no_unqualified_elimination':all(a['research_status']=='pending_evidence' for a in pub['assessments'])},'public':pub}

    state=new_dialogue()
    for f,a in (('category','打印机'),('usage','低频家庭打印'),('needs_color','否'),
        ('accepts_outsourced_color','是'),('monthly_pages_range','0-50'),('budget_max_cny','1000'),
        ('device_deployment_region','中国大陆河南省'),('wechat_required','必须'),
        ('wechat_workflow','小程序'),('accepts_initial_setup','接受'),
        ('requires_scan','否'),('requires_auto_duplex','否')):
        state=submit_message(state,f,a)
    view=render_chat(deepcopy(state))
    report=json.loads(view['report_json'])
    cognition=report.get('cognition_comparison')
    normal_checks={'normal_entry_has_comparison':isinstance(cognition,dict)}
    if cognition:
        public=cognition['public']
        reqs={r['id']:r for r in cog.requirements(confirmed_values(state))}
        action=cognition['decision']['next_action']
        normal_checks['normal_audit_first_matches_decision']=bool(public['next_actions']) and (
            reqs[public['next_actions'][0]['requirement_id']]['dimension']==action['dimension'] and
            public['next_actions'][0]['candidate_id'] in action['candidates'])
    results['normal_original']={'checks':normal_checks,'prompt':view['prompt'],'text':view['result_text']}

    state=submit_message(state,'needs_color','是')
    state=submit_message(state,'requires_scan','是')
    bundle=json.loads((OLD/'C08/request.json').read_text(encoding='utf8'))
    bundle.update(dialogue_version=state['version'],confirmed_values_sha256=digest(confirmed_values(state)),
                  as_of=date.today().isoformat())
    with patch('shopping_decision.chat_bridge._analysis',return_value={
            'recommendation':{'status':'research'},'verified_research_bundle':bundle}):
        view=render_chat(state)
    report=json.loads(view['report_json'])
    pub=report.get('public_decision')
    checks={'backend_publishes_bound_comparison':isinstance(pub,dict)}
    if pub:
        checks.update(inspect_public(pub,bundle))
    checks['transaction_flags_remain_false']=all(report[k] is False for k in (
        'purchase_recommendation_approved','transactions_enabled','live_price_verified'))
    results['backend_both_excluded']={'checks':checks,'prompt':view['prompt'],'text':view['result_text'],'public':pub}
    failed=[name+':'+check for name,row in results.items() for check,ok in row['checks'].items() if not ok]
    print(json.dumps({'purpose':'冻结业务探针；通过仍须EVALUATION人审，不是真实交易/模型实效',
        'failed_checks':failed,'results':results},ensure_ascii=False,indent=2))
    return int(bool(failed))

if __name__=='__main__':
    raise SystemExit(main())
