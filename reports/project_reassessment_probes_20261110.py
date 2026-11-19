# 2026-11-10 项目重评：复用11-09独立故障逻辑；本轮输出另存，后续执行者可指定自己的输出路径。
"""P0.8 独立诊断留档；含失败样本，不是商品推荐通过率。"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from shopping_decision.p0_7_official_details import parse_detail, load_reviewed_local_replay, enrich_discovered_catalog
from shopping_decision.product_compare import compare_products, load_official_catalog
from shopping_decision.public_catalog import catalog_from_brother_snapshot, _read_bounded_json, BROTHER_SNAPSHOT
from shopping_decision.dialogue_flow import new_dialogue, apply_turn, compare_dialogue
from shopping_decision.discovery_bridge import review_user_links


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def html(text):
    return ("<html><body>导航 HL-10W HL-10W 黑白激光打印机 页面 " + text
            + " 服务支持 页脚内容仅用于边界和格式检验</body></html>").encode("utf-8")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="复算已暴露的独立诊断，不是推荐通过率")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "reports/project_reassessment_probes_20261110.json")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    original = []
    for p in read("reports/assessment_probes_20261109.json")["new_adversarial_extraction_probes"]:
        x = parse_detail("HL-10W", html(p["input"]), observed_at=now)
        actual = x["facts"].get(p["feature"], {}).get("value")
        original.append({"id": p["id"], "input": p["input"], "feature": p["feature"],
                         "actual": actual, "expectation_met": actual is not True})
    variants = []
    for ident, text, feature in (
        ("other_model_suffix_duplex", "标配A4自动双面打印（仅限HL-B2188DW），HL-10W为手动双面。", "auto_duplex"),
        ("other_model_suffix_wireless", "支持无线网络连接（仅适用于HL-B2188DW），本型号仅USB连接。", "wireless"),
        ("other_model_suffix_billing", "按页付费、购买打印页数（仅适用于HL-B2188DW），HL-10W使用普通耗材。", "pay_per_page_consumables"),
        ("stylesheet_hidden_wireless", '<style>.not-visible { display: none; }</style><div class="not-visible">支持无线网络连接</div>本机仅USB。', "wireless"),
        ("visible_positive_wireless", "本型号支持无线网络连接。", "wireless"),
    ):
        x = parse_detail("HL-10W", html(text), observed_at=now)
        actual = x["facts"].get(feature, {}).get("value")
        expected = ident == "visible_positive_wireless"
        variants.append({"id": ident, "input_kind": "synthetic_html", "input": text, "feature": feature,
                         "expected": "true" if expected else "not_true", "actual": actual,
                         "expectation_met": actual is True if expected else actual is not True})

    source = read("reports/p0_8_refetched_official_sources_20261109.json")
    raw_replay = []
    for row in source["models"]:
        path = ROOT / "data/raw/p0_8_official_details" / (row["response_sha256"] + ".html")
        body = path.read_bytes()
        parsed = parse_detail(row["model_id"], body, observed_at=datetime.fromisoformat(row["observed_at"]))
        positive = [k for k, v in parsed["facts"].items() if v["value"] is True]
        raw_replay.append({"model_id": row["model_id"], "raw_path": path.relative_to(ROOT).as_posix(),
                           "sha256_matches": hashlib.sha256(body).hexdigest() == row["response_sha256"],
                           "positive_features_match": positive == row["extracted_positive_features"],
                           "billing_matches": parsed["billing_model"] == row["billing_model"],
                           "facts": {k: v["value"] for k, v in parsed["facts"].items()},
                           "consumables": [v["model"] for v in parsed["consumables"]]})
    answers = {"category": "printer", "usage": "家用黑白打印", "needs_color": False,
               "accepts_outsourced_color": True, "monthly_pages_range": [0, 50], "budget_max_cny": 1000,
               "wechat_required": True, "wechat_workflow": "miniprogram", "requires_wireless": True}
    state = apply_turn(new_dialogue(), answers, raw_text="评估者合成确认：黑白、无线、微信小程序、千元内")
    before = compare_dialogue(state)
    bc = {x["model_id"]: x for x in before["comparison"]["comparison"]["candidates"]}
    changed = apply_turn(state, {"wechat_required": False, "requires_wireless": False, "requires_auto_duplex": True},
                         raw_text="合成改答：微信无线不再必须，改为必须自动双面")
    after = compare_dialogue(changed)
    ac = {x["model_id"]: x for x in after["comparison"]["comparison"]["candidates"]}
    unknown = apply_turn(state, {"wechat_workflow": "unknown", "budget_scope": "unknown"}, raw_text="合成回答：暂不确定")
    conflict = apply_turn(state, {"requirements": ["必须彩色打印"]}, raw_text="合成冲突输入")
    known = load_official_catalog()
    view = catalog_from_brother_snapshot(_read_bounded_json(BROTHER_SNAPSHOT), known_catalog=known, now=now)
    view["old_model_ids"] = [p["model_id"] for p in known["products"]]
    live = read("reports/p0_7_live_discovery_20261109.json")
    bad = deepcopy(live["details"])
    bad[0]["observed_at"] = "2099-01-01T00:00:00+00:00"
    try:
        enrich_discovered_catalog(view, bad)
        future_rejected = False
    except ValueError:
        future_rejected = True
    stale = deepcopy(load_reviewed_local_replay())
    stale["recorded_on"] = now.date().isoformat()
    for item in stale["products"]:
        if item["model_id"] == "HL-10W":
            item["manufacturer_detail_evidence"]["observed_at"] = "2020-01-01T00:00:00+00:00"
    stale_row = next(x for x in compare_products(stale, category="printer", required={"wireless": True}, today=now.date())["candidates"]
                     if x["model_id"] == "HL-10W")
    digests = {hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "data/raw").rglob("*.html")}
    provenance = []
    for mid in live["target_model_ids"]:
        d = bc[mid]["manufacturer_detail_evidence"]
        fresh = next(x for x in source["models"] if x["model_id"] == mid)
        provenance.append({"model_id": mid, "normal_output_digest": d["response_sha256"],
                           "normal_output_observed_at": d["observed_at"], "matching_raw_file_exists": d["response_sha256"] in digests,
                           "p08_archived_digest": fresh["response_sha256"], "normal_output_uses_p08_archive": d["response_sha256"] == fresh["response_sha256"]})
    links = review_user_links("打印机", "https://item.taobao.com/item.htm?id=1234567890\nhttps://detail.tmall.com/item.htm?id=1234567890\nhttps://item.taobao.com.evil.example/item.htm?id=1234567891\nhttps://m.tb.cn/example", platform="taobao")
    turns = [{"text": "合成结构化确认", "answers": answers}, {"text": "改为自动双面", "answers": {"wechat_required": False, "requires_wireless": False, "requires_auto_duplex": True}}]
    cli = subprocess.run([sys.executable, "-m", "shopping_decision.dialogue_flow"],
                         input="".join(json.dumps(x, ensure_ascii=False) + "\n" for x in turns),
                         env={**os.environ, "PYTHONIOENCODING": "utf-8"}, cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8", timeout=30)
    records = [json.loads(x) for x in cli.stdout.splitlines()]
    result = {"role": "independent_reviewer", "observed_at": now.isoformat(), "original_four": original,
              "new_html_variants": variants, "archived_source_replay": raw_replay,
              "normal_dialogue": {"source_mode": before["source_mode"], "candidate_count": len(bc),
                  "HL_10W_required_met": bc["HL-10W"]["required_met"], "HL_10W_billing_model": bc["HL-10W"]["billing_model"],
                  "HL_10W_unknowns": bc["HL-10W"]["unknowns"], "changed_version": after["session_version"],
                  "old_conclusions_invalidated": changed["history"][-1]["old_conclusions_invalidated"],
                  "HL_B2188DW_auto_duplex_met": "auto_duplex" in ac["HL-B2188DW"]["required_met"],
                  "HL_10W_auto_duplex_unknown": "auto_duplex" in ac["HL-10W"]["required_unknown"],
                  "conflict_status": compare_dialogue(conflict)["status"], "unknown_unresolved_actions": compare_dialogue(unknown)["unresolved_actions"]},
              "normal_output_provenance": provenance, "future_detail_rejected": future_rejected,
              "stale_detail_probe": {k: stale_row[k] for k in (
                  "status", "manufacturer_detail_age_days", "manufacturer_detail_is_stale",
                  "required_met", "required_unknown", "unknowns")},
              "taobao_link_probe": {k: links[k] for k in ("candidate_count", "rejected_count", "purchase_recommendation_approved", "transactions_enabled")},
              "real_text_cli_subprocess": {"returncode": cli.returncode, "output_line_count": len(records),
                  "source_modes": [r.get("comparison", {}).get("source_mode") for r in records[1:]], "versions": [r.get("version") for r in records[1:]]},
              "purchase_recommendation_approved": False, "transactions_enabled": False,
              "limitations": ["新输入是合成故障诊断，不能当推荐通过率。", "原始官网HTML重放不代表本轮再次联网取证。", "文本CLI测试显式使用UTF-8管道编码。"]}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
