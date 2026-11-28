from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase
from shopping_decision.claim_gate import publish_checked_comparison

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/"handoffs/evaluator_executor/PRINTER-CANDIDATE-TRADEOFF-20261125/evidence/executor/model/web-gpt-20261125"
HP="HP M232dw"
BROTHER="Brother HL-L1238W"

def fixture(case):
    return json.loads((OLD/case/"request.json").read_text(encoding="utf8"))

def public(case):
    return publish_checked_comparison(fixture(case))

class UnifiedActions(TestCase):
    def test_four_cases(self):
        for case in ("C08","C08_SHORT"):
            p=public(case)
            self.assertEqual(p["next_actions"],[])
            self.assertTrue(all(a["research_status"]=="excluded_for_research" for a in p["assessments"]))
        p=public("C12")
        self.assertEqual(p["next_actions"][0]["candidate_id"],HP)
        self.assertEqual(p["next_actions"][0]["requirement_id"],"cognition:color_print")
        self.assertTrue(all(a["candidate_id"]==HP for a in p["next_actions"]))
    def test_source_time_and_candidate_order(self):
        b=fixture("C08")
        for s in b["sources"]: s.pop("observed_at",None)
        p=publish_checked_comparison(b)
        self.assertTrue(all(a["research_status"]=="pending_evidence" for a in p["assessments"]))
        self.assertTrue(p["next_actions"])
        before=p["next_actions"]
        b["candidates"].reverse()
        self.assertEqual(before,publish_checked_comparison(b)["next_actions"])
    def test_origins(self):
        b=fixture("C01")
        model=json.loads((OLD/"C01/response.json").read_text(encoding="utf8"))
        r=publish_checked_comparison(b)
        for origin in ("manual","model"):
            v=publish_checked_comparison(b,model if origin=="model" else None,origin=origin)
            self.assertEqual(r["next_actions"],v["next_actions"])
            self.assertEqual(r["assessments"],v["assessments"])
