"""Discover and run all required new regression groups, rejecting empty delivery."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
PATTERNS=('test_session_decision_contract.py','test_cost_scenario_binding.py',
          'test_model_receipt_boundaries.py','test_evidence_snapshot_lineage.py',
          'test_printer_decision_journey.py')

def main():
    suite=unittest.TestSuite()
    found={}
    missing=[]
    for name in PATTERNS:
        if not (ROOT/'tests'/name).is_file():
            found[name]=0
            missing.append(name)
            continue
        group=unittest.TestLoader().discover(str(ROOT/'tests'),pattern=name)
        found[name]=group.countTestCases()
        if not found[name]:
            missing.append(name)
        suite.addTests(group)
    print(json.dumps({'discovered':found,'missing_or_empty':missing},ensure_ascii=False),flush=True)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return int(bool(missing) or not result.wasSuccessful())

if __name__=='__main__':
    raise SystemExit(main())
