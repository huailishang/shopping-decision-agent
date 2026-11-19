"""P0.9：商品身份归属、原始证据回放与过期降级专项回归。"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from shopping_decision.dialogue_flow import compare_dialogue, new_dialogue, apply_turn
from shopping_decision.p0_7_official_details import load_reviewed_local_replay, parse_detail
from shopping_decision.product_compare import compare_products

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 10, 13, 55, tzinfo=timezone.utc)


def detail_html(text: str) -> bytes:
    return (
        "<html><body><h1>HL-10W HL-10W 黑白激光打印机</h1>"
        + text
        + "<footer>服务支持</footer></body></html>"
    ).encode("utf-8")


class P09TrustTests(unittest.TestCase):
    def test_postfix_other_model_qualifier_is_not_attributed(self):
        cases = (
            ("auto_duplex", "标配A4自动双面打印（仅限HL-B2188DW），HL-10W为手动双面。"),
            ("wireless", "支持无线网络连接（仅适用于HL-B2188DW），本型号仅USB连接。"),
            ("pay_per_page_consumables", "按页付费、购买打印页数（仅适用于HL-B2188DW），HL-10W使用普通耗材。"),
        )
        for feature, text in cases:
            with self.subTest(feature=feature):
                parsed = parse_detail("HL-10W", detail_html(text), observed_at=NOW)
                self.assertNotIn(feature, parsed["facts"])

    def test_css_class_and_id_hidden_text_are_not_evidence(self):
        html = (
            "<html><head><style>.hidden-feature { display: none; }"
            "#hidden-id { visibility: hidden; }</style></head><body>"
            "<h1>HL-10W HL-10W 黑白激光打印机</h1>"
            "<div class='hidden-feature'>支持无线网络连接</div>"
            "<span id='hidden-id'>微信小程序直连，支持远程打印</span>"
            "本型号仅支持USB。<footer>服务支持</footer></body></html>"
        ).encode("utf-8")
        parsed = parse_detail("HL-10W", html, observed_at=NOW)
        self.assertNotIn("wireless", parsed["facts"])
        self.assertNotIn("wechat_miniprogram", parsed["facts"])

    def test_visible_positive_text_still_survives_conservative_filter(self):
        parsed = parse_detail(
            "HL-10W",
            detail_html("本型号支持无线网络连接。微信小程序直连，支持远程打印。"),
            observed_at=NOW,
        )
        self.assertTrue(parsed["facts"]["wireless"]["value"])
        self.assertTrue(parsed["facts"]["wechat_miniprogram"]["value"])

    def test_normal_replay_uses_p08_raw_html_with_matching_hashes(self):
        catalog = load_reviewed_local_replay()
        self.assertEqual(
            catalog["local_evidence_manifest"],
            "reports/p0_8_refetched_official_sources_20261109.json",
        )
        evidenced = [p for p in catalog["products"] if p.get("manufacturer_detail_evidence")]
        self.assertEqual(len(evidenced), 3)
        archive = ROOT / "data/raw/p0_8_official_details"
        for item in evidenced:
            digest = item["manufacturer_detail_evidence"]["response_sha256"]
            raw = archive / (digest + ".html")
            self.assertTrue(raw.is_file())
            self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(), digest)

    def test_stale_detail_downgrades_current_facts_to_unknown(self):
        catalog = load_reviewed_local_replay()
        row = next(p for p in catalog["products"] if p["model_id"] == "HL-10W")
        original_fact = deepcopy(row["facts"]["wireless"])
        row["manufacturer_detail_evidence"]["observed_at"] = "2020-01-01T00:00:00+00:00"
        # 目录日期保持新鲜，证明刷新目录日期不能刷新逐型号详情证据。
        catalog["recorded_on"] = NOW.date().isoformat()
        result = compare_products(
            catalog,
            category="printer",
            required={"wireless": True},
            today=NOW.date(),
        )
        stale = next(p for p in result["candidates"] if p["model_id"] == "HL-10W")
        self.assertEqual(stale["required_met"], [])
        self.assertEqual(stale["required_unknown"], ["wireless"])
        self.assertEqual(stale["status"], "needs_verification")
        self.assertTrue(stale["manufacturer_detail_is_stale"])
        self.assertEqual(row["facts"]["wireless"], original_fact)

    def test_missing_raw_detail_is_rejected(self):
        manifest = json.loads(
            (ROOT / "reports/p0_8_refetched_official_sources_20261109.json").read_text(encoding="utf-8")
        )
        digest = manifest["models"][0]["response_sha256"]
        original_is_file = Path.is_file

        def missing_raw(path: Path):
            if path.name == digest + ".html":
                return False
            return original_is_file(path)

        with patch.object(Path, "is_file", missing_raw):
            with self.assertRaisesRegex(FileNotFoundError, "p0_8_raw_detail_missing"):
                load_reviewed_local_replay()

    def test_hash_mismatch_is_rejected_and_dialogue_explicitly_degrades(self):
        manifest = json.loads(
            (ROOT / "reports/p0_8_refetched_official_sources_20261109.json").read_text(encoding="utf-8")
        )
        digest = manifest["models"][0]["response_sha256"]
        original_read_bytes = Path.read_bytes

        def tampered_read(path: Path):
            raw = original_read_bytes(path)
            if path.name == digest + ".html":
                return raw + b"tampered"
            return raw

        with patch.object(Path, "read_bytes", tampered_read):
            with self.assertRaisesRegex(ValueError, "p0_8_raw_detail_hash_mismatch"):
                load_reviewed_local_replay()

        state = apply_turn(
            new_dialogue(),
            {
                "category": "printer",
                "usage": "家用黑白打印",
                "needs_color": False,
                "accepts_outsourced_color": True,
                "monthly_pages_range": [0, 50],
                "budget_max_cny": 1000,
                "wechat_required": True,
                "wechat_workflow": "miniprogram",
                "requires_wireless": True,
            },
            raw_text="P0.9合成回归：黑白无线微信打印",
        )
        with patch(
            "shopping_decision.dialogue_flow.load_reviewed_local_replay",
            side_effect=ValueError("p0_8_raw_detail_hash_mismatch"),
        ):
            result = compare_dialogue(state)
        self.assertEqual(result["source_mode"], "older_manufacturer_directory_snapshot_only")
        self.assertIn("完整性校验失败", result["source_warning"])
        self.assertFalse(result["purchase_recommendation_approved"])
        self.assertFalse(result["transactions_enabled"])


if __name__ == "__main__":
    unittest.main()
