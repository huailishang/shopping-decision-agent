"""Evaluator diagnostic only; preserves executor artifacts and frozen gates."""
from pathlib import Path
from datetime import datetime, timezone
import base64
import hashlib
import json
import os
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
TASK = OUT.parents[2]
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))
from shopping_decision.chat_bridge import new_dialogue, submit_message


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(label, argv):
    start = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True,
                            env=dict(os.environ, PYTHONPATH='.:tests'), timeout=300)
    (OUT / (label + '.stdout')).write_bytes(result.stdout)
    (OUT / (label + '.stderr')).write_bytes(result.stderr)
    meta = dict(argv=argv, start=start, end=datetime.now(timezone.utc).isoformat(),
                elapsed_seconds=time.monotonic()-tick, exit_code=result.returncode)
    save(OUT / (label + '.meta.json'), meta)
    return meta


def read_view(state, folder):
    folder.mkdir(parents=True)
    request = dict(schema_version=1, action='guide', state=state, worksheet=None, payload={})
    save(folder / 'stdin.json', request)
    result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'shopping_decision.chat_bridge', '--worksheet-stdin'],
                            cwd=ROOT, input=json.dumps(request, ensure_ascii=False).encode(),
                            capture_output=True, timeout=30)
    (folder / 'stdout').write_bytes(result.stdout)
    (folder / 'stderr').write_bytes(result.stderr)
    if result.returncode:
        raise RuntimeError(f'bridge exit {result.returncode}')
    view = {k: base64.b64decode(v).decode() for k, v in
            (line.split('\t', 1) for line in result.stdout.decode().splitlines())}
    save(folder / 'response.json', view)
    return view


started = datetime.now(timezone.utc).isoformat()
executor_before = {p.relative_to(ROOT).as_posix(): digest(p)
                   for p in (TASK / 'evidence/executor').rglob('*') if p.is_file()}
product_paths = list((ROOT / 'shopping_decision').glob('*.py')) + list((ROOT / 'desktop').glob('*.java'))
product_before = {p.relative_to(ROOT).as_posix(): digest(p) for p in product_paths}
save(OUT / 'start-snapshot.json', dict(started=started, executor=executor_before,
                                     product=product_before, holdouts_sha256=digest(OUT/'HOLDOUTS.json')))
manifest = json.loads((TASK / 'evidence/executor/manifest.json').read_text(encoding='utf-8-sig'))
mismatches = [item['path'] for item in manifest['artifacts']
              if digest(ROOT/item['path']) != item['sha256']]
save(OUT / 'manifest-check.json', dict(total=len(manifest['artifacts']), mismatches=mismatches,
     current_note='Evaluator appended diagnostic entry to CURRENT after reading executor handoff; mismatch is recorded, not repaired.'))

gates = {}
for phase in ['scope', 'controls', 'delivery']:
    gates[phase] = run(phase, [sys.executable, '-X', 'utf8', str(TASK/'VERIFY_PACKET.py'), phase])
    print(phase, gates[phase]['exit_code'], flush=True)
gates['scenarios'] = run('scenarios', [sys.executable, '-X', 'utf8', str(TASK/'VERIFY_SCENARIOS.py'), '--role', 'evaluator'])
print('scenarios', gates['scenarios']['exit_code'], flush=True)

fixture = json.loads((OUT / 'HOLDOUTS.json').read_text(encoding='utf8'))
rows = []
for case in fixture['cases']:
    state = submit_message(submit_message(new_dialogue(), 'category', '打印机'), 'usage', case['usage'])
    view = read_view(state, OUT/case['id']/'read-00')
    initial = view['prompt_field']
    focus = json.loads(view['guidance_focus_json'])
    context = json.loads(view['cognition_context_json'])
    note = json.loads(view['decision_note_json'])
    report = json.loads(view['report_json'])
    checks = dict(relevant=initial in case['allowed_fields'],
                  no_auto_confirmation=json.loads(view['state_json']) == state,
                  same_focus=focus == context['guidance_focus'] == note['guidance_focus'],
                  same_prompt=focus['field'] == initial and focus['question'] == view['prompt'],
                  safe=all(report[k] is False for k in ['purchase_recommendation_approved', 'transactions_enabled', 'live_price_verified']))
    continuation = []
    reached = False
    if case.get('continue'):
        for number in range(12):
            field = view['prompt_field']
            if not field:
                break
            answer = fixture['continuation_policy']['answers'].get(field, '暂不确定')
            continuation.append(dict(field=field, answer=answer))
            state = submit_message(state, field, answer)
            view = read_view(state, OUT/case['id']/f'read-{number+1:02}')
            ctx = json.loads(view['cognition_context_json'])
            target = case['allowed_fields'][0]
            confirmed = ctx['user_confirmed'].get(target) == case['target_value']
            dimension = {'requires_scan':'scan', 'requires_auto_duplex':'auto_duplex'}.get(target)
            evidence_next = (ctx['usage_research']['status'] == 'research_required' if target == 'idle_weeks_pattern'
                             else any(c['dimension'] == dimension for c in ctx['candidate_facts']))
            reached = confirmed and evidence_next
            if reached:
                break
    rows.append(dict(id=case['id'], kind=case['kind'], expected=case['allowed_fields'], initial=initial,
                     checks=checks, passed=all(checks.values()), continuation=continuation,
                     target_and_research_reached=reached if case.get('continue') else None,
                     terminal_field=view['prompt_field'], terminal_prompt=view['prompt']))
    print(case['id'], initial, rows[-1]['passed'], reached, flush=True)
save(OUT/'holdout-results.json', dict(passed=sum(r['passed'] for r in rows), total=len(rows),
     continuation_passed=sum(r['target_and_research_reached'] is True for r in rows), continuation_total=3,
     cases=rows, holdouts_sha256=digest(OUT/'HOLDOUTS.json')))

executor_after = {p.relative_to(ROOT).as_posix(): digest(p)
                  for p in (TASK/'evidence/executor').rglob('*') if p.is_file()}
product_after = {p.relative_to(ROOT).as_posix(): digest(p) for p in product_paths}
save(OUT/'summary.json', dict(started=started, ended=datetime.now(timezone.utc).isoformat(),
     gates=gates, manifest_mismatches=mismatches, executor_artifacts_unchanged=executor_before == executor_after,
     products_unchanged=product_before == product_after, holdout_passed=sum(r['passed'] for r in rows),
     continuation_passed=sum(r['target_and_research_reached'] is True for r in rows),
     limit='Diagnostic, not L3; no independent full unit/native rerun; no claim of complete effective work time.'))
print('diagnostic saved', flush=True)
