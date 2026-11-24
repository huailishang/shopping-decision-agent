"""Exact model scope admission through shared comparison and actual printer chat."""
from copy import deepcopy
from pathlib import Path
import runpy
import unittest

from shopping_decision.confirmed_comparison import publish_confirmed_comparison
from shopping_decision.evidence_comparison import SAFE_FLAGS

ROOT = Path(__file__).resolve().parents[1]
HANDOFFS = ROOT / "handoffs/evaluator_executor"
TRANSFER = runpy.run_path(str(HANDOFFS / "GENERIC-CONFIRMED-REQUIREMENTS-20261124/VERIFY_TRANSFER.py"))
CHAT = runpy.run_path(str(HANDOFFS / "PRINTER-CHAT-CONTEXT-20261124/evidence/evaluator/replay_session_conditions.py"))
MISSING = object()


class ExactModelScopeTests(unittest.TestCase):
    def kettle(self, fact_scope=MISSING, source_scope=MISSING):
        bundle, requirements = TRANSFER["base_case"]()
        short, exact = "lab-kettle-x", "lab-kettle-x-plus"
        bundle["candidates"] = [{"id": exact}, {"id": short}]
        for source in bundle["sources"]:
            source.update(scope_models=[short, exact])
        height, volume = bundle["facts"]
        height.update(id="short-height", candidate_id=short)
        volume.update(id="short-volume", candidate_id=short)
        src = next(s for s in bundle["sources"] if s["id"] == height["source_id"])
        separate = dict(src, id="short-height-source")
        bundle["sources"].append(separate)
        height["source_id"] = separate["id"]
        if fact_scope is not MISSING:
            height["scope_models"] = fact_scope
        if source_scope is not MISSING:
            separate["scope_models"] = source_scope
        bundle["facts"] = [dict(volume, id="exact-volume", candidate_id=exact),
                           dict(height, id="exact-height", candidate_id=exact,
                                source_id=src["id"], scope_models=[exact]), height, volume]
        before = deepcopy(bundle)
        result = publish_confirmed_comparison(
            bundle, requirements, as_of=TRANSFER["TODAY"],
            deployment_region=TRANSFER["DEPLOYMENT"])
        self.assertEqual(bundle, before)
        self.assertIsNotNone(result)
        self.assertTrue(all(result[f] is False for f in SAFE_FLAGS))
        claims = {(c["candidate_id"], c["dimension"]): c for c in result["claims"]}
        assessments = {a["candidate_id"]: a["research_status"] for a in result["assessments"]}
        self.assertEqual(claims[short, "capacity"]["status"], "met")
        self.assertEqual(claims[short, "capacity"]["supporting_fact_ids"], ["short-volume"])
        self.assertEqual(claims[exact, TRANSFER["HEIGHT"]]["status"], "met")
        self.assertEqual(assessments[exact], "eligible_for_research")
        return claims[short, TRANSFER["HEIGHT"]], assessments[short]

    def assert_pending(self, claim, disposition):
        self.assertEqual(claim["status"], "unknown")
        self.assertEqual(claim["supporting_fact_ids"], [])
        self.assertEqual(disposition, "pending_evidence")

    def test_fact_scope_malformed_types_do_not_admit(self):
        for scope in ("lab-kettle-x-plus", "lab-kettle-x", None, [], {},
                      1, True, ["lab-kettle-x", 9], ["lab-kettle-x", ""],
                      ["lab-kettle-x", " "], ["lab-kettle-x", " padded "]):
            with self.subTest(scope=scope):
                self.assert_pending(*self.kettle(fact_scope=scope))

    def test_source_scope_malformed_even_for_synthetic(self):
        for scope in ("lab-kettle-x-plus", "lab-kettle-x", None, [], {},
                      1, False, ["lab-kettle-x", None], ["lab-kettle-x", ""]):
            with self.subTest(scope=scope):
                self.assert_pending(*self.kettle(source_scope=scope))

    def test_source_and_fact_scope_intersection(self):
        short, exact = "lab-kettle-x", "lab-kettle-x-plus"
        for a, b in (([short], [exact]), ([exact], [short]), ([exact], [exact])):
            with self.subTest(fact=a, source=b):
                self.assert_pending(*self.kettle(fact_scope=a, source_scope=b))
        for a, b in (([short], [short, exact]), ([short, exact], [short]),
                     (MISSING, [short, exact])):
            with self.subTest(fact=a, source=b):
                claim, disposition = self.kettle(fact_scope=a, source_scope=b)
                self.assertEqual(claim["status"], "met")
                self.assertEqual(claim["supporting_fact_ids"], ["short-height"])
                self.assertEqual(claim["source_audit"][0]["source_id"], "short-height-source")
                self.assertEqual(disposition, "eligible_for_research")

    def test_printer_chat_malformed_scope_keeps_price_and_audit(self):
        for field in ("fact", "source"):
            for scope in ("review-model-plus", None, [], ["review-model", 3],
                          ["review-model-plus"]):
                with self.subTest(field=field, scope=scope):
                    state, bundle = CHAT["cases"]()["positive_control"]
                    row = bundle["facts"][1] if field == "fact" else next(
                        s for s in bundle["sources"] if s["id"] == bundle["facts"][1]["source_id"])
                    row["scope_models"] = scope
                    before = deepcopy(bundle)
                    result = CHAT["replay"](state, bundle)
                    self.assertEqual(bundle, before)
                    self.assertEqual(CHAT["status"](result, "wx"), "unknown")
                    self.assertEqual(CHAT["status"](result, "ceiling"), "met")
                    self.assertTrue(all(a["research_status"] == "pending_evidence"
                                        for a in result["assessments"]))
                    self.assertTrue(all(v is False for key in ("chat_flags", "public_flags")
                                        for v in result[key].values()))

    def test_invalid_fact_does_not_poison_other_fact_for_same_condition(self):
        state, bundle = CHAT["cases"]()["positive_control"]
        bad = dict(bundle["facts"][1], id="foreign-negative", value=False,
                   scope_models="review-model-plus")
        bundle["facts"].append(bad)
        result = CHAT["replay"](state, bundle)
        claim = next(c for c in result["claims"] if c["requirement_id"] == "wx")
        self.assertEqual(claim["status"], "met")
        self.assertEqual(claim["supporting_fact_ids"], ["wechat-support"])
        self.assertEqual(result["assessments"][0]["research_status"], "eligible_for_research")


if __name__ == "__main__":
    unittest.main()
