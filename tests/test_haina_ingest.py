"""海纳离线线索导入：只使用合成输入，验证身份降级与正常入口可见性。"""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from shopping_decision.discovery_pool import build_discovery_pool
from shopping_decision.haina_ingest import ingest_haina_product_search

NOW = datetime(2026, 11, 10, 14, 0, tzinfo=timezone.utc)
AT = "2026-11-10T13:59:00Z"


def sample_payload():
    return {
        "error_code": 0,
        "error_msg": "Success",
        "data": {
            "rows": [
                {
                    "title": "兄弟HL-2595DW 黑白激光打印机",
                    "brand_name": "兄弟（Brother）",
                    "mall_id": "183",
                    "mall_name": "京东",
                    "shop_name": "兄弟打印旗舰店",
                    "shop_type": "旗舰店",
                    "cate3_name": "打印机",
                    "url": "https://union-click.jd.com/jdc?tracking=secret&skuId=123456789",
                    "price": "¥1999",
                    "score": "0.99",
                    "comment_cnt": "999",
                    "union_spec": json.dumps(
                        {"SpecParams": {"主体": {"认证型号": "MFC-L5728DW"}}},
                        ensure_ascii=False,
                    ),
                },
                {
                    "title": "二手兄弟 HL-2260/HL-2595DW 多型号打印机",
                    "brand_name": "兄弟",
                    "mall_id": "243",
                    "mall_name": "淘宝精选",
                    "shop_name": "二手办公设备",
                    "shop_type": "其他第三方",
                    "cate3_name": "打印机",
                    "url": "https://s.click.taobao.com/t?tracking=secret&skuId=998877",
                    "price": "¥388",
                    "union_spec": json.dumps(
                        {"SpecParams": {"主体": {"认证型号": "HL-2260"}}},
                        ensure_ascii=False,
                    ),
                },
                {
                    "title": "兄弟 HL-B2158W A4 黑白激光打印机",
                    "brand_name": "Brother",
                    "mall_id": "183",
                    "mall_name": "京东",
                    "shop_name": "自营专区",
                    "shop_type": "自营",
                    "cate3_name": "打印机",
                    "url": "https://union-click.jd.com/jdc?tracking=secret",
                    "union_spec": json.dumps(
                        {"SpecParams": {"主体": {"认证型号": "HL-B2158W"}}},
                        ensure_ascii=False,
                    ),
                    "platform_item_id": "999999999",
                    "purchasable": True,
                },
                {
                    "title": "兄弟 HL-L1238W 原装硒鼓",
                    "brand_name": "Brother",
                    "mall_id": "183",
                    "mall_name": "京东",
                    "shop_name": "耗材店",
                    "shop_type": "自营",
                    "cate3_name": "打印机",
                    "url": "https://union-click.jd.com/jdc?tracking=secret",
                    "union_spec": "{}",
                },
            ]
        },
    }


