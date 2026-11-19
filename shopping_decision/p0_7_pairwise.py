"""P0.7 对照：人工核实事实 vs 现场发现后自动核证；只做型号技术事实比较。"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, time, timezone
from pathlib import Path

from .product_compare import compare_products, load_official_catalog
from .public_catalog import catalog_from_brother_snapshot, _read_bounded_json, BROTHER_SNAPSHOT
from .p0_7_official_details import enrich_discovered_catalog

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = [
    ("home_basic_budget", {"monochrome_print": True, "wireless": True, "wechat_miniprogram": True}, {}, 1000),
    ("home_basic_spec_only", {"monochrome_print": True, "wireless": True, "wechat_miniprogram": True}, {}, None),
    ("color_needed", {"color_print": True}, {}, 1000),
    ("auto_duplex", {"monochrome_print": True, "auto_duplex": True}, {}, None),
    ("page_plan", {"pay_per_page_consumables": True}, {}, None),
    ("scan_requirement", {"scan": True}, {}, None),
    ("wireless_not_wanted", {"wireless": False}, {}, None),
    ("wechat_not_wanted", {"wechat_miniprogram": False}, {}, None),
    ("prefer_wireless", {"monochrome_print": True}, {"wireless": True}, None),
    ("durability_unknown", {"independent_durability_test": True}, {}, None),
    ("monochrome_not_wanted", {"monochrome_print": False}, {}, None),
    ("zero_budget_unknown", {"monochrome_print": True}, {}, 0),
    ("duplex_not_wanted", {"auto_duplex": False}, {}, None),
    ("page_plan_not_wanted", {"pay_per_page_consumables": False}, {}, None),
    ("prefer_wechat", {"monochrome_print": True}, {"wechat_miniprogram": True}, None),
    ("double_hard", {"wechat_miniprogram": True, "auto_duplex": True}, {}, None),
]


def run_pairwise(live: dict, manual: dict, *, today: date) -> dict:
    if live.get("operation") != "p0_7_live_discovery_detail_and_comparison":
        raise ValueError("wrong_live_report")
    if manual.get("source_kind") != "manufacturer_public_pages" or manual.get("market_region") != "CN":
        raise ValueError("wrong_manual_baseline")
    targets = live.get("target_model_ids")
    details = live.get("details")
    if (not isinstance(targets, list) or not 1 <= len(targets) <= 5
            or not all(isinstance(x, str) for x in targets)
            or len(set(targets)) != len(targets)):
        raise ValueError("invalid_live_target_models")
    if (not isinstance(details, list)
            or any(not isinstance(d, dict) or not isinstance(d.get("model_id"), str)
                   for d in details)):
        raise ValueError("invalid_live_detail_records")
    detail_ids = [d["model_id"] for d in details]
    if (live.get("fetch_failures") or len(detail_ids) != len(targets)
            or set(detail_ids) != set(targets) or len(set(detail_ids)) != len(details)):
        raise ValueError("incomplete_live_detail_coverage")

    # 旧目录用于重建型号身份，现场详情来自本轮 live 记录；不是完整当天网页重放。
    known = load_official_catalog()
    historical = catalog_from_brother_snapshot(
        _read_bounded_json(BROTHER_SNAPSHOT), known_catalog=known,
        now=datetime.combine(today, time.max, tzinfo=timezone.utc))
    historical["old_model_ids"] = [p["model_id"] for p in known["products"]]
    enriched = enrich_discovered_catalog(historical, details)
    auto_by_id = {p["model_id"]: p for p in enriched["products"]}
    manually_by_id = {p["model_id"]: p for p in manual["products"]}
    common = [m for m in targets if m in auto_by_id and m in manually_by_id]
    if len(common) != len(targets):
        raise ValueError("incomplete_manual_or_discovery_coverage")
    auto_catalog = {**enriched, "products": [auto_by_id[x] for x in common]}
    manual_catalog = {**manual, "products": [manually_by_id[x] for x in common]}

    records = []
    for case_id, required, preferred, budget in SCENARIOS:
        a = compare_products(manual_catalog, category="printer", required=required,
                             preferred=preferred, budget_max_cny=budget, today=today,
                             target_region="CN")
        b = compare_products(auto_catalog, category="printer", required=required,
                             preferred=preferred, budget_max_cny=budget, today=today,
                             target_region="CN")
        a_rows = {r["model_id"]: r for r in a["candidates"]}
        b_rows = {r["model_id"]: r for r in b["candidates"]}
        for mid in common:
            aa, bb = a_rows[mid], b_rows[mid]
            fields = ("required_met", "required_unknown", "required_failed",
                      "preferred_met", "preferred_unknown", "preferred_failed",
                      "budget_status", "status")
            equal = all(aa[k] == bb[k] for k in fields)
            records.append({"scenario": case_id, "model": mid, "matching": equal,
                            "manual_status": aa["status"], "automatic_status": bb["status"],
                            "manual_required": {k: aa[k] for k in fields[:3]},
                            "automatic_required": {k: bb[k] for k in fields[:3]}})
    return {
        "operation": "p0_7_manual_vs_auto_fact_comparison", "date": today.isoformat(),
        "source_report": "2026-11-09现场联网取证记录（不是再次联网）",
        "candidate_identity_reconstruction": "2026-11-07历史目录+2026-11-09现场详情ID",
        "live_catalog_full_snapshot_replay": False,
        "case_count": len(SCENARIOS), "common_models": common,
        "comparison_units": len(records), "matching_units": sum(r["matching"] for r in records),
        "mismatches": [r for r in records if not r["matching"]],
        "records": records, "manual_is_independently_reviewed": False,
        "purchase_recommendation_approved": False, "transactions_enabled": False,
        "limitations": ["相同官网的两条事实抽取路径对照，不能当成独立耐用性或商品质量评测",
                        "没有商城SKU、地区实时报价、库存或可购买建议资格"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", type=Path, default=ROOT / "reports/p0_7_live_discovery_20261109.json")
    parser.add_argument("--manual", type=Path, default=ROOT / "knowledge/p0_7_manual_printer_baseline_20261109.json")
    parser.add_argument("--out", type=Path, default=ROOT / "reports/p0_7_pairwise_20261109.json")
    args = parser.parse_args()
    live = json.loads(args.live.read_text(encoding="utf-8"))
    manual = json.loads(args.manual.read_text(encoding="utf-8"))
    output = run_pairwise(live, manual, today=date.fromisoformat(manual["recorded_on"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k not in ("records", "mismatches")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
