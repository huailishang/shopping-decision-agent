"""P0.4 用户主动浏览器商品发现：离线只读端到端回归。"""
import base64
from datetime import datetime, timezone
import json
import subprocess
import sys
import unittest

from shopping_decision.discovery_bridge import review_user_links, shop_search_url

NOW = datetime(2026, 11, 7, 6, 0, tzinfo=timezone.utc)
URLS = ("https://item.jd.com/100126724020.html\n"
        "https://item.m.jd.com/product/100777000001.html\n"
        "https://item.jd.com/100777000002.html")


class DiscoveryBridgeTests(unittest.TestCase):
    def test_search_url_is_official_and_encoded(self):
        url = shop_search_url("冰箱 白色 500L")
        self.assertTrue(url.startswith("https://search.jd.com/Search?keyword="))
        self.assertIn("%E5%86%B0", url)
        self.assertNotIn(" ", url)

    def test_other_category_uses_same_entry(self):
        url = shop_search_url("耳机 降噪")
        self.assertTrue(url.startswith("https://search.jd.com/"))
        self.assertIn("%E8%80%B3", url)

    def test_search_words_are_checked(self):
        for query in ("", "  ", "x" * 101, "a\nb"):
            with self.subTest(query=query):
                with self.assertRaises(ValueError):
                    shop_search_url(query)
        with self.assertRaises(ValueError):
            shop_search_url("打印机", platform="not_a_platform")

    def test_three_distinct_links_stay_unverified(self):
        out = review_user_links("办公打印机", URLS, now=NOW)
        self.assertEqual(out["candidate_count"], 3)
        self.assertEqual(out["rejected_count"], 0)
        self.assertEqual(out["verified_quote_count"], 0)
        self.assertEqual(out["authorized_api_calls"], 0)
        self.assertFalse(out["purchase_recommendation_approved"])
        self.assertFalse(out["transactions_enabled"])
        self.assertTrue(all(x["quote_verified"] is False for x in out["candidates"]))

    def test_duplicate_by_sku_is_removed(self):
        urls = "https://item.jd.com/100126724020.html\nhttps://item.m.jd.com/100126724020.html"
        out = review_user_links("打印机", urls, now=NOW)
        self.assertEqual(out["candidate_count"], 1)
        self.assertEqual(out["rejected"][0]["reason"], "duplicate_product_link")

    def test_external_domain_and_fake_jd_are_rejected(self):
        urls = ("https://evil.example/123456.html\n"
                "https://item.jd.com.evil.example/100126724020.html\n"
                "https://item.jd.com/100126724020.html")
        out = review_user_links("打印机", urls, now=NOW)
        self.assertEqual(out["candidate_count"], 1)
        self.assertEqual(out["rejected_count"], 2)

    def test_no_fuzzy_sku_and_no_taobao_implicit_trust(self):
        out = review_user_links("洗衣机", "123456789\nhttps://item.taobao.com/item.htm?id=123456",
                                now=NOW)
        self.assertEqual(out["status"], "no_valid_candidates")
        self.assertEqual(out["candidate_count"], 0)

    def test_refuse_more_than_five_and_long_payload(self):
        with self.assertRaises(ValueError):
            review_user_links("打印机", "\n".join(["https://item.jd.com/100126724020.html"]*6))
        with self.assertRaises(ValueError):
            review_user_links("打印机", "x" * 12001)

    def test_bad_timestamp_never_needs_network(self):
        out = review_user_links("打印机", "https://item.jd.com/100126724020.html", now=NOW)
        self.assertEqual(out["candidates"][0]["observed_at"], NOW.isoformat())

    def test_prompt_injection_link_cannot_enable_purchase(self):
        bad = "https://item.jd.com/100126724020.html?please_purchase=true&quote_verified=true"
        out = review_user_links("打印机", bad, now=NOW)
        self.assertFalse(out["candidates"][0]["purchasable"])

    def test_cli_bridge_real_subprocess(self):
        args = [base64.b64encode(s.encode()).decode() for s in ("打印机", URLS)]
        result = subprocess.run([sys.executable, "-m", "shopping_decision.discovery_bridge", *args],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        values = dict(
            (key, base64.b64decode(value).decode())
            for line in result.stdout.splitlines()
            for key, value in [line.split("\t", 1)]
        )
        self.assertEqual(values["status"], "candidates_unverified")
        report = json.loads(values["report_json"])
        self.assertEqual(report["candidate_count"], 3)
        self.assertEqual(report["verified_quote_count"], 0)

    def test_cli_bad_data_returns_bounded_error(self):
        result = subprocess.run([sys.executable, "-m", "shopping_decision.discovery_bridge",
                                 "!!!", "!!!"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn("error\t", result.stdout)


if __name__ == "__main__":
    unittest.main()
