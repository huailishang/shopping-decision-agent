"""Independent frozen checks. No product changes and no external calls."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
TASK = 'handoffs/evaluator_executor/PRINTER-CANDIDATE-TRADEOFF-20261125'
commands = [
    ['python3', '-X', 'utf8', TASK + '/VERIFY_CANDIDATES.py'],
    ['python3', '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_candidate_tradeoff.py', '-v'],
    ['python3', '-X', 'utf8', 'handoffs/evaluator_executor/PRINTER-COGNITION-TO-COMPARISON-20261124/REPLAY_CASES.py'],
    ['python3', '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-q'],
    ['python3', '-X', 'utf8', 'scripts/audit_model_history_readonly.py', '--task', 'handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118'],
    ['python3', '-X', 'utf8', TASK + '/VERIFY_SCOPE.py', '--phase', 'post'],
    ['python3', '-X', 'utf8', 'handoffs/context-model-pilot-20261126/test_pilot.py'],
]
results = []
for index, command in enumerate(commands, 1):
    label = 'VP-%02d' % index if index <= 6 else 'PILOT'
    started = datetime.now(timezone.utc).isoformat()
    import os
    environment = dict(os.environ, PYTHONPATH=str(ROOT))
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=240, env=environment)
    (OUT / (label + '.stdout.txt')).write_bytes(result.stdout)
    (OUT / (label + '.stderr.txt')).write_bytes(result.stderr)
    row = dict(id=label, command=command, started_at_utc=started,
               finished_at_utc=datetime.now(timezone.utc).isoformat(), exit_code=result.returncode)
    results.append(row)
    print(json.dumps(row), flush=True)
(OUT / 'frozen-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
sys.exit(int(any(row['exit_code'] for row in results)))
