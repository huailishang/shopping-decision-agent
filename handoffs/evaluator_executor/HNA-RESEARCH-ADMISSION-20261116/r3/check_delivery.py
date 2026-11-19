"""Evaluator-owned offline acceptance checks. Never build product decisions here."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[3]
MODELS = {'HL-L1238W', 'M232dw'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_of(result):
    require(isinstance(result, dict), 'result must be an object')
    research = result.get('real_printer_case_research', {})
    snapshot = research.get('shared_research_snapshot')
    require(isinstance(snapshot, dict), 'normal result lacks shared research snapshot')
    return snapshot


def validate_snapshot(snapshot, case):
    for key in ('purchase_recommendation_approved', 'transactions_enabled'):
        require(snapshot.get(key) is False, 'unsafe shared flag: ' + key)
    require(snapshot.get('verified_platform_identity_count') == 0, 'invented platform identity')
    require(snapshot.get('verified_live_quote_count') == 0, 'invented live quote')
    plan = snapshot.get('decision_plan')
    require(isinstance(plan, dict), 'decision_plan missing: existing output is insufficient')
    require(plan.get('schema_version') == 1, 'unexpected decision plan schema')
    require(plan.get('current_path') == case['expected_current_path'], 'wrong current research action')
    require(plan.get('scope') == 'conditional_model_research', 'research scope lost')
    require(plan.get('reuse_verified') is False, 'first setup cannot prove subsequent reuse')
    require(plan.get('purchase_recommendation_approved') is False, 'plan approves buying')
    require(plan.get('transactions_enabled') is False, 'plan enables transaction')
    question = plan.get('primary_question')
    expected_field = case['expected_primary_question_field']
    if expected_field is None:
        require(question is None, 'answered WeChat requirement must not be asked again')
    else:
        require(isinstance(question, dict) and question.get('field') == expected_field,
                'central research question was displaced by purchase bookkeeping')
        require(question.get('status') == 'unconfirmed', 'proxy unknown became confirmation')
    branches = plan.get('branches')
    require(isinstance(branches, list) and len(branches) == 2, 'two conditional paths required')
    branch_map = {}
    for branch in branches:
        condition = branch.get('when', {}).get('wechat_required')
        require(type(condition) is bool and condition not in branch_map, 'ambiguous branch condition')
        branch_map[condition] = branch
        require(branch.get('basis') == 'hypothetical_not_user_confirmation', 'branch became user answer')
        require(set(branch.get('candidate_model_ids', [])) == MODELS, 'unproven candidate elimination')
        ids = branch.get('source_ids')
        require(isinstance(ids, list) and {'R7', 'R10'} <= set(ids), 'setup evidence is not bound')
        registry = snapshot.get('source_registry', {})
        require(all(source in registry for source in ids), 'unmapped source ID')
        for source in ids:
            ref = registry[source]
            require(ref.get('url') and ref.get('checked_on') and ref.get('limit'), 'source scope/date missing')
        for key in ('explanation', 'limitations'):
            require(isinstance(branch.get(key), str) and branch[key].strip(), 'branch explanation/limit missing')
        action = branch.get('next_step')
        require(isinstance(action, dict), 'branch next step missing')
        for key in ('action', 'owner_role', 'exact_item'):
            require(isinstance(action.get(key), str) and action[key].strip(), 'vague next step: ' + key)
    require(branch_map[True].get('state') == 'pending_reuse_evidence', 'mandatory path asserts reuse')
    require(branch_map[False].get('state') == 'research_can_continue', 'optional WeChat stops all research')
    require(branch_map[True]['next_step'].get('blocks') == 'wechat_reuse_claim', 'wrong mandatory-path gate')
    require(branch_map[False]['next_step'].get('blocks') == 'specific_unverified_claim_only',
            'missing supplier evidence was generalized to a whole-project stop')
    checks = plan.get('purchase_checks')
    require(isinstance(checks, list), 'purchase checks absent')
    fields = {item.get('field') for item in checks}
    require({'budget_scope', 'delivery_region', 'sale_identity', 'live_price'} <= fields,
            'purchase prerequisites were silently dropped')
    require(all(item.get('stage') == 'purchase' and item.get('verified') is False for item in checks),
            'purchase checks used as verified facts or global research gates')
    require(isinstance(plan.get('text'), str) and len(plan['text'].strip()) >= 60,
            'no readable conditional comparison')
    return {'case': case['id'], 'current_path': plan['current_path'], 'source_ids': ['R7', 'R10'],
            'reuse_verified': False, 'claims': 'research_only_no_new_external_facts'}


def run_behavior(out):
    cases = read(TASK / 'cases.json')['cases']
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT))
    from shopping_decision.chat_bridge import render_chat, submit_message
    from shopping_decision.dialogue_flow import new_dialogue
    results = []
    errors = []
    for case in cases:
        name = case['id']
        payload = case['input']
        wire = (json.dumps(payload, ensure_ascii=False) + '\n').encode('utf-8')
        command = [sys.executable, '-X', 'utf8', '-m', 'shopping_decision.dialogue_flow', '--real-printer-case']
        completed = subprocess.run(command, input=wire, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   cwd=ROOT, timeout=45)
        (out / (name + '.input.jsonl')).write_bytes(wire)
        (out / (name + '.stdout.jsonl')).write_bytes(completed.stdout)
        (out / (name + '.stderr.log')).write_bytes(completed.stderr)
        try:
            require(completed.returncode == 0, 'normal CLI failed')
            last = [json.loads(line) for line in completed.stdout.decode('utf-8').splitlines() if line.strip()][-1]
            cli_snapshot = snapshot_of(last)
            checked = validate_snapshot(cli_snapshot, case)
            answers = payload['answers']
            state = new_dialogue()
            messages = [('category', '打印机'), ('usage', answers['usage']), ('needs_color', '否'),
                        ('accepts_outsourced_color', '是'), ('accepts_initial_setup', '接受'),
                        ('device_deployment_region', answers['device_deployment_region']),
                        ('monthly_pages_range', '0-50'), ('budget_max_cny', str(answers['budget_max_cny']))]
            if 'wechat_required' in answers:
                messages.append(('wechat_required', '必须' if answers['wechat_required'] else '不需要'))
            if answers.get('wechat_workflow') == 'miniprogram':
                messages.append(('wechat_workflow', '微信小程序直接打印'))
            for field, message in messages:
                state = submit_message(state, field, message)
            chat = render_chat(state)
            (out / (name + '.chat.json')).write_text(json.dumps({
                'basis': 'proxy_or_hypothetical_replay_not_direct_user_feedback', 'result': chat},
                ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            chat_snapshot = snapshot_of(json.loads(chat['report_json'])['research_result'])
            validate_snapshot(chat_snapshot, case)
            require(cli_snapshot['decision_plan'] == chat_snapshot['decision_plan'], 'CLI/chat decision mismatch')
            require(cli_snapshot['decision_plan']['text'] in chat['result_text'],
                    'new reasoning hidden in audit but absent from visible chat result')
            checked['chat_visible_and_same'] = True
            results.append(checked)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            errors.append({'case': name, 'error': str(exc)})
    result = {'cases_checked': len(cases), 'passed': len(results), 'results': results, 'errors': errors,
              'limit': 'Normal local entry behavior, not new material acquisition or real-user effectiveness.'}
    (out / 'behavior_summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    require(not errors, json.dumps(result, ensure_ascii=False))
    return result


def verify_frozen(expected_sha):
    require(digest(TASK / 'FROZEN_INPUTS.json') == expected_sha, 'frozen manifest changed')
    frozen = read(TASK / 'FROZEN_INPUTS.json')
    for name, expected in frozen['files'].items():
        path = ROOT / name
        require(path.is_file() and digest(path) == expected, 'frozen input changed: ' + name)
    for name, expected in frozen['protected_product_files'].items():
        path = ROOT / name
        require(path.is_file() and digest(path) == expected, 'outside product scope changed: ' + name)
    for name in frozen['product_inventory']:
        require((ROOT / name).is_file(), 'existing product file removed: ' + name)
    current_inventory = {p.relative_to(ROOT).as_posix()
                         for folder, pattern in (('shopping_decision', '*.py'), ('tests', '*.py'),
                                                 ('desktop', '*.java'), ('knowledge', '*.json'))
                         for p in (ROOT / folder).rglob(pattern)}
    additions = current_inventory - set(frozen['product_inventory'])
    require(additions <= set(frozen['allowed_product_paths']), 'out-of-scope new product files: ' + str(sorted(additions)))
    return {'status': 'frozen_inputs_match', 'protected_product_files': len(frozen['protected_product_files'])}


def submission_check():
    evidence = TASK / 'evidence'
    comparison = read(evidence / 'impact_comparison.json')
    require(comparison.get('baseline_sha256') == digest(TASK / 'preparation/baseline.stdout.jsonl'),
            'baseline replaced')
    require(comparison.get('new_external_material_count') == 0, 'this offline package cannot claim new acquisition')
    require(comparison.get('real_user_feedback_collected') is False, 'proxy replay became human trial')
    require(comparison.get('formal_36_started') is False, 'formal evaluation was not authorized')
    require(comparison.get('purchase_recommendation_approved') is False, 'buy approval changed')
    require(comparison.get('transactions_enabled') is False, 'transaction changed')
    for key in ('before_observation', 'after_observation', 'actual_change', 'unchanged_external_gaps',
                'effect_claim_limit', 'actual_cost', 'negative_evidence_paths'):
        require(bool(comparison.get(key)), 'comparison omitted: ' + key)
    for filename in ('CASE_COMPARISON.md', 'evidence/claim_source_map.json'):
        path = TASK / filename
        require(path.is_file() and path.stat().st_size > 0, 'deliverable missing: ' + filename)
    return {'status': 'submission_present_needs_independent_semantic_review'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', choices=('frozen', 'behavior', 'submission'), required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--frozen-sha', required=True)
    args = parser.parse_args()
    try:
        result = verify_frozen(args.frozen_sha)
        if args.check == 'behavior':
            require(args.out is not None, 'behavior requires separate evidence output directory')
            result = run_behavior(args.out)
        elif args.check == 'submission':
            result = submission_check()
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'status': 'check_failed', 'reason': str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
