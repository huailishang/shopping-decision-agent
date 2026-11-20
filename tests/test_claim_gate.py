"""Adversarial, positive and cross-category coverage for the shared publication boundary."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from test_model_comparison import bundle, response
from shopping_decision.claim_gate import (normalize_evidence_fact, publish_checked_comparison,
                                          validate_research_claims)
from shopping_decision.evidence_comparison import rule_comparison, validate_model_result

ROOT = Path(__file__).resolve().parents[1]
MATRIX = (ROOT / "handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118"
          / "post_review/PRINTER-TRUSTED-DECISION-20261119/evidence/decision_matrix.json")


def public_rows(data, model=None, origin="rule"):
    return publish_checked_comparison(data, model, origin=origin)


class ClaimGateTests(unittest.TestCase):
    def test_numeric_rule_correct_but_opposite_summary_and_explanation(self):
        data = bundle()
        data["facts"][0]["value"] = 1300
        malicious = response("failed")
        malicious["summary"] = "预算1000，现价1300，比预算低，立即购买"
        malicious["assessments"][0]["comparisons"][0]["explanation"] = "1300小于1000，快去买"
        self.assertEqual(rule_comparison(data)["assessments"][0]["comparisons"][0]["status"], "failed")
        self.assertFalse(validate_model_result(data, malicious)["semantic_entailment_verified"])
        public = public_rows(data, malicious, "model")
        self.assertEqual(public["claims"][0]["status"], "failed")
        self.assertEqual(public["assessments"][0]["research_status"], "excluded_for_research")
        self.assertFalse(public["purchase_recommendation_approved"])
        self.assertNotIn("立即购买", json.dumps(public, ensure_ascii=False))
        self.assertNotIn("1300小于1000", json.dumps(public, ensure_ascii=False))
        self.assertNotIn("快去买", json.dumps(public, ensure_ascii=False))

    def test_tradeoff_cites_other_candidate_or_dimension(self):
        data = bundle()
        data["candidates"].append({"id": "b"})
        other = deepcopy(data["facts"][0])
        other.update(id="other", candidate_id="b")
        data["facts"].append(other)
        bad = response()
        b = deepcopy(bad["assessments"][0])
        b["candidate_id"] = "b"
        b["comparisons"][0]["fact_ids"] = ["other"]
        bad["assessments"].append(b)
        bad["assessments"][0]["tradeoffs"] = [{"statement": "无效引用", "fact_ids": ["other"],
                                              "conditions": []}]
        # Existing structural validator is NOT the public gate.
        validate_model_result(data, bad)
        with self.assertRaisesRegex(ValueError, "unbound_public_tradeoff"):
            public_rows(data, bad, "model")
        data = bundle()
        unused = deepcopy(data["facts"][0])
        unused.update(id="unrelated", dimension="other_dimension")
        data["facts"].append(unused)
        bad = response()
        bad["assessments"][0]["tradeoffs"] = [{"statement": "另一维度", "fact_ids": ["unrelated"],
                                              "conditions": []}]
        validate_model_result(data, bad)
        with self.assertRaisesRegex(ValueError, "unbound_public_tradeoff"):
            public_rows(data, bad, "model")

    def test_action_kind_research_but_description_says_buy_now(self):
        data = bundle()
        bad = response()
        bad["next_actions"] = [{"kind": "research", "description": "立刻付款下单"}]
        public = public_rows(data, bad, "model")
        self.assertNotIn("立刻付款下单", json.dumps(public, ensure_ascii=False))
        self.assertNotIn("research", [a["kind"] for a in public["next_actions"]])
        self.assertTrue(all(a["kind"] in ("verify_price", "research", "clarify")
                            for a in public["next_actions"]))
        self.assertFalse(public["transactions_enabled"])

    def test_listing_sku_not_a_regionally_valid_price_or_current_stock(self):
        data = bundle()
        data["region"] = "Henan county"
        data["sources"][0].update(url="https://example.org/item",
                                  type="official_storefront_html",
                                  observed_at="2026-11-18T06:00:00+00:00",
                                  scope_models=["a"], scope_region="Henan county",
                                  valid_until="2026-11-18")
        data["facts"][0].update(kind="catalog_price", value=900)
        public = public_rows(data)
        self.assertEqual(public["claims"][0]["status"], "unknown")
        self.assertIn("verify_price", [a["kind"] for a in public["next_actions"]])
        data["facts"][0]["kind"] = "live_quote"
        # A timestamp and an official-looking page are insufficient.
        self.assertEqual(public_rows(data)["claims"][0]["status"], "unknown")
        data["sources"][0].update(quote_region="Henan county", quote_sku="SKU-A",
                                  quote_merchant="synthetic merchant")
        result = public_rows(data)
        self.assertEqual(result["claims"][0]["status"], "met")
        self.assertFalse(result["live_price_verified"])
        self.assertTrue(result["claims"][0]["verification"]["unverified_external_fact"])
        data["sources"][0]["quote_region"] = "other county"
        self.assertEqual(public_rows(data)["claims"][0]["status"], "unknown")

    def test_source_is_index_only_or_series_only_for_exact_model(self):
        data = bundle()
        data["requirements"][0].update(dimension="feature", unit="bool",
                                       op="eq", value=True)
        data["facts"][0].update(dimension="feature", unit="bool", value=True,
                                kind="manual_research")
        data["sources"][0].update(url="https://example.org/feature",
                                  observed_at="2026-11-18T03:00:00+00:00",
                                  scope_models=["a"])
        for name in ("official_search_index_only", "manufacturer_series_pdf",
                     "marketplace_category_index_only"):
            data["sources"][0]["type"] = name
            self.assertEqual(public_rows(data)["claims"][0]["status"], "unknown")
        data["sources"][0]["type"] = "official_exact_model_document"
        data["sources"][0]["scope_models"] = ["a-variant"]
        self.assertEqual(public_rows(data)["claims"][0]["status"], "unknown")
        data["sources"][0]["scope_models"] = ["a"]
        self.assertEqual(public_rows(data)["claims"][0]["status"], "met")
        self.assertTrue(public_rows(data)["claims"][0]["verification"]["unverified_external_fact"])

    def test_input_change_or_source_revocation_removes_prior_verified_claim(self):
        data = bundle()
        before = public_rows(data)
        self.assertEqual(before["claims"][0]["status"], "met")
        data["requirements"][0]["value"] = 800
        after = public_rows(data)
        self.assertEqual(after["claims"][0]["status"], "failed")
        self.assertNotEqual(before["claims"][0]["claim_id"], after["claims"][0]["claim_id"])
        data["sources"][0]["revoked"] = True
        revoked = public_rows(data)
        self.assertEqual(revoked["claims"][0]["status"], "unknown")
        self.assertEqual(revoked["claims"][0]["supporting_fact_ids"], [])

    def test_missing_or_conflicting_fact_remains_unknown_or_conflict(self):
        data = bundle()
        data["facts"] = []
        self.assertEqual(public_rows(data)["claims"][0]["status"], "unknown")
        data = bundle()
        other = deepcopy(data["facts"][0])
        other.update(id="f2", value=1200)
        data["facts"].append(other)
        self.assertEqual(public_rows(data)["claims"][0]["status"], "conflict")
        data["sources"][0]["revoked"] = True
        self.assertEqual(public_rows(data)["claims"][0]["status"], "unknown")

    def test_generic_second_nonprinter_category_same_gate(self):
        data = bundle()
        data["category"] = "synthetic_air_purifier"
        data["requirements"][0].update(id="air_flow", dimension="air_flow", unit="m3/h",
                                       op="gte", value=300)
        data["facts"][0].update(dimension="air_flow", unit="m3/h", value=320)
        passed = public_rows(data)
        self.assertEqual(passed["claims"][0]["status"], "met")
        data["facts"][0]["value"] = 250
        self.assertEqual(public_rows(data)["claims"][0]["status"], "failed")
        data["facts"][0]["value"] = False
        self.assertEqual(public_rows(data)["claims"][0]["status"], "unknown")

    def test_typed_evidence_fact_and_computed_expression(self):
        data = bundle()
        evidence = normalize_evidence_fact(data['facts'][0], data['sources'][0],
                                           data, data['requirements'][0])
        for key in ('fact_id', 'source_id', 'candidate_id', 'dimension', 'value',
                    'unit', 'scope', 'observed_at', 'valid_until', 'grade', 'limitations'):
            self.assertIn(key, evidence)
        self.assertTrue(evidence['admitted'])
        self.assertEqual(public_rows(data)['claims'][0]['rule_expression'], '900 ≤ 1000')
        data['facts'][0]['value'] = 1300
        public = public_rows(data)
        self.assertEqual(public['claims'][0]['rule_expression'], '1300 ≤ 1000')
        self.assertIn('1300 ≤ 1000', public['assessments'][0]['comparisons'][0]['text'])

    def test_valid_verified_claim_and_public_text_positive(self):
        data = bundle()
        public = public_rows(data)
        claim = public["claims"][0]
        self.assertEqual(claim["status"], "met")
        self.assertEqual(claim["supporting_fact_ids"], ["f"])
        self.assertTrue(claim["verification"]["entailed_by_rule"])
        self.assertIn("研究层面满足", public["assessments"][0]["comparisons"][0]["text"])
        self.assertNotIn("合成900低于1000", json.dumps(public, ensure_ascii=False))
        self.assertFalse(public["purchase_recommendation_approved"])
        self.assertFalse(public["live_price_verified"])

    def test_historical_manual_matrix_is_downgraded_not_relabelled_as_verified(self):
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        public = validate_research_claims(matrix)
        self.assertEqual(public["origin"], "manual")
        self.assertGreater(public["manual_claims_downgraded"], 0)
        self.assertTrue(all(c["status"] == "unknown" for c in public["claims"]))
        self.assertFalse(public["manual_decision_gain_accepted"])
        self.assertNotIn("MEASURABLE_NEXT_ACTION", json.dumps(public, ensure_ascii=False))
        self.assertFalse(public["purchase_recommendation_approved"])

    def test_cli_actual_verified_display_replay(self):
        data = bundle()
        bad = response()
        bad["summary"] = "直接支付"
        bad["assessments"][0]["comparisons"][0]["explanation"] = "直接支付"
        with TemporaryDirectory() as temp:
            base = Path(temp)
            src = base / "input.json"
            out = base / "public.json"
            src.write_text(json.dumps({"bundle": data, "model_result": bad}, ensure_ascii=False),
                           encoding="utf-8")
            cmd = [sys.executable, "-X", "utf8", "scripts/verify_claim_publication.py",
                   "--input", str(src), "--out", str(out)]
            run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            shown = out.read_text(encoding="utf-8")
            self.assertNotIn("直接支付", shown)
            self.assertIn("研究层面满足", shown)
            cmd = [sys.executable, "-m", "shopping_decision.model_comparison",
                   "--bundle", str(base / "typed.json"), "--verified-report"]
            (base / "typed.json").write_text(json.dumps(data), encoding="utf-8")
            run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["publication_schema"], "verified-claims/v1")


if __name__ == "__main__":
    unittest.main()
