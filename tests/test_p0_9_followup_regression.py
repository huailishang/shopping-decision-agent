"""P0.9 独立复核后新增回归：保留原14例与报告投毒，不修改评估者脚本。"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest

from shopping_decision.p0_7_official_details import parse_detail, load_reviewed_local_replay
from shopping_decision.discovery_pool import build_discovery_pool
from shopping_decision.haina_ingest import ingest_haina_product_search
from shopping_decision.product_compare import compare_products


HTML_CASES = (
    ("css_descendant_hidden", '<style>.wrap .secret{display:none}</style><div class="wrap"><div class="secret">支持无线网络连接</div></div>本型号仅USB。', None),
    ("css_attribute_hidden", '<style>[data-secret="yes"]{display:none}</style><div data-secret="yes">支持无线网络连接</div>本型号仅USB。', None),
    ("css_tag_hidden", '<style>aside{display:none}</style><aside>支持无线网络连接</aside>本型号仅USB。', None),
    ("css_compound_classes_hidden", '<style>.spec.secret{visibility:hidden}</style><div class="spec secret">支持无线网络连接</div>本型号仅USB。', None),
    ("other_family_dcp_scope", "DCP-B7658DW支持无线网络连接；HL-10W仅USB。", None),
    ("other_family_mfc_scope", "MFC-L5728DW支持无线网络连接。HL-10W仅USB。", None),
    ("paragraph_other_model_scope", "<section><h2>HL-B2188DW。</h2><p>支持无线网络连接。</p></section><section>HL-10W仅USB。</section>", None),
    ("positive_negative_separate_sentences", "本型号支持无线网络连接。更正：本型号不支持无线网络连接，仅USB。", None),
    ("positive_scope_following_sentence", "支持无线网络连接。以上功能仅适用于HL-B2188DW，HL-10W仅USB。", None),
    ("visible_opacity_half", '<span style="opacity:0.5">本型号支持无线网络连接。</span>', True),
    ("visible_comparison_with_other_model", "与HL-B2188DW相比，HL-10W同样支持无线网络连接。", True),
    ("visible_wireless_other_feature_negative", "HL-10W支持无线网络连接，但不支持自动双面。", True),
    ("inherited_hidden_parent", "<div hidden><section><b>支持无线网络连接</b></section></div>本型号仅USB。", None),
    ("malformed_hidden_child", "<div hidden><span>支持无线网络连接</div>本型号仅USB。", None),
)


class P09FollowupRegression(unittest.TestCase):
    def test_original_fourteen_independent_html_expectations(self):
        now = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
        for label, snippet, expected in HTML_CASES:
            with self.subTest(label=label):
                html = ("<html><body><h1>HL-10W HL-10W 黑白激光打印机</h1>"
                        + snippet + "<footer>服务支持</footer></body></html>").encode("utf-8")
                row = parse_detail("HL-10W", html, observed_at=now)
                self.assertIs(row["facts"].get("wireless", {}).get("value"), expected)

    def test_unhandled_hidden_css_is_rejected_not_promoted_to_fact(self):
        now = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
        html = (
            '<html><body><h1>HL-10W HL-10W 黑白激光打印机</h1>'
            '<style>.claim > span{display:none}</style>'
            '<div class="claim"><span>支持无线网络连接</span></div>'
            '<footer>服务支持</footer></body></html>'
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "unresolved_css_hidden_visibility"):
            parse_detail("HL-10W", html, observed_at=now)

    def test_report_nested_approval_link_price_and_bad_field_types_are_blocked(self):
        now = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
        payload = {"error_code": 0, "data": {"rows": [{
            "title": "兄弟 HL-B2158W 黑白激光打印机", "brand_name": "Brother",
            "mall_name": "京东", "shop_name": "合成店", "cate3_name": "打印机",
            "union_spec": '{"型号":"HL-B2158W"}',
            "url": "https://union-click.jd.com/?tracking=fake",
        }]}}
        imported = ingest_haina_product_search(payload, observed_at=now.isoformat(), now=now)
        self.assertEqual(build_discovery_pool([imported], now=now)["unverified_source_lead_count"], 1)
        for field, value in (
            ("brand_hint", {"url": "https://s.click.taobao.com/fake", "price": 1, "purchase_recommendation_approved": True}),
            ("title_model_candidates", [{"price": 1, "model": "HL-B2158W"}]),
            ("spec_model_candidates", ["https://fake.example/offers"]),
            ("seller_type_hint", ["旗舰店"]),
            ("used_or_refurbished_hint", "false"),
            ("price", 1),
        ):
            with self.subTest(field=field):
                modified = deepcopy(imported)
                modified["items"][0][field] = value
                pool = build_discovery_pool([modified], now=now)
                self.assertEqual(pool["candidate_count"], 0)
                self.assertEqual(pool["unverified_source_lead_count"], 0)
                self.assertEqual(pool["rejected_count"], 1)
                self.assertNotIn("s.click.taobao.com", json.dumps(pool))

    def test_stale_billing_and_consumables_not_current(self):
        catalog = load_reviewed_local_replay()
        row = next(x for x in catalog["products"] if x["model_id"] == "HL-10W")
        row["manufacturer_detail_evidence"]["observed_at"] = "2020-01-01T00:00:00Z"
        comparison = compare_products(
            catalog, category="printer", required={"wireless": True},
            today=datetime(2026, 11, 10, tzinfo=timezone.utc).date()
        )
        result = next(x for x in comparison["candidates"] if x["model_id"] == "HL-10W")
        self.assertTrue(result["manufacturer_detail_is_stale"])
        self.assertEqual(result["billing_model"], "unknown")
        self.assertEqual(result["consumables"], [])
        self.assertFalse(any("此型号采用购买打印页数" in x for x in result["unknowns"]))
        self.assertTrue(any("历史详情" in x for x in result["unknowns"]))

    def test_cli_utf8_and_report_injection_not_echoed(self):
        now = datetime.now(timezone.utc)
        payload = {"error_code": 0, "data": {"rows": [{
            "title": "兄弟 HL-B2158W 黑白激光打印机", "brand_name": "Brother",
            "mall_name": "京东", "shop_name": "合成店", "cate3_name": "打印机",
        }]}}
        imported = ingest_haina_product_search(payload, observed_at=now.isoformat(), now=now)
        imported["items"][0]["brand_hint"] = {
            "url": "https://s.click.taobao.com/fake", "price": 1,
            "purchase_recommendation_approved": True
        }
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.json"
            path.write_text(json.dumps(imported, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-X", "utf8", "-m", "shopping_decision.dialogue_flow",
                 "--haina-report", str(path)],
                input='{"text":"合成中文","answers":{"category":"printer","needs_color":false}}\n',
                capture_output=True, text=True, encoding="utf-8", timeout=30
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("s.click.taobao.com", proc.stdout)
        lines = [json.loads(x) for x in proc.stdout.splitlines()]
        self.assertEqual(lines[1]["discovery_pool"]["unverified_source_lead_count"], 0)
        self.assertFalse(lines[1]["discovery_pool"]["purchase_recommendation_approved"])
        self.assertFalse(lines[1]["discovery_pool"]["transactions_enabled"])


if __name__ == "__main__":
    unittest.main()
