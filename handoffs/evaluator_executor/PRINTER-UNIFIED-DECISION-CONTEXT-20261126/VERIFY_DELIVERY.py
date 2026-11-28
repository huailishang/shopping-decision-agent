"""Require actual new regression groups; execute them, never count empty discovery."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
PATTERNS=('test_unified_decision_actions.py','test_context_builder.py','test_model_adapter.py',
          'test_action_ranking.py','test_printer_lifecycle.py')

def main():
    suite=unittest.TestSuite()
    discovered={}
    missing=[]
    for name in PATTERNS:
        if not (ROOT/'tests'/name).is_file():
            discovered[name]=0
            missing.append(name)
            continue
        tests=unittest.TestLoader().discover(str(ROOT/'tests'),pattern=name)
        count=tests.countTestCases()
        discovered[name]=count
        if not count:
            missing.append(name)
        suite.addTests(tests)
    print(json.dumps({'discovered':discovered,'missing_or_empty':missing},ensure_ascii=False),flush=True)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return int(bool(missing) or not result.wasSuccessful())

if __name__=='__main__':
    raise SystemExit(main())
