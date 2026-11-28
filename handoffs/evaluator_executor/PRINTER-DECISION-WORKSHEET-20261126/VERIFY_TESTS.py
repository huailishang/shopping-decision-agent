"""Require meaningful implemented worksheet test groups, then actually run them."""
from pathlib import Path
import sys,unittest,json
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
GROUPS=['test_decision_worksheet','test_worksheet_bridge','test_worksheet_persistence','test_worksheet_evidence','test_worksheet_journeys']
suite=unittest.TestSuite();counts={};missing=[]
for group in GROUPS:
    if not (ROOT/'tests'/(group+'.py')).is_file():missing.append(group);continue
    tests=unittest.defaultTestLoader.loadTestsFromName(group)
    counts[group]=tests.countTestCases();suite.addTests(tests)
print(json.dumps({'groups':counts,'missing':missing},ensure_ascii=False))
if missing or any(n<5 for n in counts.values()):raise SystemExit('五组必须存在且各至少5个有业务辨别力的用例；不按数量代替人工语义审查。')
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
