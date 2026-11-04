"""厂商事实来源回查只能访问白名单，不因为包含型号就宣称功能获得独立核验。"""
from unittest import TestCase
from shopping_decision.official_source_check import is_allowed, inspect_html, check_one


class OfficialSourceRecheckTests(TestCase):
    def test_only_predefined_https_manufacturer_domains(self):
        self.assertTrue(is_allowed("https://www.brother.cn/printer/prt/hl-l1238w"))
        self.assertTrue(is_allowed("https://support.hp.com/cn-zh/product/product-specs/a"))
        for url in ("http://www.brother.cn/a", "https://127.0.0.1/x",
                    "https://brother.cn.evil.example/a",
                    "https://www.brother.cn:8000/a", "https://username@support.hp.com/"):
            self.assertFalse(is_allowed(url), url)

    def test_html_model_anchor_but_not_capability(self):
        body = b"<html><body><strong>HL-L1238W</strong> product page</body></html>"
        self.assertTrue(inspect_html(body, "HL-L1238W"))
        self.assertFalse(inspect_html(body, "HL-L1808W"))
        self.assertTrue(inspect_html(b"<html>HP 108w</html>", "HP-Laser-108w"))

    def test_blocked_url_is_not_visited(self):
        result = check_one("https://127.0.0.1/test", "X")
        self.assertEqual(result["status"], "blocked_url")

    def test_source_check_does_not_change_catalog(self):
        from shopping_decision.product_compare import load_official_catalog, CATALOG_PATH
        before = CATALOG_PATH.read_bytes()
        load_official_catalog()
        self.assertEqual(before, CATALOG_PATH.read_bytes())
