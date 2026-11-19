"""P0.9-B: 至少18个独立人工期望样本 + 7轮正常入口，均为纯合成合同测试。"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from shopping_decision.sale_configuration_evidence import assess_sale_evidence_report

MODELS = {"HL-10W", "HL-B2188DW", "HL-B2158W", "M232dw", "M232dwc"}


def sample(now=None):
    now = now or datetime.now(timezone.utc)
    return {
        "source_id": "synthetic:case001",
        "platform": "JD", "platform_item_id": "12345678",
        "selected_sku_id": "12345679", "seller_id": "seller001",
        "selected_variant": "single_new_printer",
        "selected_model_id": "HL-10W",
        "title_models": ["HL-10W"], "spec_models": ["HL-10W"],
        "item_kind": "printer", "condition": "new",
        "source_ref": "synthetic:platform_panel",
        "source_sha256": "a" * 64,
        "observed_at": (now - timedelta(days=1)).isoformat(),
        "review_valid_until": (now + timedelta(days=5)).isoformat(),
        "review_status": "active",
        "field_anchors": {key: "synthetic:anchor_" + str(i) for i, key in enumerate((
            "platform_item_id", "seller_id", "selected_variant",
            "selected_model_id", "item_kind", "condition"))},
        "permitted_uses": ["local_parse", "user_display", "minimal_audit"],
    }


def report(*items, mode="synthetic_test"):
    return {
        "operation": "p0_9_b_sale_configuration_evidence",
        "source_mode": mode,
        "items": list(items),
    }


def change(row, **kwargs):
    altered = deepcopy(row)
    altered.update(kwargs)
    return altered


class P09BConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.base = sample(self.now)

    def assess(self, *rows):
        return assess_sale_evidence_report(report(*rows), now=self.now, known_models=MODELS)

    def test_hp_m232dw_and_m232dwc_are_distinct_exact_models(self):
        for model in ("M232dw", "M232dwc"):
            row = change(self.base, selected_model_id=model,
                         title_models=[model], spec_models=[model])
            result = self.assess(row)
            self.assertEqual(result["accepted_rows"], 1)
            self.assertEqual(result["configurations"][0]["selected_model_id"], model)
        mismatch = change(self.base, selected_model_id="M232dw",
                          title_models=["M232dwc"], spec_models=["M232dwc"])
        rejected = self.assess(mismatch)
        self.assertEqual(rejected["accepted_rows"], 0)
        self.assertEqual(rejected["rejected"][0]["reason"],
                         "title_spec_or_selected_model_conflict")

    def test_twenty_four_manual_expected_input_cases(self):
        b, now = self.base, self.now
        incomplete_anchor = deepcopy(b["field_anchors"])
        incomplete_anchor.pop("selected_model_id")
        cases = [
            ("base_synthetic", b, "accepted_synthetic"),
            ("wrong_platform", change(b, platform="PDD"), "platform_or_item_id_invalid"),
            ("bad_item_id", change(b, platform_item_id="not_an_id"), "platform_or_item_id_invalid"),
            ("missing_sku", change(b, selected_sku_id=None), "selected_sku_id_missing"),
            ("bad_sku_id", change(b, selected_sku_id="abc"), "sku_id_invalid"),
            ("multi_model_title", change(b, title_models=["HL-10W", "HL-B2158W"]), "title_spec_or_selected_model_conflict"),
            ("mismatching_spec", change(b, spec_models=["HL-B2158W"]), "title_spec_or_selected_model_conflict"),
            ("no_spec_evidence", change(b, spec_models=[]), "title_spec_or_selected_model_conflict"),
            ("toner_not_host", change(b, item_kind="toner"), "not_single_new_printer"),
            ("used_listing", change(b, condition="used"), "not_single_new_printer"),
            ("bundle_listing", change(b, selected_variant="bundle"), "not_single_new_printer"),
            ("missing_seller", change(b, seller_id=""), "source_or_seller_invalid"),
            ("bad_hash", change(b, source_sha256="a" * 10), "source_hash_invalid"),
            ("future_observation", change(b, observed_at=(now + timedelta(days=1)).isoformat()), "source_observation_invalid"),
            ("naive_observation", change(b, observed_at=now.replace(tzinfo=None).isoformat()), "source_observation_invalid"),
            ("expired_review", change(b, review_valid_until=(now - timedelta(seconds=1)).isoformat()), "review_expired"),
            ("withdrawn", change(b, review_status="withdrawn"), "review_withdrawn_or_unconfirmed"),
            ("missing_uses", change(b, permitted_uses=[]), "required_local_uses_not_evidenced"),
            ("missing_model_anchor", change(b, field_anchors=incomplete_anchor), "platform_field_anchor_missing"),
            ("forged_approval", change(b, identity_verified=True), "unrecognized_or_forbidden_fields"),
            ("forged_price", change(b, price=399), "unrecognized_or_forbidden_fields"),
            ("url_smuggled", change(b, source_ref="https://untrusted.example"), "source_or_seller_invalid"),
            ("unreviewed_model", change(b, selected_model_id="HL-Z999W", title_models=["HL-Z999W"], spec_models=["HL-Z999W"]), "manufacturer_model_not_reviewed"),
            ("missing_source_ref", change(b, source_ref=""), "source_or_seller_invalid"),
        ]
        self.assertGreaterEqual(len(cases), 18)
        for name, row, expected in cases:
            with self.subTest(name=name):
                output = self.assess(row)
                self.assertEqual(output["input_rows"], 1)
                if expected == "accepted_synthetic":
                    self.assertEqual(output["accepted_rows"], 1)
                    self.assertEqual(output["configuration_count"], 1)
                    self.assertFalse(output["configurations"][0]["identity_verified"])
                else:
                    self.assertEqual(output["accepted_rows"], 0)
                    self.assertEqual(output["rejected_count"], 1)
                    self.assertEqual(output["rejected"][0]["reason"], expected)
                self.assertEqual(output["real_identity_verified_count"], 0)
                self.assertFalse(output["purchase_recommendation_approved"])
                self.assertFalse(output["transactions_enabled"])

    def test_bad_row_does_not_lose_good_row(self):
        mixed = self.assess(self.base, change(self.base, price=199))
        self.assertEqual(mixed["input_rows"], 2)
        self.assertEqual(mixed["accepted_rows"], 1)
        self.assertEqual(mixed["rejected_count"], 1)
        self.assertEqual(mixed["configuration_count"], 1)

    def test_platform_item_sku_seller_are_separate_keys(self):
        b = self.base
        result = self.assess(
            b,
            change(b, source_id="synthetic:second", platform="TAOBAO"),
            change(b, source_id="synthetic:third", selected_sku_id="12345680"),
            change(b, source_id="synthetic:fourth", seller_id="seller002"),
        )
        self.assertEqual(result["configuration_count"], 4)
        self.assertEqual(result["accepted_rows"], 4)
        self.assertEqual(result["real_identity_verified_count"], 0)

    def test_same_key_conflicting_model_is_not_silently_merged(self):
        other = change(self.base, source_id="synthetic:second", source_sha256="b" * 64,
                       selected_model_id="HL-B2158W",
                       title_models=["HL-B2158W"], spec_models=["HL-B2158W"])
        result = self.assess(self.base, other)
        self.assertEqual(result["configuration_count"], 2)
        self.assertTrue(all(x["status"] == "synthetic_source_conflict_requires_review"
                            for x in result["configurations"]))
        self.assertEqual(result["real_identity_verified_count"], 0)

    def test_same_hash_changed_observation_event_requires_review(self):
        other = change(
            self.base, source_id="synthetic:second",
            observed_at=(self.now - timedelta(hours=12)).isoformat(),
        )
        result = self.assess(self.base, other)
        self.assertEqual(result["configuration_count"], 2)
        self.assertTrue(all(x["status"] == "synthetic_source_conflict_requires_review"
                            for x in result["configurations"]))

    def test_same_key_same_source_merge_only_at_configuration_grain(self):
        other = change(self.base, source_id="synthetic:second")
        result = self.assess(self.base, other)
        self.assertEqual(result["configuration_count"], 1)
        self.assertEqual(result["configurations"][0]["source_count"], 2)
        self.assertFalse(result["configurations"][0]["identity_verified"])

    def test_real_mode_cannot_be_turned_on_by_input(self):
        with self.assertRaisesRegex(ValueError, "not_authorized"):
            assess_sale_evidence_report(report(self.base, mode="real_response"),
                                        now=self.now, known_models=MODELS)

    def test_normal_cli_seven_turns_with_synthetic_binding(self):
        turns = [
            {"text": "合成原案", "answers": {"category": "printer", "usage": "家用",
             "needs_color": False, "accepts_outsourced_color": True,
             "monthly_pages_range": [0,50], "budget_max_cny": 1000,
             "wechat_required": True, "requires_wireless": True}},
            {"text": "改要求双面", "answers": {"requires_auto_duplex": True}},
            {"text": "改要求彩色", "answers": {"needs_color": True}},
            {"text": "不再要求微信", "answers": {"wechat_required": False}},
            {"text": "预算降低", "answers": {"budget_max_cny": 800}},
            {"text": "冲突条件", "answers": {"needs_color": False, "requirements": ["必须彩色打印"]}},
            {"text": "不确定，撤回要求", "answers": {"requirements": None, "requires_auto_duplex": None}},
        ]
        with TemporaryDirectory() as folder:
            path = Path(folder) / "evidence.json"
            path.write_text(json.dumps(report(self.base), ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run([sys.executable, "-m", "shopping_decision.dialogue_flow",
                                   "--sale-evidence-report", str(path)],
                                  input="".join(json.dumps(t, ensure_ascii=False) + "\n" for t in turns),
                                  text=True, capture_output=True, encoding="utf-8", timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = [json.loads(x) for x in proc.stdout.splitlines()]
        self.assertEqual(len(rows), 8)
        self.assertEqual([x["version"] for x in rows[1:]], list(range(1, 8)))
        for x in rows[1:]:
            evidence = x["sale_configuration_evidence"]
            self.assertEqual(evidence["source_mode"], "synthetic_test")
            self.assertEqual(evidence["real_identity_verified_count"], 0)
            self.assertFalse(evidence["purchase_recommendation_approved"])
            self.assertFalse(evidence["transactions_enabled"])
            self.assertLessEqual(evidence["displayed_configuration_count"], 3)
            self.assertTrue(x["history"]["old_conclusions_invalidated"])
        self.assertEqual(rows[6]["comparison"]["status"], "condition_conflict")
        self.assertNotEqual(rows[7]["comparison"]["status"], "condition_conflict")
        self.assertIn("auto_duplex", rows[2]["sale_configuration_evidence"]["configurations"][0]["required_unknown"])
        self.assertNotIn("auto_duplex", rows[7]["sale_configuration_evidence"]["configurations"][0]["required_unknown"])


if __name__ == "__main__":
    unittest.main()
