"""Offline evaluator checks for a minimal, incomplete-evidence research flow."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
STAGES = {'requirements', 'evidence', 'comparison', 'explanation', 'feedback', 'evaluation'}
MODELS = {'HL-L1238W', 'M232dw'}


def need(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_ref(ref):
    need(isinstance(ref, dict), 'evidence binding missing')
    path = (ROOT / ref.get('path', '')).resolve()
    need(path.is_relative_to(TASK / 'evidence'), 'evidence path is outside current task evidence')
    need(path.is_file() and sha(path) == ref.get('sha256'), 'evidence missing or changed')
    return path


def check_case(result, case):
    need(isinstance(result, dict), 'normal result must be an object')
    view = result.get('research_case')
    need(isinstance(view, dict), 'normal entry has not produced a selected-evidence research_case')
    need(view.get('schema_version') == 1, 'unexpected research case version')
    need(view.get('case_id') == 'PRINTER-HENAN-FAMILY-20261116', 'proxy case identity changed')
    need(view.get('input_basis') == 'project_owner_proxy', 'proxy input became direct user confirmation')
    need(view.get('flow_status') == 'research_delivered_with_limits', 'flow completion overclaims evidence')
    for key in ('purchase_recommendation_approved', 'transactions_enabled', 'wechat_reuse_verified',
                'live_price_verified', 'long_term_reliability_verified', 'real_user_effect_verified'):
        need(view.get(key) is False, 'unverified claim enabled: ' + key)
    need(view.get('new_external_fact_count') == 0, 'local reuse claimed as new external evidence')
    pack_id = case['input']['research_context']['evidence_pack_id']
    pack = read(TASK / 'evidence_packs.json')['packs'][pack_id]
    need(view.get('evidence_pack_id') == pack_id, 'requested evidence pack was ignored')
    used = view.get('used_facts')
    need(isinstance(used, list), 'used fact list missing')
    need({row.get('id') for row in used} == set(case['expected_claim_ids']), 'selected facts not actually used')
    expected = {row['id']: row for row in pack['claims']}
    for fact in used:
        need(fact == expected[fact['id']], 'source statement/date/scope was changed or invented')
    need(view.get('source_registry') == pack['sources'], 'unselected sources silently used')
    candidates = view.get('candidate_assessments')
    need(isinstance(candidates, list) and {r.get('model_id') for r in candidates} == MODELS,
         'research anchors missing or invented')
    for row in candidates:
        available = {c['id'] for c in pack['claims'] if c['model_id'] == row['model_id']}
        need(set(row.get('supported_claim_ids', [])) == available, 'candidate uses missing/unselected claim')
        need(row.get('research_status') in {'keep_for_research', 'pending_evidence'},
             'sparse evidence caused unsupported winner or exclusion')
        need({'wechat_reuse', 'live_price', 'long_term_reliability'} <= set(row.get('unknown_fields', [])),
             'missing facts were silently filled')
        need(isinstance(row.get('reason'), str) and row['reason'].strip(), 'candidate has no reason')
    core = view.get('processed_stages')
    need(isinstance(core, list) and {'requirements', 'evidence', 'comparison', 'explanation'} <= set(core),
         'normal entry skipped a core research step')
    feedback = view.get('feedback')
    need(isinstance(feedback, dict) and feedback.get('status') == 'not_collected'
         and feedback.get('actual_response_count') == 0, 'missing feedback became human validation')
    need(isinstance(view.get('report_text'), str) and len(view['report_text'].strip()) >= 120,
         'no readable model comparison')
    need(isinstance(view.get('next_actions'), list) and view['next_actions'], 'no concrete next action')
    for action in view['next_actions']:
        need(all(isinstance(action.get(k), str) and action[k].strip()
                 for k in ('action', 'owner_role', 'exact_item')), 'vague next action')
    return view


def make_chat(case):
    sys.path.insert(0, str(ROOT))
    from shopping_decision.chat_bridge import render_chat, submit_message
    from shopping_decision.dialogue_flow import new_dialogue
    answers = case['input']['answers']
    state = new_dialogue()
    messages = [('category', '打印机'), ('usage', answers['usage']), ('needs_color', '否'),
                ('accepts_outsourced_color', '是'), ('accepts_initial_setup', '接受'),
                ('device_deployment_region', answers['device_deployment_region']),
                ('monthly_pages_range', '0-50'), ('budget_max_cny', str(answers['budget_max_cny']))]
    for field, text in messages:
        state = submit_message(state, field, text)
    # This is a declared proxy replay, not evidence that a real user clicked or answered.
    state['research_context'] = copy.deepcopy(case['input']['research_context'])
    return render_chat(state)


def run_cases(out):
    out.mkdir(parents=True, exist_ok=True)
    results, errors = [], []
    for case in read(TASK / 'cases.json')['cases']:
        ident = case['id']
        wire = (json.dumps(case['input'], ensure_ascii=False) + '\n').encode('utf-8')
        command = [sys.executable, '-X', 'utf8', '-m', 'shopping_decision.dialogue_flow', '--real-printer-case']
        completed = subprocess.run(command, cwd=ROOT, input=wire, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, timeout=60)
        (out / (ident + '.input.jsonl')).write_bytes(wire)
        (out / (ident + '.stdout.jsonl')).write_bytes(completed.stdout)
        (out / (ident + '.stderr.log')).write_bytes(completed.stderr)
        try:
            need(completed.returncode == 0, 'normal CLI process failed')
            last = [json.loads(s) for s in completed.stdout.decode('utf-8').splitlines() if s.strip()][-1]
            view = check_case(last, case)
            chat = make_chat(case)
            (out / (ident + '.chat.json')).write_text(json.dumps({
                'basis': 'proxy_replay_not_direct_user_feedback', 'result': chat},
                ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            chat_report = json.loads(chat['report_json'])
            chat_view = check_case(chat_report['research_result'], case)
            need(view == chat_view, 'CLI and chat do not use the same evidence/decision')
            need(view['report_text'] in chat['result_text'], 'comparison hidden outside visible chat result')
            results.append({'case': ident, 'role': case['role'], 'used_claim_count': len(view['used_facts']),
                            'flow_status': view['flow_status'], 'chat_visible_and_same': True})
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            errors.append({'case': ident, 'error': str(exc)})
    summary = {'cases_checked': 3, 'passed': len(results), 'results': results, 'errors': errors,
               'limit': 'One proxy walkthrough plus sparse/empty engineering variants, not three user trials.'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    need(not errors, json.dumps(summary, ensure_ascii=False))
    return summary


def frozen_check(expected_sha):
    path = TASK / 'FROZEN_INPUTS.json'
    need(sha(path) == expected_sha, 'frozen manifest changed')
    manifest = read(path)
    for name, expected in manifest['files'].items():
        p = ROOT / name
        need(p.is_file() and sha(p) == expected, 'frozen input changed: ' + name)
    for name, expected in manifest['protected_product_files'].items():
        p = ROOT / name
        need(p.is_file() and sha(p) == expected, 'outside-scope product changed: ' + name)
    for name in manifest['product_inventory']:
        need((ROOT / name).is_file(), 'existing product file removed: ' + name)
    inventory = {p.relative_to(ROOT).as_posix()
                 for folder, pattern in (('shopping_decision', '*.py'), ('tests', '*.py'),
                                         ('desktop', '*.java'), ('knowledge', '*.json'), ('scripts', '*.py'))
                 for p in (ROOT / folder).rglob(pattern)}
    need(inventory - set(manifest['product_inventory']) <= set(manifest['allowed_product_paths']),
         'new product files outside frozen scope')
    registry = ROOT / 'knowledge/printer_minimal_evidence_packs.json'
    if registry.exists():
        need(sha(registry) == sha(TASK / 'evidence_packs.json'), 'runtime pack registry differs from accepted summaries')
    return {'status': 'frozen_inputs_match', 'protected_count': len(manifest['protected_product_files'])}


def delivery_check():
    evidence = TASK / 'evidence'
    trace = read(evidence / 'flow_trace.json')
    stages = trace.get('stages')
    need(isinstance(stages, list) and {s.get('stage') for s in stages} == STAGES, 'six stages not processed')
    for stage in stages:
        need(stage.get('status') and stage.get('observation'), 'stage has only a checkmark')
        file_ref(stage.get('evidence'))
    by_stage = {s['stage']: s for s in stages}
    need(by_stage['feedback']['status'] == 'not_collected', 'fixture absence became real feedback')
    need(trace.get('real_user_feedback_collected') is False, 'proxy replay became user feedback')
    need(trace.get('new_external_fact_count') == 0, 'existing materials counted as new acquisition')
    assessment = read(evidence / 'assessment.json')
    need(assessment.get('real_user_effect_verified') is False, 'engineering check claimed human benefit')
    need(assessment.get('formal_36_started') is False, 'formal evaluation not in scope')
    need(assessment.get('effect_verdict') in {'inconclusive', 'no_observed_gain', 'limited_case_observation'},
         'unsupported effect verdict')
    need(type(assessment.get('judged_question_count')) is int and assessment['judged_question_count'] >= 0,
         'judged task count not recorded')
    if assessment['judged_question_count'] == 0:
        need(assessment.get('reason_no_judgment'), 'zero judgable questions needs honest reason')
    paired = assessment.get('paired_comparison')
    need(isinstance(paired, dict) and paired.get('status') in {'compared', 'not_comparable'},
         'comparison stage was skipped')
    if paired['status'] == 'compared':
        left, right = file_ref(paired.get('basic_output')), file_ref(paired.get('reasoned_output'))
        need(left != right, 'one output file relabelled as two groups')
        need(paired.get('same_input_and_evidence') is True and paired.get('limitations'), 'unfair comparison')
    else:
        need(paired.get('reason') and paired.get('attempt_evidence'), 'comparison absence has no actual diagnosis')
        file_ref(paired['attempt_evidence'])
    need(assessment.get('baseline_sha256') == sha(TASK / 'preparation/baseline.stdout.jsonl'), 'baseline replaced')
    for filename in ('RESEARCH_DELIVERY.md', 'evidence/first_walkthrough.json', 'evidence/breakpoints.json',
                     'evidence/claim_source_map.json', 'evidence/iterations.json'):
        p = TASK / filename
        need(p.is_file() and p.stat().st_size > 0, 'required delivery missing: ' + filename)
    need(isinstance(assessment.get('remaining_unknowns'), list) and assessment['remaining_unknowns'],
         'known external gaps disappeared')
    return {'status': 'flow_and_assessment_records_present_needs_independent_semantic_review',
            'real_user_feedback_collected': False, 'effect_verdict': assessment['effect_verdict']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', choices=('frozen', 'flow', 'delivery'), required=True)
    parser.add_argument('--frozen-sha', required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    try:
        result = frozen_check(args.frozen_sha)
        if args.check == 'flow':
            need(args.out is not None, 'flow requires separate evidence output')
            result = run_cases(args.out)
        elif args.check == 'delivery':
            result = delivery_check()
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'status': 'check_failed', 'reason': str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
