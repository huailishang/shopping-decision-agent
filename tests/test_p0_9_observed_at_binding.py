"""P0.9 2026-11-12 修复：固定历史证据的原观察时刻，防止仅改清单日期刷新有效期。"""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import hashlib
import json
import unittest

from shopping_decision.p0_7_official_details import (
    parse_detail, enrich_discovered_catalog, load_reviewed_local_replay,
)
from shopping_decision.product_compare import compare_products, load_official_catalog
from shopping_decision.public_catalog import (
    BROTHER_SNAPSHOT, _read_bounded_json, catalog_from_brother_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "reports/p0_8_refetched_official_sources_20261109.json"
# 固定于当时的 P0.8 取证记录；测试期待值不从被测准入实现派生。
OBSERVATIONS = {
    "HL-10W": "2026-11-09T14:01:03.133068+00:00",
    "HL-B2188DW": "2026-11-09T14:01:03.875727+00:00",
    "HL-B2158W": "2026-11-09T14:01:04.511646+00:00",
}


def view_for_replay():
    known = load_official_catalog()
    view = catalog_from_brother_snapshot(
        _read_bounded_json(BROTHER_SNAPSHOT), known_catalog=known,
        now=datetime.now(timezone.utc),
    )
    view["old_model_ids"] = [p["model_id"] for p in known["products"]]
    return view


class FrozenObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.rows = {row["model_id"]: row for row in cls.manifest["models"]}

    def _load_with_manifest(self, changed):
        original_read = Path.read_text

        def read(path, *args, **kwargs):
            if path == MANIFEST_PATH:
                return json.dumps(changed, ensure_ascii=False)
            return original_read(path, *args, **kwargs)

        with patch.object(Path, "read_text", read):
            return load_reviewed_local_replay()

    def _raw_detail(self, model):
        row = self.rows[model]
        body = (ROOT / "data/raw/p0_8_official_details"
                / (row["response_sha256"] + ".html")).read_bytes()
        self.assertEqual(hashlib.sha256(body).hexdigest(), row["response_sha256"])
        return parse_detail(model, body, observed_at=datetime.fromisoformat(OBSERVATIONS[model]))

    def test_original_three_observations_and_positive_fields_remain_valid(self):
        catalog = load_reviewed_local_replay()
        products = {p["model_id"]: p for p in catalog["products"]}
        for model, observed in OBSERVATIONS.items():
            with self.subTest(model=model):
                row = self.rows[model]
                self.assertEqual(row["observed_at"], observed)
                item = products[model]
                self.assertEqual(item["manufacturer_detail_evidence"]["observed_at"], observed)
                self.assertEqual(item["manufacturer_detail_evidence"]["response_sha256"], row["response_sha256"])
                self.assertTrue(item["facts"]["wireless"]["value"])
                self.assertEqual(item["manufacturer_detail_evidence"]["billing_model"], row["billing_model"])
                self.assertEqual(item["consumables"], self._raw_detail(model)["consumables"])
        self.assertTrue(products["HL-B2188DW"]["facts"]["auto_duplex"]["value"])
        self.assertTrue(products["HL-10W"]["facts"]["pay_per_page_consumables"]["value"])

    def test_manifest_before_after_change_rejected_for_all_three_models(self):
        for model, original in OBSERVATIONS.items():
            for delta in (timedelta(seconds=-1), timedelta(hours=1), timedelta(days=1)):
                with self.subTest(model=model, shift=str(delta)):
                    changed = deepcopy(self.manifest)
                    row = next(x for x in changed["models"] if x["model_id"] == model)
                    row["observed_at"] = (datetime.fromisoformat(original) + delta).isoformat()
                    with self.assertRaisesRegex(ValueError, "reviewed_detail_observation_time_mismatch"):
                        self._load_with_manifest(changed)

    def test_direct_reviewed_admission_before_after_change_rejected(self):
        for model, original in OBSERVATIONS.items():
            for delta in (timedelta(seconds=-1), timedelta(hours=1)):
                with self.subTest(model=model, shift=str(delta)):
                    detail = self._raw_detail(model)
                    detail["observed_at"] = (datetime.fromisoformat(original) + delta).isoformat()
                    with self.assertRaisesRegex(ValueError, "reviewed_detail_observation_time_mismatch"):
                        enrich_discovered_catalog(view_for_replay(), [detail], reviewed_local_replay=True)

    def test_equivalent_timezone_accepted_by_both_reviewed_paths(self):
        for model, original in OBSERVATIONS.items():
            instant = datetime.fromisoformat(original)
            for variant in (instant.astimezone(timezone(timedelta(hours=8))).isoformat(),
                            instant.astimezone(timezone(timedelta(hours=-5))).isoformat(),
                            instant.isoformat().replace("+00:00", "Z")):
                with self.subTest(model=model, timestamp=variant):
                    changed = deepcopy(self.manifest)
                    row = next(x for x in changed["models"] if x["model_id"] == model)
                    row["observed_at"] = variant
                    catalog = self._load_with_manifest(changed)
                    product = next(p for p in catalog["products"] if p["model_id"] == model)
                    self.assertTrue(product["facts"]["wireless"]["value"])
                    self.assertEqual(
                        datetime.fromisoformat(product["manufacturer_detail_evidence"]["observed_at"]),
                        datetime.fromisoformat(original),
                    )
                    detail = self._raw_detail(model)
                    detail["observed_at"] = variant
                    admitted = enrich_discovered_catalog(view_for_replay(), [detail], reviewed_local_replay=True)
                    matched = next(p for p in admitted["products"] if p["model_id"] == model)
                    self.assertTrue(matched["facts"]["wireless"]["value"])

    def test_future_manifest_time_rejected_without_reading_new_page(self):
        changed = deepcopy(self.manifest)
        changed["models"][0]["observed_at"] = "2099-01-01T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "reviewed_detail_observation_time_mismatch"):
            self._load_with_manifest(changed)

    def test_thirty_day_boundary_uses_original_time_not_refreshed_manifest(self):
        catalog = load_reviewed_local_replay()
        model = "HL-10W"
        for comparison_day, expected_age, expected_stale in (
            (date(2026, 12, 9), 30, False),
            (date(2026, 12, 10), 31, True),
        ):
            with self.subTest(day=comparison_day):
                comparison_input = deepcopy(catalog)
                comparison_input["recorded_on"] = comparison_day.isoformat()
                result = compare_products(comparison_input, category="printer",
                                          required={"wireless": True},
                                          budget_max_cny=None, today=comparison_day)
                row = next(p for p in result["candidates"] if p["model_id"] == model)
                self.assertEqual(row["manufacturer_detail_age_days"], expected_age)
                self.assertEqual(row["manufacturer_detail_is_stale"], expected_stale)
                self.assertEqual("wireless" in row["required_unknown"], expected_stale)
                self.assertEqual("wireless" in row["required_met"], not expected_stale)
                self.assertFalse(result["purchase_recommendation_approved"])
                self.assertFalse(result["transactions_enabled"])

    def test_same_original_unreviewed_stays_pending_not_auto_approved(self):
        detail = self._raw_detail("HL-10W")
        catalog = enrich_discovered_catalog(view_for_replay(), [detail], reviewed_local_replay=False)
        item = next(x for x in catalog["products"] if x["model_id"] == "HL-10W")
        self.assertEqual(item["manufacturer_claim_pending_review"]["status"],
                         "awaiting_per_field_review")
        self.assertNotIn("manufacturer_detail_evidence", item)


if __name__ == "__main__":
    unittest.main()
