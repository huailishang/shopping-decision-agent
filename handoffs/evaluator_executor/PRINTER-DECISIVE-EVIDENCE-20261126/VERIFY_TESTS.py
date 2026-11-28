"""New behavior tests must exist and actually execute; missing files are failures."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
names=['test_decision_uncertainty','test_decisive_evidence_actions','test_uncertainty_bridge','test_uncertainty_persistence','test_decision_note']
missing=[n for n in names if not (ROOT/'tests'/(n+'.py')).is_file()]
if missing:print('Missing implementations/tests: '+', '.join(missing));raise SystemExit(1)
suite=unittest.defaultTestLoader.loadTestsFromNames(names)
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(int(not result.wasSuccessful() or bool(result.skipped) or result.testsRun==0))