class HainaIngestTests(unittest.TestCase):
    def test_real_response_is_blocked_until_usage_permission_is_approved(self):
        result = ingest_haina_product_search(
            sample_payload(), observed_at=AT, source_mode="real_response", now=NOW
        )
        self.assertEqual(result["status"], "blocked_real_data_use_not_approved")
        self.assertEqual(result["items"], [])
        self.assertFalse(result["purchase_recommendation_approved"])
        self.assertFalse(result["transactions_enabled"])

    def test_synthetic_import_detects_conflicts_bundles_used_and_accessories(self):
        result = ingest_haina_product_search(sample_payload(), observed_at=AT, now=NOW)
        self.assertEqual(result["source_mode"], "synthetic_test")
        self.assertEqual(result["status"], "source_leads_unverified")
        self.assertEqual(result["input_rows"], 4)
        self.assertEqual(result["imported_leads"], 4)
        rows = result["items"]
        self.assertEqual(rows[0]["identity_status"], "title_spec_model_conflict")
        self.assertEqual(rows[0]["link_kind"], "jd_promotion_redirect")
        self.assertEqual(rows[1]["identity_status"], "multiple_model_or_option_ambiguous")
        self.assertTrue(rows[1]["used_or_refurbished_hint"])
        self.assertEqual(rows[2]["identity_status"], "manufacturer_model_candidate_only")
        self.assertEqual(rows[3]["product_kind_status"], "likely_accessory_or_consumable")
        for row in rows:
            self.assertIsNone(row["platform_item_id"])
            self.assertIsNone(row["canonical_url"])
            self.assertFalse(row["identity_verified"])
            self.assertFalse(row["quote_verified"])
            self.assertFalse(row["purchasable"])
            for forbidden in ("url", "price", "score", "comment_cnt", "good_comments_share"):
                self.assertNotIn(forbidden, row)

    def test_candidate_pool_keeps_idless_leads_visible_but_out_of_candidates(self):
        imported = ingest_haina_product_search(sample_payload(), observed_at=AT, now=NOW)
        pool = build_discovery_pool([imported], now=NOW)
        self.assertEqual(pool["candidate_count"], 0)
        self.assertEqual(pool["unverified_source_lead_count"], 4)
        self.assertEqual(pool["unverified_source_leads"][0]["identity_status"], "title_spec_model_conflict")
        self.assertTrue(all(x["platform_item_id"] is None for x in pool["unverified_source_leads"]))
        self.assertFalse(pool["purchase_recommendation_approved"])
        self.assertFalse(pool["transactions_enabled"])

    def test_bad_business_code_and_future_observation_are_rejected(self):
        bad = sample_payload()
        bad["error_code"] = 403
        self.assertEqual(
            ingest_haina_product_search(bad, observed_at=AT, now=NOW)["status"],
            "api_error",
        )
        self.assertEqual(
            ingest_haina_product_search(
                sample_payload(), observed_at="2027-01-01T00:00:00Z", now=NOW
            )["status"],
            "invalid_input",
        )

    def test_normal_text_cli_displays_source_leads_without_claiming_comparison(self):
        imported = ingest_haina_product_search(sample_payload(), observed_at=AT, now=NOW)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "haina-synthetic-report.json"
            path.write_text(json.dumps(imported, ensure_ascii=False), encoding="utf-8")
            turn = {
                "text": "合成测试：黑白打印即可",
                "answers": {
                    "category": "printer",
                    "usage": "家用黑白打印",
                    "needs_color": False,
                    "accepts_outsourced_color": True,
                    "monthly_pages_range": [0, 50],
                    "budget_max_cny": 1000,
                    "wechat_required": False,
                    "requires_wireless": True,
                    "requires_auto_duplex": True,
                },
            }
            proc = subprocess.run(
                [sys.executable, "-X", "utf8", "-m", "shopping_decision.dialogue_flow", "--haina-report", str(path)],
                input=json.dumps(turn, ensure_ascii=False) + "\n",
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(lines), 2)
        discovery = lines[1]["discovery_pool"]
        self.assertEqual(discovery["candidate_count"], 0)
        self.assertEqual(discovery["unverified_source_lead_count"], 4)
        self.assertEqual(discovery["total_unverified_source_lead_count"], 4)
        self.assertEqual(discovery["displayed_source_lead_count"], 3)
        self.assertEqual(len(discovery["unverified_source_leads"]), 3)
        fact_result = lines[1]["comparison"]["comparison"]["comparison"]
        self.assertEqual(fact_result["total_candidate_count"], 9)
        self.assertLessEqual(len(fact_result["candidates"]), 3)
        self.assertIn("excluded_by_verified_spec", [x["status"] for x in fact_result["candidates"]])
        self.assertFalse(discovery["purchase_recommendation_approved"])
        self.assertFalse(discovery["transactions_enabled"])


if __name__ == "__main__":
    unittest.main()
