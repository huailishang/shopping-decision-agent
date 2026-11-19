"""P0.9 第二次独立复评后的执行者回归：12个原反证、事实准入、报告逐行隔离。"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest

from shopping_decision.p0_7_official_details import (
    parse_detail, enrich_discovered_catalog, load_reviewed_local_replay,
)
from shopping_decision.public_catalog import (
    catalog_from_brother_snapshot, _read_bounded_json, BROTHER_SNAPSHOT,
)
from shopping_decision.product_compare import load_official_catalog, compare_products
from shopping_decision.discovery_pool import build_discovery_pool
from shopping_decision.haina_ingest import ingest_haina_product_search


# 由11-11独立再评估报告里的12个输入固定为执行者回归用例，不更改评估者原报告。
CASES = (
    ("question", "本机是否支持无线网络连接？请查阅详细规格。", None, False),
    ("conditional", "如果本机支持无线网络连接，请先连接路由器。", None, False),
    ("later_correction", "本型号支持无线网络连接。更正：无线网络连接不支持，仅有USB。", None, False),
    ("long_model_scope", "<section><h2>HL-B2188DW</h2><p>连接方式说明</p><p>家庭网络环境</p><p>设置步骤如下</p><p>支持无线网络连接。</p></section><p>HL-10W仅USB。</p>", None, False),
    ("inline_comment_hidden", '<span style="display:/**/none">支持无线网络连接</span>本机仅USB。', None, False),
    ("class_case", '<style>.WIRELESS {display:none}</style><div class="wireless">HL-10W支持无线网络连接。</div>', True, True),
    ("other_feature_negative", "本型号不支持扫描。支持无线网络连接。", True, False),
    ("visible_descendant", '<style>.panel .feature {opacity:0.75;display:block}</style><div class="panel"><span class="feature">HL-10W支持无线网络连接。</span></div>', True, False),
    ("other_model_then_current", "<h2>DCP-B7658DW</h2><p>不支持无线网络连接。</p><h2>HL-10W</h2><p>本型号支持无线网络连接。</p>", True, False),
    ("unknown_css", '<style>.area + .secret{display:none}</style><div class="secret">支持无线网络连接</div>本机仅USB。', "reject", False),
    ("hidden_attribute", '<div hidden="hidden"><p>HL-10W支持无线网络连接。</p></div>本机仅USB。', None, False),
    ("inline_negation", "<p>本机<span>不</span>支持无线网络连接，仅USB。</p>", None, False),
)


def sample_detail(snippet, *, standard=False):
    prefix = "<!doctype html>" if standard else ""
    body = (prefix + '<html><body><h1>HL-10W HL-10W 黑白激光打印机</h1>'
            + snippet + '<footer>服务支持</footer></body></html>').encode("utf-8")
    return parse_detail("HL-10W", body, observed_at=datetime.now(timezone.utc))


def discovered_view(now):
    known = load_official_catalog()
    view = catalog_from_brother_snapshot(
        _read_bounded_json(BROTHER_SNAPSHOT), known_catalog=known, now=now)
    view["old_model_ids"] = [x["model_id"] for x in known["products"]]
    return view


def synthetic_report(now):
    payload = {"error_code": 0, "data": {"rows": [{
        "title": "兄弟 HL-B2158W 黑白激光打印机", "brand_name": "Brother",
        "mall_name": "京东", "shop_name": "合成店", "cate3_name": "打印机",
        "union_spec": '{"型号":"HL-B2158W"}',
    }]}}
    return ingest_haina_product_search(payload, observed_at=now.isoformat(), now=now)


class P09SecondRepair(unittest.TestCase):
    def test_twelve_new_independent_html_inputs(self):
        for label, snippet, expected, standard in CASES:
            with self.subTest(case=label):
                try:
                    detail = sample_detail(snippet, standard=standard)
                    value = detail["facts"].get("wireless", {}).get("value")
                    self.assertNotEqual(expected, "reject")
                    self.assertIs(value, expected)
                except ValueError:
                    if expected != "reject":
                        raise

    def test_new_auto_claim_never_becomes_approved_comparison_fact(self):
        now = datetime.now(timezone.utc)
        for label, snippet, expected, standard in CASES:
            if expected == "reject":
                continue
            with self.subTest(case=label):
                detail = sample_detail(snippet, standard=standard)
                view = discovered_view(now)
                catalog = enrich_discovered_catalog(view, [detail])
                model = next(x for x in catalog["products"] if x["model_id"] == "HL-10W")
                self.assertEqual(model["manufacturer_claim_pending_review"]["status"], "awaiting_per_field_review")
                self.assertNotIn("manufacturer_detail_evidence", model)
                comparison = compare_products(
                    catalog, category="printer", required={"wireless": True}, today=now.date())
                result = next(x for x in comparison["candidates"] if x["model_id"] == "HL-10W")
                self.assertNotIn("wireless", result["required_met"])
                self.assertIn("wireless", result["required_unknown"])
                self.assertFalse(comparison["purchase_recommendation_approved"])

    def test_approved_three_source_replay_keeps_real_positive(self):
        catalog = load_reviewed_local_replay()
        rows = {x["model_id"]: x for x in catalog["products"]}
        for model_id in ("HL-10W", "HL-B2188DW", "HL-B2158W"):
            with self.subTest(model=model_id):
                self.assertTrue(rows[model_id]["facts"]["wireless"]["value"])
                self.assertEqual(
                    rows[model_id]["manufacturer_detail_evidence"]["admission"],
                    "frozen_p0_8_local_field_review")
        result = compare_products(catalog, category="printer",
                                  required={"wireless": True}, today=datetime.now(timezone.utc).date())
        for row in result["candidates"]:
            if row["model_id"] in rows and row["model_id"] in ("HL-10W", "HL-B2188DW", "HL-B2158W"):
                self.assertIn("wireless", row["required_met"])
        self.assertFalse(result["purchase_recommendation_approved"])

    def test_forged_review_flag_or_changed_digest_cannot_approve(self):
        now = datetime.now(timezone.utc)
        view = discovered_view(now)
        detail = sample_detail("HL-10W支持无线网络连接。")
        with self.assertRaisesRegex(ValueError, "detail_not_in_frozen_reviewed_set"):
            enrich_discovered_catalog(view, [detail], reviewed_local_replay=True)

    def test_url_string_rejected_and_bad_enum_does_not_discard_good_row(self):
        now = datetime.now(timezone.utc)
        report = synthetic_report(now)
        self.assertEqual(build_discovery_pool([report], now=now)["unverified_source_lead_count"], 1)
        for key in ("brand_hint", "seller_hint", "mall_hint", "displayed_title"):
            with self.subTest(field=key):
                altered = deepcopy(report)
                altered["items"][0][key] = "https://s.click.taobao.com/t?tracking=synthetic-review-11"
                result = build_discovery_pool([altered], now=now)
                self.assertEqual(result["unverified_source_lead_count"], 0)
                self.assertEqual(result["rejected_count"], 1)
                self.assertNotIn("synthetic-review-11", json.dumps(result))
        mixed = deepcopy(report)
        invalid = deepcopy(report["items"][0])
        invalid["source_id"] = "haina-synthetic-row:002"
        invalid["identity_status"] = {}
        mixed["items"].append(invalid)
        result = build_discovery_pool([mixed], now=now)
        self.assertEqual(result["unverified_source_lead_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_mixed_good_bad_cli_outputs_only_good_row(self):
        now = datetime.now(timezone.utc)
        report = synthetic_report(now)
        bad = deepcopy(report["items"][0])
        bad["source_id"] = "haina-synthetic-row:002"
        bad["identity_status"] = {}
        report["items"].append(bad)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.json"
            path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "shopping_decision.dialogue_flow", "--haina-report", str(path)],
                input='{"text":"合成测试","answers":{"category":"printer","needs_color":false}}\n',
                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = [json.loads(x) for x in proc.stdout.splitlines()]
        pool = output[1]["discovery_pool"]
        self.assertEqual(pool["unverified_source_lead_count"], 1)
        self.assertEqual(pool["rejected_count"], 1)
        self.assertFalse(pool["purchase_recommendation_approved"])
        self.assertNotIn("https://s.click.taobao.com", proc.stdout)


if __name__ == "__main__":
    unittest.main()
