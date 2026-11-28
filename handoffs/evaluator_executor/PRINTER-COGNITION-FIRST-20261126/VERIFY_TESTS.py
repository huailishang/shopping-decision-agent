"""Five mandatory cognition-first behavior suites must exist and run without SKIP."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
names=['test_cognition_guide','test_guided_requirements','test_cognition_guide_bridge','test_cognition_context_lineage','test_cognition_guide_persistence']
missing=[x for x in names if not (ROOT/'tests'/(x+'.py')).is_file()]
if missing:print('Missing behavior suites: '+', '.join(missing));raise SystemExit(1)
suite=unittest.defaultTestLoader.loadTestsFromNames(names)
r=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(int(not r.wasSuccessful() or bool(r.skipped) or r.testsRun==0))
