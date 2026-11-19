"""P0.9-B evaluator S1-S4 repair guards: independent expectations, synthetic-only."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from shopping_decision.sale_configuration_evidence import assess_sale_evidence_report
from tests.test_p0_9_b_evidence import sample, report, MODELS


class P09BS1S4Regressions(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.base = sample(self.now)

    def gate(self, *rows, at=None):
        return assess_sale_evidence_report(report(*rows), now=at or self.now, known_models=MODELS)

    def test_s1_bad_row_types_before_and_after_good(self):
        bad_values = [
            ("platform_list", {"platform": []}),
            ("platform_dict", {"platform": {}}),
            ("uses_nested_dict", {"permitted_uses": ["local_parse", {"user_display": True}, "minimal_audit"]}),
            ("uses_nested_list", {"permitted_uses": ["local_parse", ["user_display"], "minimal_audit"]}),
        ]
        for label, edits in bad_values:
            for order in (0, 1):
                with self.subTest(label=label, order=order):
                    bad = deepcopy(self.base)
                    bad["source_id"] = "synthetic:separate_bad"
                    bad.update(edits)
                    rows = [bad, self.base] if order == 0 else [self.base, bad]
                    out = self.gate(*rows)
                    self.assertEqual((out["accepted_rows"], out["rejected_count"]), (1, 1))
                    self.assertEqual(out["configuration_count"], 1)
                    self.assertEqual(out["configurations"][0]["status"], "synthetic_field_binding_test_only")

    def test_s2_revocation_and_use_loss_are_order_invariant(self):
        for edits in ({"review_status": "withdrawn"}, {"permitted_uses": ["local_parse"]}):
            for reverse in (False, True):
                with self.subTest(edits=edits, reverse=reverse):
                    invalid = deepcopy(self.base)
                    invalid.update(edits)
                    rows = [invalid, self.base] if reverse else [self.base, invalid]
                    out = self.gate(*rows)
                    self.assertEqual(out["accepted_rows"], 1)
                    self.assertEqual(out["rejected_count"], 1)
                    self.assertTrue(all(x["status"] != "synthetic_field_binding_test_only"
                                        for x in out["configurations"]))

    def test_s2_other_source_remains_valid_and_can_restore_after_review(self):
        other = deepcopy(self.base)
        other["source_id"] = "synthetic:new_review_event"
        other["source_ref"] = "synthetic:new_platform_panel"
        other["source_sha256"] = "b" * 64
        other["observed_at"] = (self.now - timedelta(hours=3)).isoformat()
        withdrawn = deepcopy(self.base)
        withdrawn["review_status"] = "withdrawn"
        out = self.gate(self.base, other, withdrawn)
        statuses = {x["source_id"]: x["status"] for x in out["configurations"]}
        self.assertEqual(statuses["synthetic:case001"], "synthetic_same_source_invalidated_requires_review")
        self.assertEqual(statuses["synthetic:new_review_event"], "synthetic_field_binding_test_only")
        self.assertEqual(out["real_identity_verified_count"], 0)

    def test_s2_timezone_equivalent_withdrawal_matches_same_event(self):
        withdrawn = deepcopy(self.base)
        withdrawn["review_status"] = "withdrawn"
        withdrawn["observed_at"] = datetime.fromisoformat(
            self.base["observed_at"]).astimezone(timezone(timedelta(hours=5, minutes=45))).isoformat()
        out = self.gate(withdrawn, self.base)
        self.assertEqual(out["configuration_count"], 1)
        self.assertEqual(out["configurations"][0]["status"], "synthetic_same_source_invalidated_requires_review")

    def test_s2_malformed_untrusted_claim_does_not_revoke_source(self):
        bad = deepcopy(self.base)
        bad["permitted_uses"] = ["local_parse", ["invalid"], "minimal_audit"]
        out = self.gate(self.base, bad)
        self.assertEqual(out["rejected_count"], 1)
        self.assertEqual(out["configurations"][0]["status"], "synthetic_field_binding_test_only")

    def test_s4_anchor_provisional_vs_auditable_sku(self):
        provisional = self.gate(self.base)
        row = provisional["configurations"][0]
        self.assertFalse(row["field_binding_complete"])
        self.assertEqual(row["sku_anchor_status"], "missing_selected_sku_anchor_unverified")
        anchored = deepcopy(self.base)
        anchored["field_anchors"]["selected_sku_id"] = "synthetic:selected_sku_panel"
        confirmed = self.gate(anchored)["configurations"][0]
        self.assertTrue(confirmed["field_binding_complete"])
        self.assertEqual(confirmed["field_anchors"]["selected_sku_id"], "synthetic:selected_sku_panel")
        self.assertEqual(confirmed["source_ref"], anchored["source_ref"])
        self.assertFalse(confirmed["identity_verified"])
        anchored["field_anchors"]["selected_sku_id"] = "https://invalid.example"
        rejected = self.gate(anchored)
        self.assertEqual(rejected["rejected"][0]["reason"], "platform_field_anchor_missing")

    def test_s3_expiry_equivalent_timezone_before_and_after(self):
        row = deepcopy(self.base)
        row["review_valid_until"] = (self.now + timedelta(seconds=1)).isoformat()
        accepted = self.gate(row, at=self.now)
        self.assertEqual(accepted["accepted_rows"], 1)
        after = self.gate(row, at=self.now + timedelta(seconds=2))
        self.assertEqual(after["accepted_rows"], 0)
        self.assertEqual(after["rejected"][0]["reason"], "review_expired")

    def test_cli_mixed_bad_types_and_withdrawn_binding_not_compared(self):
        valid = deepcopy(self.base)
        withdrawn = deepcopy(valid)
        withdrawn["review_status"] = "withdrawn"
        bad = deepcopy(valid)
        bad["source_id"] = "synthetic:bad"
        bad["platform"] = {}
        turns = [{"text": "合成打印机", "answers": {
            "category": "printer", "usage": "home",
            "needs_color": False, "requires_wireless": True}}]
        with TemporaryDirectory() as folder:
            p = Path(folder) / "s1_s2.json"
            p.write_text(json.dumps(report(valid, bad, withdrawn), ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "shopping_decision.dialogue_flow",
                 "--sale-evidence-report", str(p)],
                input="".join(json.dumps(t, ensure_ascii=False) + "\n" for t in turns),
                text=True, capture_output=True, encoding="utf-8", timeout=30,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = [json.loads(s) for s in result.stdout.splitlines()]
        sale = output[1]["sale_configuration_evidence"]
        self.assertEqual(sale["rejected_count"], 2)
        self.assertEqual(sale["accepted_rows"], 1)
        self.assertTrue(all(c["status"] == "synthetic_same_source_invalidated_requires_review"
                            and c["manufacturer_model_fact_status"] == "manufacturer_facts_not_compared"
                            and not c["required_met"]
                            for c in sale["configurations"]))
        self.assertFalse(sale["purchase_recommendation_approved"])


    def test_s2_rejected_malformed_state_event_cannot_invalidate_valid_row(self):
        valid = deepcopy(self.base)
        valid["field_anchors"]["selected_sku_id"] = "synthetic:sku_panel"
        variations = [
            ("forbidden_approval", {"review_status": "withdrawn", "identity_verified": True}),
            ("forbidden_price", {"permitted_uses": [], "price": 499}),
            ("withdrawal_with_nested_uses", {"review_status": "withdrawn",
                                            "permitted_uses": ["local_parse", {"bad": True}]}),
            ("withdrawal_with_unknown_use", {"review_status": "withdrawn",
                                             "permitted_uses": ["local_parse", "unknown_use"]}),
            ("withdrawal_with_duplicate_uses", {"review_status": "withdrawn",
                                               "permitted_uses": ["local_parse", "local_parse"]}),
            ("withdrawal_with_bad_anchor", {"review_status": "withdrawn",
                                           "field_anchors": {**valid["field_anchors"],
                                                             "selected_sku_id": {"forged": True}}}),
            ("withdrawal_with_other_model", {"review_status": "withdrawn",
                                             "selected_model_id": "HL-B2158W"}),
            ("withdrawal_with_bad_expiry", {"review_status": "withdrawn",
                                           "review_valid_until": []}),
        ]
        for label, edits in variations:
            for reverse in (False, True):
                with self.subTest(label=label, reverse=reverse):
                    bad = deepcopy(valid)
                    bad.update(edits)
                    out = self.gate(*( [bad, valid] if reverse else [valid, bad] ))
                    self.assertEqual((out["accepted_rows"], out["rejected_count"]), (1, 1))
                    self.assertEqual(out["configuration_count"], 1)
                    active = out["configurations"][0]
                    self.assertEqual(active["status"], "synthetic_field_binding_test_only")
                    self.assertTrue(active["field_binding_complete"])
                    self.assertFalse(out["purchase_recommendation_approved"])
                    self.assertFalse(out["transactions_enabled"])

    def test_s2_valid_state_events_still_revoke_but_other_source_isolated(self):
        valid = deepcopy(self.base)
        other = deepcopy(valid)
        other.update(source_id="synthetic:independent", source_ref="synthetic:independent_panel",
                     source_sha256="b" * 64)
        for edits in ({"review_status": "withdrawn"}, {"permitted_uses": ["local_parse"]},
                      {"permitted_uses": []}):
            for reverse in (False, True):
                with self.subTest(edits=edits, reverse=reverse):
                    event = deepcopy(valid)
                    event.update(edits)
                    rows = [event, valid, other] if reverse else [valid, other, event]
                    out = self.gate(*rows)
                    statuses = {x["source_id"]: x["status"] for x in out["configurations"]}
                    self.assertEqual(statuses[valid["source_id"]],
                                     "synthetic_same_source_invalidated_requires_review")
                    self.assertEqual(statuses[other["source_id"]],
                                     "synthetic_field_binding_test_only")
                    self.assertEqual((out["accepted_rows"], out["rejected_count"]), (2, 1))

    def test_s2_bad_withdrawal_has_no_effect_in_normal_cli(self):
        valid = deepcopy(self.base)
        valid["field_anchors"]["selected_sku_id"] = "synthetic:sku_panel"
        bad = deepcopy(valid)
        bad.update(review_status="withdrawn", identity_verified=True)
        turns = [{"text": "合成打印机", "answers": {
            "category": "printer", "usage": "home",
            "needs_color": False, "requires_wireless": True}}]
        with TemporaryDirectory() as folder:
            p = Path(folder) / "s2_bad_event.json"
            p.write_text(json.dumps(report(valid, bad), ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run([sys.executable, "-m", "shopping_decision.dialogue_flow",
                                   "--sale-evidence-report", str(p)],
                                  input="".join(json.dumps(t, ensure_ascii=False) + "\n" for t in turns),
                                  text=True, capture_output=True, encoding="utf-8", timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = [json.loads(s) for s in proc.stdout.splitlines()]
        sale = output[1]["sale_configuration_evidence"]
        self.assertEqual((sale["accepted_rows"], sale["rejected_count"]), (1, 1))
        self.assertTrue(any(c["status"] == "synthetic_field_binding_test_only"
                            for c in sale["configurations"]))
        self.assertFalse(sale["purchase_recommendation_approved"])
        self.assertFalse(sale["transactions_enabled"])


if __name__ == "__main__":
    unittest.main()
