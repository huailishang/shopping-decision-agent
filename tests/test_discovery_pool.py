"""JD/Taobao 统一候选池测试：完全合成，无商城请求。"""
import copy
from datetime import datetime, timezone
import json
import unittest

from shopping_decision.jd_union_official import import_goods_query_response
from shopping_decision.taobao_material import import_tbk_material_snapshot
from shopping_decision.discovery_bridge import review_user_links
from shopping_decision.discovery_pool import build_discovery_pool

NOW = datetime(2026, 11, 7, 8, 0, tzinfo=timezone.utc)
AT = "2026-11-07T07:00:00Z"
SKU = "100126724020"
ALIASES = {"HL-L1238W": ["HL-L1238W"], "HL-L1238WXL": ["HL-L1238WXL"]}


def jd(title="兄弟HL-L1238W 黑白打印机"):
    goods = [{"skuId": int(SKU), "skuName": title, "priceInfo": {"price": 700}}]
    content = {"jd_union_open_goods_query_responce": {
        "code": "0", "queryResult": json.dumps({"code": 200, "data": goods}, ensure_ascii=False)}}
    return import_goods_query_response(content, keyword="打印机", observed_at=AT, now=NOW)


def tb(title="配件硒鼓适用HL-L1238W"):
    content = {"tbk_dg_material_optional_response": {"result_list": {
        "map_data": [{"item_id": SKU, "title": title, "reserve_price": "999"}]}}}
    return import_tbk_material_snapshot(content, keyword="打印机", observed_at=AT, now=NOW)


def manual():
    return review_user_links("打印机", "https://item.jd.com/" + SKU + ".html", now=NOW)


class DiscoveryPoolTest(unittest.TestCase):
    def test_two_platforms_same_digits_do_not_merge(self):
        result = build_discovery_pool([jd(), tb(), manual()], known_aliases=ALIASES, now=NOW)
        self.assertEqual(result["candidate_count"], 2)
        first, second = result["candidates"]
        self.assertEqual(first["platform"], "JD")
        self.assertEqual(second["platform"], "TAOBAO")
        self.assertEqual(first["platform_item_id"], second["platform_item_id"])
        self.assertEqual(len(first["provenance"]), 2)
        self.assertEqual(len(second["provenance"]), 1)

    def test_model_anchor_with_chinese_prefix_is_only_hint(self):
        result = build_discovery_pool([jd()], known_aliases=ALIASES, now=NOW)
        item = result["candidates"][0]
        self.assertEqual(item["model_hint"], "HL-L1238W")
        self.assertEqual(item["model_hint_status"], "title_anchor_only_unverified")
        self.assertFalse(item["identity_verified"])
        self.assertFalse(item["quote_verified"])

    def test_accessories_with_model_title_are_not_approved(self):
        result = build_discovery_pool([tb()], known_aliases=ALIASES, now=NOW)
        self.assertEqual(result["candidates"][0]["model_hint"], "HL-L1238W")
        self.assertIn("product_kind", result["candidates"][0]["missing_fields"])
        self.assertFalse(result["candidates"][0]["purchasable"])

    def test_model_suffix_not_false_positive(self):
        result = build_discovery_pool([jd("兄弟HL-L1238WXL")],
                                      known_aliases=ALIASES, now=NOW)
        self.assertEqual(result["candidates"][0]["model_hint"], "HL-L1238WXL")

    def test_manual_link_has_no_title_and_no_model(self):
        result = build_discovery_pool([manual()], known_aliases=ALIASES, now=NOW)
        self.assertIsNone(result["candidates"][0]["model_hint"])
        self.assertEqual(result["candidates"][0]["model_hint_status"], "no_title_source")

    def test_fake_price_flags_never_promoted(self):
        data = jd()
        data["items"][0]["live_price_cny"] = 1
        data["items"][0]["purchasable"] = True
        data["items"][0]["quote_verified"] = True
        result = build_discovery_pool([data], now=NOW)
        self.assertIsNone(result["candidates"][0]["live_price_cny"])
        self.assertIsNone(result["candidates"][0]["within_budget"])
        self.assertFalse(result["candidates"][0]["purchasable"])
        self.assertFalse(result["purchase_recommendation_approved"])
        self.assertFalse(result["transactions_enabled"])

    def test_platform_spoofed_input_rejected(self):
        data = jd()
        data["items"][0]["platform"] = "TAOBAO_TBK_IMPORT_UNVERIFIED"
        result = build_discovery_pool([data], now=NOW)
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["rejected_count"], 1)

    def test_conflicting_titles_for_same_id_require_review(self):
        a = jd("HL-L1238W")
        b = jd("HL-L1238WXL")
        result = build_discovery_pool([a,b], known_aliases=ALIASES, now=NOW)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["candidates"][0]["status"], "needs_identity_conflict_review")
        self.assertIsNone(result["candidates"][0]["model_hint"])

    def test_error_response_report_blocked(self):
        data = jd()
        data["status"] = "api_error"
        result = build_discovery_pool([data], now=NOW)
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["blocked_report_count"], 1)

    def test_untrusted_future_time_rejected(self):
        data = jd()
        data["items"][0]["observed_at"] = "2027-01-01T00:00:00Z"
        result = build_discovery_pool([data], now=NOW)
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["rejected_count"], 1)

    def test_truncation_does_not_replace_existing(self):
        result = build_discovery_pool([jd(), tb()], now=NOW, max_candidates=1)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_bad_args_are_rejected(self):
        with self.assertRaises(ValueError):
            build_discovery_pool([jd()], now=NOW, max_candidates=True)
        with self.assertRaises(ValueError):
            build_discovery_pool([jd()], known_aliases=[], now=NOW)


if __name__ == "__main__":
    unittest.main()
