"""S1-S4独立新变体；旧探针写入全部转至临时目录，新结果必须写到不存在的路径。"""
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from io import StringIO
from itertools import permutations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import argparse
import hashlib
import json
import os
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shopping_decision import sale_configuration_evidence as gate
from shopping_decision import dialogue_flow as dialogue

PROTECTED = [
    'reports/p0_9_b_independent_20261112.json',
    'reports/p0_9_b_independent_validation_20261112.json',
    'reports/p0_9_b_developer_replay_independent_20261112.json',
    'reports/p0_9_b_22_development_scenarios_20261112.json',
    'reports/p0_9_b_independent_20261112.py',
    'shopping_decision/sale_configuration_evidence.py',
    'shopping_decision/dialogue_flow.py',
    'shopping_decision/discovery_pool.py',
    'shopping_decision/p0_7_official_details.py',
    'tests/test_p0_9_b_s1s4_followup.py',
]
MODELS = {'HL-10W', 'HL-B2158W', 'HL-B2188DW'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists():
        parser.error('output exists; refusing to overwrite any previous result')
    if target.suffix != '.json' or target.parent != (ROOT / 'reports').resolve():
        parser.error('output must be a new JSON under this repository reports directory')
    protected = PROTECTED + [str(p.relative_to(ROOT)).replace('\\', '/')
                             for p in (ROOT / 'reports').glob('P0_9_B_*.md')]
    before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in protected}
    now = datetime.now(timezone.utc)
    base = {
        'source_id': 'synthetic:new_review_A', 'source_ref': 'synthetic:new_review_panel_A',
        'platform': 'TAOBAO', 'platform_item_id': '75432001', 'selected_sku_id': '75432009',
        'seller_id': 'new_review_seller', 'selected_variant': 'single_new_printer',
        'selected_model_id': 'HL-B2158W', 'title_models': ['HL-B2158W'], 'spec_models': ['HL-B2158W'],
        'item_kind': 'printer', 'condition': 'new',
        'source_sha256': hashlib.sha256(b'new review wholly synthetic panel').hexdigest(),
        'observed_at': (now - timedelta(hours=4)).isoformat(),
        'review_valid_until': (now + timedelta(days=3)).isoformat(), 'review_status': 'active',
        'field_anchors': {k: 'synthetic:new_anchor_' + k for k in (
            'platform_item_id', 'seller_id', 'selected_variant', 'selected_model_id',
            'item_kind', 'condition', 'selected_sku_id')},
        'permitted_uses': ['local_parse', 'user_display', 'minimal_audit'],
    }

    def altered(**edits):
        row = deepcopy(base)
        row.update(edits)
        return row

    def envelope(rows):
        return {'operation': 'p0_9_b_sale_configuration_evidence',
                'source_mode': 'synthetic_test', 'items': rows}

    def assess(rows, at=now):
        try:
            return gate.assess_sale_evidence_report(envelope(rows), now=at, known_models=MODELS)
        except Exception as exc:
            return {'exception': type(exc).__name__, 'reason': str(exc)}

    def active(out):
        return [x for x in out.get('configurations', [])
                if x['status'] == 'synthetic_field_binding_test_only']

    def safe(out):
        return (out.get('real_identity_verified_count') == 0
                and out.get('verified_quote_count') == 0
                and out.get('purchase_recommendation_approved') is False
                and out.get('transactions_enabled') is False)

    cases = []

    def record(ident, passed, expected, actual, *, kind='acceptance'):
        cases.append({'id': ident, 'expectation_met': bool(passed), 'kind': kind,
                      'expected': expected, 'actual': actual})

    # 防止旧探针在主输出以外悄悄重写22例复跑等旁文件。
    with TemporaryDirectory() as folder:
        mapped = {}
        original_write = Path.write_text
        original_read = Path.read_text

        def isolated_write(path, data, *a, **kw):
            if not path.resolve().is_relative_to(ROOT):
                return original_write(path, data, *a, **kw)
            key = str(path.resolve())
            out = Path(folder) / (hashlib.sha256(key.encode()).hexdigest() + '.json')
            mapped[key] = out
            return original_write(out, data, *a, **kw)

        def isolated_read(path, *a, **kw):
            redirected = mapped.get(str(path.resolve()))
            return original_read(redirected if redirected else path, *a, **kw)

        code = 0
        with patch.object(Path, 'write_text', isolated_write), \
             patch.object(Path, 'read_text', isolated_read), redirect_stdout(StringIO()):
            try:
                runpy.run_path(str(ROOT / 'reports/p0_9_b_independent_20261112.py'), run_name='__main__')
            except SystemExit as exc:
                code = int(exc.code or 0)
        old_result = json.loads(mapped[str((ROOT / PROTECTED[0]).resolve())].read_text(encoding='utf-8'))
    old_replay = {'exit_code': code, 'passed': old_result['new_cases_passed'],
                  'total': old_result['new_case_total'], 'cases': old_result['cases'],
                  'developer_22': old_result['developer_22_replay'],
                  'all_legacy_script_writes_were_temporary': True}

    result = assess([base])
    record('fully_anchored_taobao_positive', len(active(result)) == 1 and safe(result)
           and active(result)[0].get('field_binding_complete') is True,
           'complete SKU anchor remains auditable with all real permissions false', result)
    for label, edits in [
        ('anchors_nested_value', {'field_anchors': {**base['field_anchors'], 'seller_id': {}}}),
        ('digest_object', {'source_sha256': {'sha': 'a' * 64}}),
        ('expiry_list', {'review_valid_until': []}),
        ('source_id_list', {'source_id': ['synthetic:invalid']}),
        ('uses_boolean', {'permitted_uses': True}),
    ]:
        result = assess([altered(**edits), base])
        record('new_mixed_type_' + label, len(active(result)) == 1 and safe(result)
               and result.get('rejected_count') == 1,
               'reject malformed row and retain good row without exception', result)

    withdrawn = altered(review_status='withdrawn')
    another = altered(source_id='synthetic:independent_B', source_ref='synthetic:independent_panel_B')
    outputs = [assess(list(order)) for order in permutations([base, withdrawn, another])]
    record('six_orders_revocation_keeps_independent_source', all(
        safe(out) and {x['source_id'] for x in active(out)} == {'synthetic:independent_B'} for out in outputs),
        'all six orders invalidate source A only and keep independent B', outputs)

    zone = timezone(timedelta(hours=-11, minutes=-30))
    offset_withdrawn = altered(review_status='withdrawn',
        observed_at=datetime.fromisoformat(base['observed_at']).astimezone(zone).isoformat())
    result = assess([base, offset_withdrawn])
    record('negative_half_hour_zone_revocation', safe(result) and not active(result),
           'same source event normalized to UTC is invalidated', result)

    for label, row in [
        ('forbidden_approval_on_withdrawal', altered(review_status='withdrawn', identity_verified=True)),
        ('forbidden_price_on_use_loss', altered(permitted_uses=[], price=499)),
        ('malformed_uses_on_withdrawal', altered(review_status='withdrawn',
             permitted_uses=['local_parse', {'user_display': False}, 'minimal_audit'])),
    ]:
        result = assess([base, row])
        record('malformed_rejected_row_must_not_invalidate_' + label,
               safe(result) and len(active(result)) == 1 and result.get('rejected_count') == 1,
               'malformed/forbidden row is rejected without revoking the valid source', result)

    # 不要求不同来源事件互相撤回，明确验证没有“同数字一律连坐”。
    result = assess([base, altered(review_status='withdrawn', platform='JD')])
    record('withdrawal_other_platform_cannot_revoke', safe(result) and len(active(result)) == 1,
           'different platform is a different event', result)

    anchors = deepcopy(base['field_anchors'])
    anchors.pop('selected_sku_id')
    partial = altered(source_id='synthetic:legacy_partial', field_anchors=anchors)
    result = assess([partial])
    record('legacy_missing_sku_anchor_is_explicitly_incomplete', safe(result) and len(active(result)) == 1
           and active(result)[0].get('field_binding_complete') is False
           and active(result)[0].get('sku_anchor_status') == 'missing_selected_sku_anchor_unverified',
           'legacy fixture may remain synthetic but cannot claim complete binding', result)
    result = assess([altered(field_anchors={**base['field_anchors'], 'selected_sku_id': []}), base])
    record('bad_sku_anchor_does_not_drop_good', safe(result) and len(active(result)) == 1
           and result.get('rejected_count') == 1,
           'bad SKU anchor rejected per row', result)
    pair = [assess([partial, base]), assess([base, partial])]
    record('merge_complete_and_partial_anchor_order', all(
        any(x.get('field_binding_complete') is True for x in active(out)) for out in pair),
        'merging a partial fixture must not discard the other complete source solely due to row order',
        pair, kind='audit_robustness')

    # 两轮CLI并带跨时区到期：受控推进门禁时钟，不改真实日期/取证记录。
    t1, t2 = now + timedelta(seconds=30), now + timedelta(seconds=90)
    short = altered(review_valid_until=(now + timedelta(seconds=60)).astimezone(
        timezone(timedelta(hours=9, minutes=30))).isoformat())

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.current.astimezone(tz) if tz else cls.current.replace(tzinfo=None)

    Clock.current = t1

    class Turns(StringIO):
        count = 0

        def __next__(self):
            line = self.readline()
            if not line:
                raise StopIteration
            self.count += 1
            if self.count == 2:
                Clock.current = t2
            return line

    answers = {'category': 'printer', 'needs_color': False, 'requires_wireless': True,
               'accepts_outsourced_color': True, 'monthly_pages_range': [0, 50], 'usage': 'home'}
    turns = [{'text': 'synthetic fresh before expiry', 'answers': answers},
             {'text': 'synthetic after expiry', 'answers': {'requires_auto_duplex': True}}]
    with TemporaryDirectory() as folder:
        path = Path(folder) / 'only_synthetic.json'
        path.write_text(json.dumps(envelope([short])), encoding='utf-8')
        out = StringIO()
        with patch.object(gate, 'datetime', Clock), \
             patch.object(sys, 'argv', ['dialogue_flow', '--sale-evidence-report', str(path)]), \
             patch.object(sys, 'stdin', Turns(''.join(json.dumps(t) + '\n' for t in turns))), \
             redirect_stdout(out):
            dialogue.main()
        rows = [json.loads(line) for line in out.getvalue().splitlines()]
    sale1, sale2 = [r['sale_configuration_evidence'] for r in rows[1:]]
    record('new_cli_half_hour_zone_expiry_between_turns', safe(sale1) and safe(sale2)
           and len(active(sale1)) == 1 and not active(sale2) and sale2.get('rejected_count') == 1,
           'one usable binding before expiry, none afterwards; source time not refreshed',
           {'first_turn': sale1, 'second_turn': sale2, 'simulated_clock_only': True})

    def cli_report(rows):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'mixed.json'
            path.write_text(json.dumps(envelope(rows)), encoding='utf-8')
            env = {k: v for k, v in os.environ.items() if k not in ('PYTHONUTF8', 'PYTHONIOENCODING')}
            proc = subprocess.run([sys.executable, '-m', 'shopping_decision.dialogue_flow',
                                   '--sale-evidence-report', str(path)], cwd=ROOT, env=env,
                                  input=(json.dumps({'text': 'synthetic cli review', 'answers': answers}) + '\n').encode(),
                                  capture_output=True, timeout=30)
        return proc.returncode, [json.loads(x) for x in proc.stdout.decode('utf-8').splitlines()][1]

    code, out = cli_report([base, withdrawn, another])
    sale = out['sale_configuration_evidence']
    record('new_subprocess_invalidated_source_not_compared_independent_kept',
           code == 0 and safe(sale) and len(active(sale)) == 1
           and all(not x['required_met'] and x['manufacturer_model_fact_status'] == 'manufacturer_facts_not_compared'
                   for x in sale['configurations'] if x['source_id'] == base['source_id']),
           'withdrawn source not associated with met specs; independent source survives', sale)
    code, out = cli_report([base, altered(review_status='withdrawn', identity_verified=True)])
    sale = out['sale_configuration_evidence']
    record('new_subprocess_forbidden_withdrawal_not_applied', code == 0 and safe(sale) and len(active(sale)) == 1,
           'forbidden rejected row must not suppress the valid source in normal CLI', sale)

    after = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in protected}
    assert before == after, 'protected business or historical report changed during review'
    result = {'role': 'independent_reviewer', 'observed_at': now.isoformat(),
              'new_total': len(cases), 'new_passed': sum(c['expectation_met'] for c in cases),
              'failed_ids': [c['id'] for c in cases if not c['expectation_met']], 'new_cases': cases,
              'old_24_replay': old_replay, 'protected_sha256': after,
              'all_protected_files_unchanged': True,
              'boundaries': {'new_haina_calls': 0, 'credential_reads': 0, 'paid_calls': 0,
                             'account_actions': 0, 'transactions': 0, 'business_code_modified': False,
                             'git_commit': False, 'git_push': False},
              'limits': ['synthetic only, no real identity positives', 'selected checks are not an accuracy estimate',
                         'original old 14/24 per-case bytes were already lost before this review']}
    with target.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('new_total', 'new_passed', 'failed_ids',
                                           'all_protected_files_unchanged')}, indent=2))
    print(json.dumps({'old_replay_passed': old_replay['passed'], 'old_replay_total': old_replay['total']}, indent=2))
    return int(any(not c['expectation_met'] and c['kind'] == 'acceptance' for c in cases))


if __name__ == '__main__':
    raise SystemExit(main())
