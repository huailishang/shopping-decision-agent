"""Offline evaluator audit; never fetch sources or modify submitted evidence."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path.cwd()
    task = Path('handoffs/evaluator_executor/HNA-EVIDENCE-REOPEN-20261116')
    evidence = root / task / 'evidence'
    snapshot = json.loads((evidence / 'accepted_submission_snapshot.json').read_text(encoding='utf-8'))
    changed = [name for name, ref in snapshot['files'].items()
               if not (root / name).is_file() or sha(root / name) != ref['sha256']]
    assert not changed, changed
    meta_results = []
    for name in snapshot['files']:
        if not name.endswith('.meta.json'):
            continue
        path = root / name
        meta = json.loads(path.read_text(encoding='utf-8'))
        for stream in ('stdout', 'stderr'):
            log = path.parent / meta[f'{stream}_path']
            assert sha(log) == meta[f'{stream}_sha256'], str(log)
            assert log.stat().st_size == meta[f'{stream}_bytes'], str(log)
        meta_results.append({'path': name, 'exit_code': meta['exit_code']})

    receipt = json.loads((evidence / 'acquisition_receipt.json').read_text(encoding='utf-8'))
    plan = json.loads((root / task / 'acquisition_plan.json').read_text(encoding='utf-8'))
    public = [a for a in receipt['actions'] if a['kind'] != 'local']
    binding_types = Counter(Path(a['evidence']['path']).suffix for a in public)
    prior = json.loads((root / plan['prior_ledger']['path']).read_text(encoding='utf-8-sig'))
    local_pdf = root / plan['routes'][0]['local_inputs'][2]
    assert sha(local_pdf) == local_pdf.stem
    local = json.loads((root / plan['routes'][0]['local_inputs'][0]).read_text(encoding='utf-8-sig'))

    def sources(value):
        found = []
        if isinstance(value, dict):
            if value.get('id') in ('R7', 'R10'):
                found.append(value)
            for item in value.values():
                found.extend(sources(item))
        elif isinstance(value, list):
            for item in value:
                found.extend(sources(item))
        return found

    old_sources = sources(local)
    assert {row['id'] for row in old_sources} == {'R7', 'R10'}
    haina = []
    for name in plan['routes'][1]['local_inputs']:
        data = json.loads((root / name).read_text(encoding='utf-8-sig'))
        haina.append({'path': name, 'sha256': sha(root / name),
                      'captured_link_count': len(data.get('links', [])),
                      'agreement_name_mentioned': any(s in data.get('text', '') for s in
                                                     ('用户协议', 'MCP开发者合作协议'))})

    spec = importlib.util.spec_from_file_location('frozen_delivery_checker', root / task / 'check_delivery.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    with tempfile.TemporaryDirectory(prefix='shopping-review-offline-') as directory:
        temporary_root = Path(directory)
        prior_copy = temporary_root / plan['prior_ledger']['path']
        prior_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / plan['prior_ledger']['path'], prior_copy)
        note = temporary_root / task / 'evidence/collected/SYNTHETIC_UNOBSERVED.txt'
        note.parent.mkdir(parents=True)
        note.write_text('SYNTHETIC: no source was fetched; this is not observation evidence.\n'
                        'https://www.brother.cn/minisite/bcnactivity/FAQ.html\n', encoding='utf-8')
        altered = copy.deepcopy(receipt)
        ref = {'path': note.relative_to(temporary_root).as_posix(), 'sha256': sha(note)}
        for action in altered['actions']:
            action['evidence'] = copy.deepcopy(ref)
        altered['owner_request']['evidence'] = copy.deepcopy(ref)
        placeholder_result = checker.validate_receipt(temporary_root, plan, altered)
        for action in altered['actions']:
            action['recorded_at'] = 'SYNTHETIC-NOT-A-TIMESTAMP'
        timestamp_result = checker.validate_receipt(temporary_root, plan, altered)

    result = {
        'schema': 'offline-independent-acquisition-audit/v1',
        'accepted_submission_files_checked': len(snapshot['files']),
        'accepted_submission_changed': changed,
        'executor_meta_triplets_checked': len(meta_results),
        'executor_history_exit_codes': meta_results,
        'actions_declared': len(receipt['actions']),
        'public_actions_declared': len(public),
        'public_action_evidence_extensions': dict(binding_types),
        'declared_public_actions': [{'id': a['id'], 'kind': a['kind'], 'recorded_at': a['recorded_at'],
                                    'url': a['url'], 'evidence': a['evidence']} for a in public],
        'timestamp_frequencies': dict(Counter(a['recorded_at'] for a in receipt['actions'])),
        'prior_reads_declared': prior['budget']['document_reads_used'],
        'total_reads_declared': prior['budget']['document_reads_used'] + len(public),
        'candidate_count': len(receipt['materials']),
        'cached_brother_pdf_sha_matches': True,
        'old_source_records': old_sources,
        'haina_local_snapshots': haina,
        'supplemental_synthetic_boundary_probes': {
            'all_bindings_replaced_by_explicitly_unobserved_note': placeholder_result,
            'invalid_action_timestamps': timestamp_result,
            'interpretation': 'Demonstrates structural-only scope, not falsification by Executor. '
                              'Frozen checker was not changed. Synthetic data never admitted as real evidence.'},
        'manual_provenance_finding': 'All six public actions bind narrative Markdown notes. '
                                     'No separate original tool request/response or run locator was supplied in accepted evidence. '
                                     'Contemporaneous remote outcomes, action order and absence of omitted attempts cannot be independently reconstructed.',
        'network_calls_by_this_audit': 0,
        'conclusion_limit': 'Integrity, arithmetic and old local source compatibility are verified. '
                            'This does not verify remote action history, license, product effectiveness or transactions.'}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
