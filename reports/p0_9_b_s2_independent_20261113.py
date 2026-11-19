"""S2资格门禁独立新变体；仅合成离线；输出排他创建、不改旧结果/业务文件。"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shopping_decision.sale_configuration_evidence import assess_sale_evidence_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists() or target.parent != (ROOT / 'reports').resolve() or target.suffix != '.json':
        parser.error('use a new JSON output path inside reports; existing files cannot be overwritten')
    protected = [ROOT / p for p in (
        'shopping_decision/sale_configuration_evidence.py', 'shopping_decision/dialogue_flow.py',
        'shopping_decision/discovery_pool.py', 'tests/test_p0_9_b_s1s4_followup.py',
        'reports/p0_9_b_s1s4_new_review_20261112.json',
        'reports/p0_9_b_s1s4_independent_validation_20261112.json',
        'reports/p0_9_b_independent_20261112.json',
        'reports/p0_9_b_independent_validation_20261112.json')]
    protected += list((ROOT / 'reports').glob('P0_9_B_*.md'))
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    now = datetime.now(timezone.utc)
    uses = ['local_parse', 'user_display', 'minimal_audit']
    models = {'HL-10W', 'HL-B2158W', 'HL-B2188DW'}
    base = {
        'source_id': 'synthetic:s2_new_source', 'source_ref': 'synthetic:s2_new_panel',
        'platform': 'JD', 'platform_item_id': '63547001', 'selected_sku_id': '63547002',
        'seller_id': 's2_new_seller', 'selected_variant': 'single_new_printer',
        'selected_model_id': 'HL-10W', 'title_models': ['HL-10W'], 'spec_models': ['HL-10W'],
        'item_kind': 'printer', 'condition': 'new',
        'source_sha256': hashlib.sha256(b'S2 fresh synthetic fixture November 13').hexdigest(),
        'observed_at': (now - timedelta(hours=3)).isoformat(),
        'review_valid_until': (now + timedelta(days=4)).isoformat(),
        'review_status': 'active', 'permitted_uses': uses,
        'field_anchors': {k: 'synthetic:s2_' + k for k in (
            'platform_item_id', 'seller_id', 'selected_variant', 'selected_model_id',
            'item_kind', 'condition', 'selected_sku_id')},
    }

    def altered(**edits):
        row = deepcopy(base)
        row.update(edits)
        return row

    def report(rows):
        return {'operation': 'p0_9_b_sale_configuration_evidence', 'source_mode': 'synthetic_test', 'items': rows}

    def assess(rows):
        try:
            return assess_sale_evidence_report(report(rows), now=now, known_models=models)
        except Exception as exc:
            return {'exception': type(exc).__name__, 'reason': str(exc)}

    def active(out):
        return [x for x in out.get('configurations', []) if x['status'] == 'synthetic_field_binding_test_only']

    def safe(out):
        return (out.get('real_identity_verified_count') == 0 and out.get('verified_quote_count') == 0
                and out.get('purchase_recommendation_approved') is False
                and out.get('transactions_enabled') is False)

    cases = []

    def record(ident, expected, actual, passed):
        cases.append({'id': ident, 'expected': expected, 'actual': actual, 'expectation_met': bool(passed)})

    out = assess([base])
    record('new_complete_positive_control', 'complete synthetic binding retained without real approval', out,
           safe(out) and len(active(out)) == 1 and active(out)[0]['field_binding_complete'])

    # 新的合法用途减少组合；测试双向行序，不以关闭所有事件躲过负向输入。
    for subset in [('minimal_audit',), ('user_display',), ('local_parse', 'user_display'),
                   ('minimal_audit', 'local_parse'), ('minimal_audit', 'user_display')]:
        event = altered(permitted_uses=list(subset))
        outputs = [assess([base, event]), assess([event, base])]
        record('legitimate_use_reduction_' + '_'.join(subset), 'valid use loss invalidates source in either order',
               outputs, all(safe(o) and not active(o) for o in outputs))

    offset = timezone(timedelta(hours=12, minutes=45))
    event = altered(review_status='withdrawn', permitted_uses=list(reversed(uses)),
                    observed_at=datetime.fromisoformat(base['observed_at']).astimezone(offset).isoformat(),
                    review_valid_until=datetime.fromisoformat(base['review_valid_until']).astimezone(offset).isoformat())
    out = assess([event, base])
    record('legal_withdrawal_permuted_uses_and_utc_equivalence', 'valid normalized same event withdraws', out,
           safe(out) and not active(out))

    bad_variants = [
        ('status_object', {'review_status': {'withdrawn': True}}),
        ('status_boolean', {'review_status': False}),
        ('source_anchor_url', {'review_status': 'withdrawn',
            'field_anchors': {**base['field_anchors'], 'platform_item_id': 'https://example.invalid/fake'}}),
        ('uppercase_digest', {'review_status': 'withdrawn', 'source_sha256': 'A' * 64}),
        ('wrong_bundle', {'review_status': 'withdrawn', 'selected_variant': 'multiple_printers'}),
        ('unicode_sku_digits', {'review_status': 'withdrawn', 'selected_sku_id': '\u0661\u0662\u0663\u0664\u0665'}),
        ('mismatched_title', {'review_status': 'withdrawn', 'title_models': ['HL-B2188DW']}),
        ('unknown_anchor', {'review_status': 'withdrawn',
            'field_anchors': {**base['field_anchors'], 'purchase_permission': 'synthetic:forged'}}),
        ('expired_event', {'review_status': 'withdrawn',
            'review_valid_until': (now - timedelta(microseconds=7)).isoformat()}),
    ]
    for label, edits in bad_variants:
        event = altered(**edits)
        outputs = [assess([base, event]), assess([event, base])]
        record('invalid_event_' + label, 'bad event rejected without affecting valid source in either order', outputs,
               all(safe(o) and len(active(o)) == 1 and o.get('rejected_count') == 1 for o in outputs))

    # ISO文本能解析但转UTC超出datetime范围；不应使一条坏事件拖垮整份报告。
    extreme = '9999-12-31T23:59:59-00:01'
    for label, edits in [
        ('withdrawn', {'review_status': 'withdrawn', 'review_valid_until': extreme}),
        ('permission_loss', {'permitted_uses': ['user_display'], 'review_valid_until': extreme}),
    ]:
        event = altered(**edits)
        outputs = [assess([base, event]), assess([event, base])]
        record('utc_out_of_range_' + label, 'invalid normalized event rejected while good row remains', outputs,
               all(safe(o) and len(active(o)) == 1 and o.get('rejected_count') == 1 for o in outputs))

    another = altered(source_id='synthetic:s2_other', source_ref='synthetic:s2_other_panel')
    event = altered(permitted_uses=['minimal_audit', 'user_display'])
    out = assess([another, event, base])
    record('new_valid_use_loss_independent_source_survives', 'only event source invalidated', out,
           safe(out) and {x['source_id'] for x in active(out)} == {'synthetic:s2_other'})

    answers = {'category': 'printer', 'needs_color': False, 'requires_wireless': True,
               'usage': 'home', 'monthly_pages_range': [0, 50]}

    def cli(rows):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'only_synthetic.json'
            path.write_text(json.dumps(report(rows)), encoding='utf-8')
            env = {k: v for k, v in os.environ.items() if k not in ('PYTHONUTF8', 'PYTHONIOENCODING')}
            proc = subprocess.run([sys.executable, '-m', 'shopping_decision.dialogue_flow',
                                   '--sale-evidence-report', str(path)], cwd=ROOT, env=env,
                                  input=(json.dumps({'text': 'S2 fresh synthetic assessment', 'answers': answers}) + '\n').encode(),
                                  capture_output=True, timeout=30)
        parsed = [json.loads(x) for x in proc.stdout.decode('utf-8').splitlines()]
        return {'returncode': proc.returncode, 'rows': parsed,
                'stderr': proc.stderr.decode('utf-8', errors='replace')}

    result = cli([base, altered(review_status='withdrawn', review_valid_until=extreme)])
    sale = result['rows'][1].get('sale_configuration_evidence', {}) if len(result['rows']) > 1 else {}
    record('cli_utc_out_of_range_rejected_without_crash', 'CLI retains valid configuration and rejects bad expiry', result,
           result['returncode'] == 0 and safe(sale) and len(active(sale)) == 1 and sale.get('rejected_count') == 1)

    result = cli([base, another, event])
    sale = result['rows'][1].get('sale_configuration_evidence', {}) if len(result['rows']) > 1 else {}
    record('cli_new_legitimate_reduction_with_independent_source', 'valid state loss applied only to correct source', result,
           result['returncode'] == 0 and safe(sale)
           and {x['source_id'] for x in active(sale)} == {'synthetic:s2_other'})

    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    assert before == after, 'protected business or historical evidence changed'
    payload = {'role': 'independent_reviewer', 'date': '2026-11-13', 'observed_at': now.isoformat(),
               'new_total': len(cases), 'new_passed': sum(c['expectation_met'] for c in cases),
               'failed_ids': [c['id'] for c in cases if not c['expectation_met']], 'cases': cases,
               'protected_files_unchanged': True,
               'protected_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): h for p, h in after.items()},
               'boundaries': {'new_api_calls': 0, 'paid_calls': 0, 'credential_reads': 0,
                              'account_actions': 0, 'transactions': 0, 'external_messages': 0,
                              'business_code_modified': False, 'git_commit': False, 'git_push': False},
               'limitations': ['synthetic only; purpose-selected boundary checks are not overall accuracy',
                               'no new real product identity, license, price or account evidence']}
    with target.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: payload[k] for k in ('new_total', 'new_passed', 'failed_ids',
                                             'protected_files_unchanged')}, indent=2))
    return int(bool(payload['failed_ids']))


if __name__ == '__main__':
    raise SystemExit(main())
