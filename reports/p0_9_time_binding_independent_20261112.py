"""独立时间绑定复验：仅离线、内存变体；不改原文/原清单或历史评估。"""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shopping_decision.p0_7_official_details import (
    parse_detail, enrich_discovered_catalog, load_reviewed_local_replay,
)
from shopping_decision.product_compare import compare_products, load_official_catalog
from shopping_decision.public_catalog import (
    BROTHER_SNAPSHOT, _read_bounded_json, catalog_from_brother_snapshot,
)

MANIFEST = ROOT / 'reports/p0_8_refetched_official_sources_20261109.json'
# 期待值来自历史取证事件，不从被测模块的冻结表生成。
EVENTS = {
    'HL-10W': ('2026-11-09T14:01:03.133068+00:00',
               '3d3a08760305db1f22c82cac514216f7d33646791775ab2490709871b2e04dff'),
    'HL-B2188DW': ('2026-11-09T14:01:03.875727+00:00',
                   'ee0c6963a4b2962d71911010aac53bf949736e8435d701be6fa5a393295d75fb'),
    'HL-B2158W': ('2026-11-09T14:01:04.511646+00:00',
                  '37fba167920c15d0be31caedfdfd057248d6ab86f659b0fe7118f82688ddc20a'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'reports/p0_9_time_binding_independent_20261112.json')
    args = parser.parse_args()
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    now = datetime.now(timezone.utc)
    records = []

    def record(group, ident, passed, **evidence):
        records.append({'group': group, 'id': ident,
                        'expectation_met': bool(passed), **evidence})

    def view():
        known = load_official_catalog()
        result = catalog_from_brother_snapshot(
            _read_bounded_json(BROTHER_SNAPSHOT), known_catalog=known, now=now)
        result['old_model_ids'] = [p['model_id'] for p in known['products']]
        return result

    def from_manifest(changed, callback=load_reviewed_local_replay):
        original_read = Path.read_text

        def read(path, *a, **kw):
            return json.dumps(changed) if path == MANIFEST else original_read(path, *a, **kw)

        with patch.object(Path, 'read_text', read):
            return callback()

    def changed_manifest(model, value, missing=False):
        changed = deepcopy(manifest)
        row = next(x for x in changed['models'] if x['model_id'] == model)
        if missing:
            row.pop('observed_at')
        else:
            row['observed_at'] = value
        return changed

    baseline = load_reviewed_local_replay()
    details = {}
    for model, (stamp, digest) in EVENTS.items():
        body = (ROOT / 'data/raw/p0_8_official_details' / (digest + '.html')).read_bytes()
        raw = parse_detail(model, body, observed_at=datetime.fromisoformat(stamp))
        details[model] = raw
        row = next(x for x in baseline['products'] if x['model_id'] == model)
        source_row = next(x for x in manifest['models'] if x['model_id'] == model)
        record('original_positive', model,
               hashlib.sha256(body).hexdigest() == digest
               and source_row['observed_at'] == stamp
               and row['manufacturer_detail_evidence']['observed_at'] == stamp
               and row['facts']['wireless']['value'] is True
               and row['consumables'] == raw['consumables']
               and (model != 'HL-B2188DW' or row['facts']['auto_duplex']['value'] is True)
               and (model != 'HL-10W' or row['facts']['pay_per_page_consumables']['value'] is True),
               source_sha256=digest, original_observed_at=stamp)

        original = datetime.fromisoformat(stamp)
        invalid = [
            ('minus_one_microsecond', (original - timedelta(microseconds=1)).isoformat()),
            ('plus_one_microsecond', (original + timedelta(microseconds=1)).isoformat()),
            ('fraction_lost', original.replace(microsecond=0).isoformat()),
            ('same_wall_clock_wrong_offset', stamp.replace('+00:00', '+08:00')),
            ('original_exploit_new_past_time', '2026-11-10T12:00:00+00:00'),
            ('naive_same_clock', original.replace(tzinfo=None).isoformat()),
            ('date_only', '2026-11-09'), ('null', None), ('boolean', True),
            ('missing', None), ('invalid_offset', stamp.replace('+00:00', '+25:00')),
            ('invalid_date', '2026-11-31T14:01:03+00:00'),
            ('future', '2099-01-01T00:00:00Z'),
        ]
        for ident, value in invalid:
            for path in ('manifest', 'direct_reviewed'):
                try:
                    if path == 'manifest':
                        from_manifest(changed_manifest(model, value, ident == 'missing'))
                    else:
                        altered = deepcopy(raw)
                        if ident == 'missing':
                            altered.pop('observed_at')
                        else:
                            altered['observed_at'] = value
                        enrich_discovered_catalog(view(), [altered], reviewed_local_replay=True)
                    error = None
                except Exception as exc:
                    error = exc
                record('changed_time_rejected', f'{model}/{path}/{ident}',
                       isinstance(error, ValueError),
                       exception=None if error is None else type(error).__name__,
                       reason=None if error is None else str(error))

        equivalents = [
            ('plus_14_next_calendar_day', original.astimezone(timezone(timedelta(hours=14))).isoformat()),
            ('minus_12', original.astimezone(timezone(timedelta(hours=-12))).isoformat()),
            ('quarter_hour_zone', original.astimezone(timezone(timedelta(hours=5, minutes=45))).isoformat()),
            ('compact_utc_offset', stamp.replace('+00:00', '+0000')),
            ('negative_zero_offset', stamp.replace('+00:00', '-00:00')),
            ('utc_z', stamp.replace('+00:00', 'Z')),
        ]
        for ident, value in equivalents:
            for path in ('manifest', 'direct_reviewed'):
                if path == 'manifest':
                    catalog = from_manifest(changed_manifest(model, value))
                else:
                    altered = deepcopy(raw)
                    altered['observed_at'] = value
                    catalog = enrich_discovered_catalog(view(), [altered], reviewed_local_replay=True)
                row = next(x for x in catalog['products'] if x['model_id'] == model)
                record('equivalent_instant_accepted', f'{model}/{path}/{ident}',
                       row['manufacturer_detail_evidence']['observed_at'] == stamp
                       and row['facts']['wireless']['value'] is True,
                       input_observed_at=value,
                       output_observed_at=row['manufacturer_detail_evidence']['observed_at'])

        for day, age, stale in [(date(2026, 12, 8), 29, False),
                                (date(2026, 12, 9), 30, False),
                                (date(2026, 12, 10), 31, True)]:
            catalog = deepcopy(baseline)
            catalog['recorded_on'] = day.isoformat()
            comparison = compare_products(catalog, category='printer', required={'wireless': True}, today=day)
            row = next(x for x in comparison['candidates'] if x['model_id'] == model)
            original_product = next(x for x in baseline['products'] if x['model_id'] == model)
            passed = (row['manufacturer_detail_age_days'] == age
                      and row['manufacturer_detail_is_stale'] == stale
                      and ('wireless' in row['required_unknown']) == stale
                      and ('wireless' in row['required_met']) == (not stale)
                      and row['consumables'] == ([] if stale else original_product['consumables'])
                      and row['billing_model'] == ('unknown' if stale else raw['billing_model'])
                      and not comparison['purchase_recommendation_approved']
                      and not comparison['transactions_enabled'])
            record('simulated_age_boundary', f'{model}/{day}', passed,
                   simulated_comparison_date=day.isoformat(), age_days=row['manufacturer_detail_age_days'],
                   stale=row['manufacturer_detail_is_stale'], required_met=row['required_met'],
                   required_unknown=row['required_unknown'], billing_model=row['billing_model'])

        # 即使原件/时间正确，未申请已审路径仍不能获得硬条件事实。
        catalog = enrich_discovered_catalog(view(), [raw])
        row = next(x for x in catalog['products'] if x['model_id'] == model)
        compared = compare_products(catalog, category='printer', required={'wireless': True})
        candidate = next(x for x in compared['candidates'] if x['model_id'] == model)
        record('unreviewed_isolation', model,
               row.get('manufacturer_claim_pending_review', {}).get('status') == 'awaiting_per_field_review'
               and 'manufacturer_detail_evidence' not in row
               and 'wireless' in candidate['required_unknown']
               and not candidate['required_met'] and not candidate['required_failed'])

    # 验证正常内容入口遇改时是显式降级，不悄悄重用旧详情摘要。
    from shopping_decision.dialogue_flow import new_dialogue, apply_turn, compare_dialogue
    answers = {'category': 'printer', 'needs_color': False, 'accepts_outsourced_color': True,
               'usage': '家用', 'monthly_pages_range': [0, 50], 'requires_wireless': True}
    state = apply_turn(new_dialogue(), answers, raw_text='独立合成评估，不写真人档案')
    for model in EVENTS:
        degraded = from_manifest(changed_manifest(model, '2026-11-10T12:00:00+00:00'),
                                 lambda: compare_dialogue(state))
        record('normal_entry_rejects_refresh', model,
               bool(degraded.get('source_warning'))
               and 'frozen_p0_8_local_field_review' not in json.dumps(degraded)
               and '2026-11-10T12:00:00+00:00' not in json.dumps(degraded),
               source_mode=degraded.get('source_mode'), source_warning=degraded.get('source_warning'))

    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONUTF8', 'PYTHONIOENCODING')}
    turns = [{'text': '独立合成评估：自动双面',
              'answers': {**answers, 'requires_auto_duplex': True}},
             {'text': '独立合成改答：改为彩色', 'answers': {'needs_color': True}}]
    proc = subprocess.run([sys.executable, '-m', 'shopping_decision.dialogue_flow'], cwd=ROOT, env=env,
                          input=''.join(json.dumps(t, ensure_ascii=False) + '\n' for t in turns).encode('utf-8'),
                          capture_output=True, timeout=30)
    output = [json.loads(line) for line in proc.stdout.decode('utf-8').splitlines()]
    candidate_rows = [x['comparison']['comparison']['comparison']['candidates'] for x in output[1:]]
    record('normal_cli', 'default_windows_utf8_bytes_two_turns',
           proc.returncode == 0 and [x['version'] for x in output[1:]] == [1, 2]
           and output[-1]['history']['old_conclusions_invalidated']
           and all(len(x) == 3 for x in candidate_rows)
           and any(x['status'] == 'excluded_by_verified_spec' for x in candidate_rows[0])
           and all(x['status'] == 'excluded_by_verified_spec' for x in candidate_rows[1])
           and all(not x['comparison']['comparison']['comparison']['purchase_recommendation_approved']
                   and not x['comparison']['comparison']['comparison']['transactions_enabled'] for x in output[1:]),
           returncode=proc.returncode, versions=[x['version'] for x in output[1:]],
           candidate_counts=[len(x) for x in candidate_rows],
           old_conclusions_invalidated=output[-1]['history']['old_conclusions_invalidated'],
           interpreter=sys.executable, utf8_environment_overrides=False)

    record('source_unchanged', 'original_manifest_and_raw_archives',
           MANIFEST.read_bytes() == manifest_bytes
           and all(hashlib.sha256((ROOT / 'data/raw/p0_8_official_details' / (digest + '.html')).read_bytes()).hexdigest()
                   == digest for _, digest in EVENTS.values()))
    groups = {}
    for case in records:
        counts = groups.setdefault(case['group'], {'passed': 0, 'total': 0})
        counts['passed'] += int(case['expectation_met'])
        counts['total'] += 1
    result = {'role': 'independent_reviewer', 'observed_at': now.isoformat(),
              'passed': sum(c['expectation_met'] for c in records), 'total': len(records),
              'groups': groups, 'cases': records,
              'limitations': ['手选时间/边界诊断，不是总体准确率', '日历日30天复核策略，不是720小时TTL',
                              '未验Windows GUI或真实平台SKU/地区报价'],
              'boundaries': {'credential_reads': 0, 'new_haina_business_calls': 0, 'paid_calls': 0,
                             'account_actions': 0, 'transactions': 0, 'business_code_modified': False,
                             'git_commit': False, 'git_push': False}}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'total': result['total'], 'groups': groups}, ensure_ascii=True, indent=2))
    return 0 if result['passed'] == result['total'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
