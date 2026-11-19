"""P0.8 修复：独立评估者发现的误判/主线断点 + 双商城用户辅助入口回归。"""
import base64
from copy import deepcopy
from datetime import datetime, timezone
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib

from shopping_decision.p0_7_official_details import (
    parse_detail, load_reviewed_local_replay, enrich_discovered_catalog, archive_public_detail,
)
from shopping_decision.product_compare import compare_products, load_official_catalog
from shopping_decision.public_catalog import catalog_from_brother_snapshot, _read_bounded_json, BROTHER_SNAPSHOT
from shopping_decision.discovery_bridge import review_user_links, shop_search_url
from shopping_decision.discovery_pool import build_discovery_pool
from shopping_decision.discovery_ingest import parse_taobao_item_url
from shopping_decision.dialogue_flow import apply_turn, compare_dialogue, new_dialogue, next_questions

NOW = datetime(2026, 11, 9, 12, 30, tzinfo=timezone.utc)


def html(text):
    return ("<html><body><h1>HL-10W HL-10W 黑白激光打印机</h1>"
            + text + "<footer>服务支持</footer></body></html>").encode("utf-8")


def scenario():
    return apply_turn(new_dialogue(), {
        "category": "printer", "usage": "家用",
        "needs_color": False, "accepts_outsourced_color": True,
        "budget_max_cny": 1000, "monthly_pages_range": [0, 50],
        "wechat_required": True, "wechat_workflow": "miniprogram",
        "requires_wireless": True,
    }, raw_text="黑白无线微信打印，1000元以内，每月0-50页")


