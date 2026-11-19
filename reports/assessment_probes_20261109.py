"""独立诊断留档：用新输入找失败，不作为产品通过率或新增训练样本。"""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import date, datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shopping_decision.dialogue_flow import apply_turn, compare_dialogue, new_dialogue, next_questions
from shopping_decision.p0_7_official_details import enrich_discovered_catalog, parse_detail
from shopping_decision.p0_7_pairwise import run_pairwise
from shopping_decision.product_compare import compare_products, load_official_catalog
from shopping_decision.public_catalog import BROTHER_SNAPSHOT, _read_bounded_json, catalog_from_brother_snapshot

TODAY = date(2026, 11, 9)
NOW = datetime(2026, 11, 9, 14, tzinfo=timezone.utc)


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def fixture(text):
    # 合成页面，沿用执行者测试的确切型号标题；攻击文本位于型号正文内。
    return ("<html><body>兄弟官网 导航 HL-10W HL-10W 黑白激光打印机 页面 "
            + text + " 服务支持 页脚内容用于确保样本长度符合解析器限制</body></html>").encode("utf-8")


def main():
    live = read_json("reports/p0_7_live_discovery_20261109.json")
    manual = read_json("knowledge/p0_7_manual_printer_baseline_20261109.json")
    pairwise = run_pairwise(live, manual, today=TODAY)
    known = load_official_catalog()
    view = catalog_from_brother_snapshot(_read_bounded_json(BROTHER_SNAPSHOT), known_catalog=known, now=NOW)
    view["old_model_ids"] = [p["model_id"] for p in known["products"]]
    enriched = enrich_discovered_catalog(view, live["details"])

    extraction = []
    for name, text, feature in (
        ("negated_wireless", "本机不支持无线网络连接，仅支持USB打印。", "wireless"),
        ("negated_wechat", "本机不支持微信小程序直连，支持远程打印的是其他型号。", "wechat_miniprogram"),
        ("other_model_duplex", "HL-B2188DW 标配A4自动双面打印；HL-10W不支持自动双面打印。", "auto_duplex"),
        ("script_only_wireless", '<script>var otherModelText="支持无线网络连接";</script>本机仅支持USB。', "wireless"),
    ):
        detail = parse_detail("HL-10W", fixture(text), observed_at=NOW)
        actual = detail["facts"].get(feature, {}).get("value")
        extraction.append({"id": name, "input_kind": "synthetic_adversarial_html", "input": text,
                           "feature": feature, "expected": "not_true", "actual": actual,
                           "expectation_met": actual is not True})

    answers = {"category": "printer", "usage": "家用黑白打印", "needs_color": False,
               "accepts_outsourced_color": True, "budget_max_cny": 1000,
               "monthly_pages_range": [0, 50], "wechat_required": True,
               "wechat_workflow": "miniprogram", "requires_wireless": True}
    state = apply_turn(new_dialogue(), answers, raw_text="合成确认：黑白、无线及微信小程序均为硬要求，千元内")
    ordinary = compare_dialogue(state)
    injected = compare_dialogue(state, catalog_override=enriched)
    path_rows = []
    for label, result in (("ordinary_text_path", ordinary), ("internal_catalog_injection", injected)):
        rows = {r["model_id"]: r for r in result["comparison"]["comparison"]["candidates"]}
        path_rows.append({"path": label, "status": result["status"],
                          "candidate_count": len(rows),
                          "three_new_models": [{k: rows[m][k] for k in ("model_id", "required_met", "required_unknown")}
                                               for m in live["target_model_ids"]],
                          "purchase_recommendation_approved": result["purchase_recommendation_approved"]})

    unknown = apply_turn(state, {"wechat_workflow": "unknown", "budget_scope": "unknown"},
                         raw_text="合成回答：微信方式与预算范围还不确定")
    unknown_result = compare_dialogue(unknown)
    unknown_probe = {"next_question_fields": [q["field"] for q in next_questions(unknown, limit=3)],
                     "comparison_questions": unknown_result.get("questions"),
                     "expected": "未决事项保留并给出可操作的下一问或明确暂停状态",
                     "observation": "next_questions空，但比较内部仍有微信方式/预算/地区问题"}

    conflict = apply_turn(state, {"requirements": ["必须彩色打印"]}, raw_text="合成冲突：已确认只需黑白，又新增必须彩色")
    conflict_result = compare_dialogue(conflict)
    conflict_probe = {"status": conflict_result["status"], "expected": "condition_conflict",
                      "expectation_met": conflict_result["status"] == "condition_conflict"}

    future = deepcopy(live["details"])
    for detail in future:
        detail["observed_at"] = "2099-01-01T00:00:00+00:00"
    try:
        future_catalog = enrich_discovered_catalog(view, future)
        future_comp = compare_products(future_catalog, category="printer", required={"wireless": True},
                                       today=TODAY, target_region="CN")
        future_probe = {"expected": "reject_future_detail_time", "rejected": False,
                        "statuses": {r["model_id"]: r["status"] for r in future_comp["candidates"]
                                     if r["model_id"] in live["target_model_ids"]}}
    except ValueError as exc:
        future_probe = {"expected": "reject_future_detail_time", "rejected": True, "error": str(exc)}

    basic = compare_products(enriched, category="printer", required={"wireless": True}, today=TODAY, target_region="CN")
    billing_row = next(r for r in basic["candidates"] if r["model_id"] == "HL-10W")
    billing_probe = {"detail_billing_model": live["details"][0]["billing_model"],
                     "comparison_has_billing_model": "billing_model" in billing_row,
                     "comparison_has_detail_provenance": "manufacturer_detail_evidence" in billing_row,
                     "candidate_unknowns": billing_row["unknowns"]}

    # 真实Python桌面桥接子进程，重放已记录原需求；没有新增真人输入或猜测收货地。
    description = "预算1000元内，每月0–50页，家里只打印黑白，偶尔彩印可在店里打印，想要微信打印，优先兄弟和惠普，可靠耐用"
    values = [description, "0–50", "1000", "", "false", "true", "", "", "", "", "unknown", "", "", "unknown"]
    encoded = [base64.b64encode(v.encode("utf-8")).decode("ascii") for v in values]
    process = subprocess.run([sys.executable, "-m", "shopping_decision.desktop_bridge", *encoded],
                             cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30)
    output = {k: base64.b64decode(v).decode("utf-8") for k, v in
              (line.split("\t", 1) for line in process.stdout.splitlines() if "\t" in line)}
    report = json.loads(output["report_json"])
    comp = report["product_comparison"]
    bridge = {"operation": "real_python_desktop_bridge_subprocess_replay", "new_human_trial": False,
              "returncode": process.returncode, "recommendation_status": report["recommendation"]["status"],
              "eligible_evidence_count": len(report["evidence"]), "candidate_count": len(comp["candidates"]),
              "questions": report["recommendation"]["questions"],
              "candidate_budget_statuses": {r["model_id"]: r["budget_status"] for r in comp["candidates"]},
              "purchase_recommendation_approved": comp["purchase_recommendation_approved"],
              "transactions_enabled": comp["transactions_enabled"]}

    sources = read_json("reports/assessment_sources_20261109.json")
    source_comparisons = []
    for row in sources["rows"]:
        if "parsed" in row:
            previous = next(d for d in live["details"] if d["model_id"] == row["model_id"])
            current = row["parsed"]
            source_comparisons.append({"model_id": row["model_id"],
                                       "same_fact_values_as_executor": {k: v["value"] for k, v in current["facts"].items()} == {k: v["value"] for k, v in previous["facts"].items()},
                                       "same_consumable_ids": [x["model"] for x in current["consumables"]] == [x["model"] for x in previous["consumables"]]})

    result = {"role": "independent_reviewer", "date": TODAY.isoformat(),
              "pairwise_recomputed": {k: pairwise[k] for k in ("case_count", "comparison_units", "matching_units", "mismatches")},
              "refetched_source_comparison": source_comparisons,
              "new_adversarial_extraction_probes": extraction,
              "ordinary_vs_injected": path_rows, "unknown_answer_question_probe": unknown_probe,
              "color_conflict_probe": conflict_probe, "future_detail_probe": future_probe,
              "billing_propagation_probe": billing_probe, "original_case_bridge_replay": bridge,
              "limitations": ["新诊断是合成故障探针，不能与旧单测合并成推荐通过率。", "本轮没有Java GUI操作、平台API授权或真实报价。"],
              "purchase_recommendation_approved": False, "transactions_enabled": False}
    (ROOT / "reports/assessment_probes_20261109.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
