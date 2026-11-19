"""Frozen offline scope and bounded execution-record checks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def need(value, message):
    if not value:
        raise ValueError(message)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--check', choices=['frozen','ledger'], required=True)
    p.add_argument('--frozen-sha', required=True)
    a = p.parse_args()
    try:
        manifest = TASK / 'FROZEN_INPUTS.json'
        need(sha(manifest) == a.frozen_sha, 'repair frozen manifest changed')
        m = json.loads(manifest.read_text(encoding='utf-8'))
        for name, expected in m['files'].items():
            need(sha(ROOT/name) == expected, 'protected input changed: '+name)
        inventory = {x.relative_to(ROOT).as_posix() for folder,glob in
            [('shopping_decision','*.py'),('tests','*.py'),('knowledge','*.json'),('desktop','*.java'),('scripts','*.py')]
            for x in (ROOT/folder).rglob(glob)}
        need(inventory == set(m['product_inventory']), 'product inventory changed')
        if a.check == 'ledger':
            d = json.loads((TASK/'evidence/iterations.json').read_text(encoding='utf-8'))
            need(d['task_id'] == m['task_id'], 'wrong ledger task')
            need(d['historical_parent_effective_hours'] == 'unknown', 'historical work time invented')
            need(type(d['concentrated_iterations']) is int and 1 <= d['concentrated_iterations'] <= 2,
                 'concentrated iteration budget exceeded')
            need(d['elapsed_basis'] == 'measured_wall_upper_bound', 'unverifiable time basis')
            segments = d['segments']
            need(isinstance(segments,list) and segments, 'missing real work segments')
            seconds=0; previous=None
            for seg in segments:
                start,end = (datetime.fromisoformat(seg[k]) for k in ['started_at','ended_at'])
                need(start.tzinfo is not None and end.tzinfo is not None, 'timezone required')
                need(end >= start and end <= datetime.now(timezone.utc), 'invalid work time')
                need(previous is None or start >= previous, 'overlapping work segments')
                need(bool(seg.get('activity')), 'missing work activity')
                seconds += (end-start).total_seconds(); previous=end
            need(seconds <= 4*3600, 'conservative work-time bound exceeded')
            for field in ['new_external_calls','credentials_read','messages_sent','transactions','git_commit','git_push']:
                need(d.get(field) == 0, 'forbidden side effect: '+field)
            need((TASK/'REPORT.md').is_file(), 'missing concentrated report')
            print(json.dumps({'status':'ledger_present','measured_wall_seconds_upper_bound':seconds}))
        else:
            print(json.dumps({'status':'frozen_match','protected_files':len(m['files'])}))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'status':'check_failed','reason':str(exc)},ensure_ascii=False))
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
