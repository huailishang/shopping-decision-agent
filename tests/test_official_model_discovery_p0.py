"""厂商商品目录发现只生成新候选，不把网页类别当成通过审核的功能。"""
from unittest import TestCase

from shopping_decision.official_model_discovery import discover_brother_monochrome


class OfficialModelDiscoveryTests(TestCase):
    def test_extracts_only_mono_model_links_and_deduplicates(self):
        html = """
        <a href="/printer/prt/hl-l1238w">HL-L1238W 黑白激光打印机</a>
        <a href="/printer/prt/hl-l1238w">了解详情</a>
        <a href="/printer/prt/hl-l3228cdw">HL-L3228CDW 彩色激光打印机</a>
        <a href="/printer/prt/hl-b2158w">HL-B2158W 高速黑白激光打印机</a>
        <a href="https://example.com/printer/prt/hl-evil">HL-EVIL 黑白激光打印机</a>
        """
        result = discover_brother_monochrome(html)
        self.assertEqual({p["model_id"] for p in result}, {"HL-L1238W", "HL-B2158W"})
        self.assertTrue(all(p["status"] == "discovered_unverified_facts" for p in result))

    def test_model_discovery_does_not_assert_price_or_compatibility(self):
        html = '<a href="/printer/prt/hl-10w">HL-10W 黑白激光打印机</a>'
        result = discover_brother_monochrome(html)
        self.assertEqual(result[0]["model_id"], "HL-10W")
        self.assertNotIn("price", result[0])
        self.assertNotIn("wechat_supported", result[0])
        self.assertNotIn("approval", result[0])