class P08RepairTests(unittest.TestCase):
    def test_reviewer_four_misread_regressions(self):
        negative_cases = (
            ("wireless", "本机不支持无线网络连接，仅支持USB打印。"),
            ("wechat_miniprogram", "本机不支持微信小程序直连，支持远程打印的是其他型号。"),
            ("auto_duplex", "HL-B2188DW 标配A4自动双面打印；HL-10W不支持自动双面打印。"),
            ("wireless", '<script>var otherModelText="支持无线网络连接";</script>本机仅支持USB。'),
        )
        for key, snippet in negative_cases:
            with self.subTest(feature=key, snippet=snippet):
                d = parse_detail("HL-10W", html(snippet), observed_at=NOW)
                self.assertNotIn(key, d["facts"])

    def test_hidden_style_template_and_other_model_not_trusted(self):
        for snippet in (
            '<span style="display:none">支持无线网络连接</span>本机仅USB。',
            '<template>支持无线网络连接</template>本机仅USB。',
            '<span aria-hidden="true">支持无线网络连接</span>本机仅USB。',
            'HL-L1228 支持无线网络连接；HL-10W仅支持USB。',
        ):
            with self.subTest(snippet=snippet):
                x = parse_detail("HL-10W", html(snippet), observed_at=NOW)
                self.assertNotIn("wireless", x["facts"])

    def test_positive_manufacturer_evidence_still_works(self):
        content = ("支持无线网络连接 微信小程序直连，支持远程打印 "
                   "按页付费 专门通过平台购买打印页数。")
        d = parse_detail("HL-10W", html(content), observed_at=NOW)
        self.assertTrue(d["facts"]["wireless"]["value"])
        self.assertTrue(d["facts"]["wechat_miniprogram"]["value"])
        self.assertEqual(d["billing_model"], "buy_print_pages_to_claim_consumables")

    def test_future_detail_is_rejected_during_merge_and_comparison(self):
        from pathlib import Path
        live = json.loads(Path("reports/p0_7_live_discovery_20261109.json").read_text(encoding="utf-8"))
        known = load_official_catalog()
        view = catalog_from_brother_snapshot(_read_bounded_json(BROTHER_SNAPSHOT),
                                             known_catalog=known, now=NOW)
        view["old_model_ids"] = [p["model_id"] for p in known["products"]]
        fake = deepcopy(live["details"][0])
        fake["observed_at"] = "2099-01-01T00:00:00+00:00"
        with self.assertRaises(ValueError):
            enrich_discovered_catalog(view, [fake])
        catalog = load_reviewed_local_replay()
        for model in catalog["products"]:
            if "manufacturer_detail_evidence" in model:
                model["manufacturer_detail_evidence"]["observed_at"] = "2099-01-01T00:00:00+00:00"
                break
        with self.assertRaises(ValueError):
            compare_products(catalog, category="printer", required={"monochrome_print": True},
                             today=NOW.date())

    def test_page_plan_and_evidence_exposed_to_comparison(self):
        c = load_reviewed_local_replay()
        x = compare_products(c, category="printer", required={"monochrome_print": True},
                             budget_max_cny=1000, today=NOW.date())
        by_id = {r["model_id"]: r for r in x["candidates"]}
        a = by_id["HL-10W"]
        self.assertEqual(a["billing_model"], "buy_print_pages_to_claim_consumables")
        self.assertEqual(len(a["manufacturer_detail_evidence"]["response_sha256"]), 64)
        self.assertEqual(a["manufacturer_detail_evidence"]["source_url"], a["official_url"])
        self.assertTrue(any("购买打印页数" in z for z in a["unknowns"]))
        self.assertEqual(a["budget_status"], "unverified_no_authorized_live_quote")
        self.assertIsNone(a["live_price_cny"])

    def test_normal_dialogue_replays_local_evidence_and_retracts(self):
        state = scenario()
        x = compare_dialogue(state)
        self.assertEqual(x["source_mode"], "recorded_manufacturer_detail_replay_no_network")
        before = {r["model_id"]: r for r in x["comparison"]["comparison"]["candidates"]}
        self.assertIn("wechat_miniprogram", before["HL-10W"]["required_met"])
        state = apply_turn(state, {"requires_wireless": False, "wechat_required": False,
                                   "requires_auto_duplex": True},
                           raw_text="修改条件，不要求微信无线，改成必须自动双面")
        y = compare_dialogue(state)
        after = {r["model_id"]: r for r in y["comparison"]["comparison"]["candidates"]}
        self.assertIn("auto_duplex", after["HL-B2188DW"]["required_met"])
        self.assertNotIn("wechat_miniprogram", after["HL-10W"]["required_met"])
        self.assertTrue(state["history"][-1]["old_conclusions_invalidated"])
        self.assertFalse(y["transactions_enabled"])

    def test_color_and_prior_answer_conflict_needs_confirmation(self):
        state = scenario()
        state = apply_turn(state, {"requirements": ["必须彩色打印"]},
                           raw_text="又说必须彩色打印")
        x = compare_dialogue(state)
        self.assertEqual(x["status"], "condition_conflict")

    def test_explicit_unknown_can_stay_unknown_with_actions(self):
        state = scenario()
        state = apply_turn(state, {"budget_scope": "unknown", "wechat_workflow": "unknown"},
                           raw_text="现在不确定费用口径和微信方式")
        x = compare_dialogue(state)
        self.assertEqual(x["status"], "model_facts_only_not_purchase")
        self.assertTrue(x["unresolved_actions"])
        self.assertFalse(x["purchase_recommendation_approved"])
        self.assertNotIn("wechat_workflow", [q["field"] for q in next_questions(state, limit=3)])

    def test_public_html_archive_replay_is_digest_bound(self):
        content = html("支持无线网络连接")
        with TemporaryDirectory() as tmp:
            saved = archive_public_detail("HL-10W", content, archive_root=Path(tmp))
            self.assertEqual(Path(saved).read_bytes(), content)
            self.assertEqual(Path(saved).name, hashlib.sha256(content).hexdigest() + ".html")
            self.assertEqual(archive_public_detail("HL-10W", content, archive_root=Path(tmp)), saved)

    def test_taobao_and_tmall_links_strict_validation(self):
        a = review_user_links("打印机", "https://item.taobao.com/item.htm?id=1234567890\n"
                                "https://detail.tmall.com/item.htm?id=1234567891",
                                platform="taobao", now=NOW)
        self.assertEqual(a["candidate_count"], 2)
        self.assertTrue(all(r["platform"] == "TAOBAO_PUBLIC_UNVERIFIED" for r in a["candidates"]))
        self.assertEqual(a["verified_quote_count"], 0)
        self.assertFalse(a["transactions_enabled"])
        self.assertTrue(shop_search_url("打印机", platform="taobao").startswith("https://s.taobao.com/search?q="))

    def test_bad_shortlinks_spoof_and_repeated_ids_are_rejected(self):
        bad = (
            "https://item.taobao.com.evil.com/item.htm?id=1234567890",
            "https://m.tb.cn/aabbcc",
            "http://item.taobao.com/item.htm?id=1234567890",
            "https://item.taobao.com/item.htm?id=1234567890&id=9999999999",
            "https://item.taobao.com@evil.example/item.htm?id=1234567890",
        )
        self.assertTrue(all(parse_taobao_item_url(x) is None for x in bad))
        out = review_user_links("打印机", "\n".join(bad), platform="taobao", now=NOW)
        self.assertEqual(out["candidate_count"], 0)
        self.assertEqual(out["rejected_count"], len(bad))

    def test_jd_taobao_same_digits_kept_separate(self):
        a = review_user_links("打印机", "https://item.jd.com/1234567890.html", now=NOW)
        b = review_user_links("打印机", "https://item.taobao.com/item.htm?id=1234567890",
                              platform="taobao", now=NOW)
        pool = build_discovery_pool([a, b], now=NOW)
        self.assertEqual(pool["candidate_count"], 2)
        self.assertEqual({x["platform"] for x in pool["candidates"]}, {"JD", "TAOBAO"})
        self.assertEqual(pool["verified_quote_count"], 0)

    def test_taobao_java_python_bridge_is_backward_compatible(self):
        params = ["打印机", "https://item.taobao.com/item.htm?id=1234567890", "taobao"]
        proc = subprocess.run(
            [sys.executable, "-m", "shopping_decision.discovery_bridge",
             *[base64.b64encode(x.encode()).decode() for x in params]],
            capture_output=True, text=True, timeout=8)
        self.assertEqual(proc.returncode, 0)
        vals = {k: base64.b64decode(v).decode()
                for k, v in (line.split("\t", 1) for line in proc.stdout.splitlines())}
        self.assertEqual(vals["status"], "candidates_unverified")
        self.assertEqual(vals["candidate_urls"], "https://item.taobao.com/item.htm?id=1234567890")
        old = subprocess.run(
            [sys.executable, "-m", "shopping_decision.discovery_bridge",
             *[base64.b64encode(x.encode()).decode() for x in
               ("打印机", "https://item.jd.com/1234567890.html")]],
            capture_output=True, text=True, timeout=8)
        self.assertEqual(old.returncode, 0)
        old_values = {k: base64.b64decode(v).decode()
                      for k, v in (line.split("\t", 1) for line in old.stdout.splitlines())}
        self.assertEqual(old_values["status"], "candidates_unverified")
