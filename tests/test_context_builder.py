from copy import deepcopy
from unittest import TestCase
from shopping_decision.context_builder import build_context,byte_proxy
from shopping_decision.claim_gate import publish_checked_comparison
from shopping_decision.model_adapter import ModelRoute
from test_unified_decision_actions import fixture,public

ROUTE=ModelRoute("offline","mock","responses",32000,4096,"synthetic fixture")

def open_color():
    b=fixture("C08")
    for s in b["sources"]: s.pop("observed_at",None)
    return publish_checked_comparison(b)

class ContextTests(TestCase):
    def test_source_gate_and_skip(self):
        for case in ("C08","C08_SHORT"):
            self.assertEqual(build_context(public(case),ROUTE)["mode"],"rules_only")
        p=open_color()
        plan=build_context(p,ROUTE,input_cap=25000)
        self.assertEqual(plan["mode"],"model_rank_actions")
        req=plan["packet"]["required"]
        self.assertTrue(all(x[1]=="pending_evidence" for x in req["candidate_eligibility"]))
        self.assertFalse(req["authorization"]["purchase"])
        self.assertEqual(len(req["allowed_actions"]),2)
    def test_budget_and_omission(self):
        p=open_color()
        big=build_context(p,ROUTE,input_cap=28000)
        required_only=dict(big["packet"],optional=[])
        from shopping_decision.model_adapter import payload
        from shopping_decision.context_builder import SYSTEM
        minimum=byte_proxy(payload(ROUTE,SYSTEM,required_only,512))
        small=build_context(p,ROUTE,input_cap=minimum)
        self.assertEqual({k:v for k,v in small["packet"]["required"].items() if k!="context_id"},
                         {k:v for k,v in big["packet"]["required"].items() if k!="context_id"})
        self.assertNotEqual(small["packet"]["required"]["context_id"],big["packet"]["required"]["context_id"])
        self.assertTrue(small["ledger"]["omitted"])
        self.assertTrue(all(o["recovery"]["claim_id"]==o["id"] for o in small["ledger"]["omitted"]))
        with self.assertRaisesRegex(ValueError,"required_wire_over_budget"):
            build_context(p,ROUTE,input_cap=minimum-1)
        for bad in (True,0,-1):
            with self.assertRaises(ValueError):
                build_context(p,ROUTE,input_cap=bad)
        with self.assertRaises(ValueError):
            build_context(p,None)
    def test_context_preserves_admitted_refutation(self):
        b=fixture("C08")
        b["facts"]=[f for f in b["facts"] if f["id"]!="hp-mono"]
        p=publish_checked_comparison(b)
        self.assertEqual(build_context(p,ROUTE)["mode"],"rules_only")
        self.assertTrue(all(a["candidate_id"]=="HP M232dw" for a in p["next_actions"]))
