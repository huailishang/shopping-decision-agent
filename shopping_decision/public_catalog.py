"""P0.6: 公开厂商目录快照 -> 型号候选 -> 既有三态事实比较。

仅操作经过记录的厂商型号目录快照；未授权商品 API、实时价格/库存和交易始终关闭。
目录记录证明型号/目录标签存在，不证明微信、无线、耐用性或具体销售配置。
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
import json
import re

from .product_compare import compare_products, load_official_catalog


ROOT = Path(__file__).resolve().parent.parent
BROTHER_SNAPSHOT = ROOT / "reports" / "p0_2_fallback_official_discovery_20261107.json"
_MODEL = re.compile(r"^HL-[A-Z0-9-]{2,32}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _read_bounded_json(path: Path, limit: int = 160_000) -> dict:
    if path.stat().st_size > limit:
        raise ValueError("snapshot_too_large")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("snapshot_not_object")
    return data


def catalog_from_brother_snapshot(snapshot: dict, *, known_catalog: dict,
                                  now: datetime | None = None) -> dict:
    """从真实来源目录推导待核型号，不要把目录链接冒充商城 SKU。

    只对未进入原事实表的型号，依据网站“黑白激光”标签记录黑白类别；
    Wi-Fi/微信/耗材等逐型号属性保持未知。完整来源时间使用原抓取时间。
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("invalid_reference_time")
    if (not isinstance(snapshot, dict)
            or snapshot.get("operation") != "read_only_model_discovery"
            or snapshot.get("provider") != "Brother CN"
            or snapshot.get("source_url") != "https://www.brother.cn/printer/prt"
            or not _DIGEST.fullmatch(str(snapshot.get("response_sha256", "")))
            or snapshot.get("catalog_complete") is not False):
        raise ValueError("untrusted_or_incomplete_snapshot_metadata")
    captured_text = snapshot.get("discovered_at")
    if not isinstance(captured_text, str):
        raise ValueError("missing_capture_time")
    try:
        captured = datetime.fromisoformat(captured_text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_capture_time") from exc
    if captured.tzinfo is None or captured > now or captured.year < 2020:
        raise ValueError("invalid_capture_time")
    models = snapshot.get("models")
    if (not isinstance(models, list) or len(models) > 100 or
            snapshot.get("found_count") != len(models)):
        raise ValueError("invalid_model_list")
    if (not isinstance(known_catalog, dict)
            or not isinstance(known_catalog.get("products"), list)
            or known_catalog.get("market_region") != "CN"
            or known_catalog.get("source_kind") != "manufacturer_public_pages"):
        raise ValueError("invalid_known_catalog")
    original_by_id = {p["model_id"]: p for p in known_catalog["products"]}
    by_model = {}
    for row in models:
        if not isinstance(row, dict):
            raise ValueError("invalid_model_entry")
        model = row.get("model_id")
        if not isinstance(model, str) or not _MODEL.fullmatch(model):
            raise ValueError("invalid_model_id")
        expected_url = f"https://www.brother.cn/printer/prt/{model.lower()}"
        if (row.get("official_url") != expected_url or row.get("brand") != "Brother"
                or row.get("category") != "printer"
                or row.get("category_hint") != "mono_laser_from_website_label"
                or row.get("status") != "discovered_unverified_facts"
                or row.get("fact_confidence") != "model_and_official_category_label_only"):
            raise ValueError("untrusted_model_provenance")
        if model in by_model:
            raise ValueError("duplicate_model_identity")
        if model in original_by_id:
            # 旧事实的证据时间不可被昨日新目录刷新。
            p = original_by_id[model]
            if p["official_url"] != expected_url:
                raise ValueError("existing_model_source_conflict")
            by_model[model] = p
        else:
            by_model[model] = {
                "model_id": model, "brand": "Brother", "category": "printer",
                "name": f"Brother {model}（官网目录发现，详细规格待核）",
                "official_url": expected_url,
                "facts": {
                    "monochrome_print": {
                        "value": True, "source_url": snapshot["source_url"],
                        "note": "仅由厂商黑白激光产品目录标签支持，尚非独立型号参数复核"},
                    "color_print": {
                        "value": False, "source_url": snapshot["source_url"],
                        "note": "仅由黑白激光品类标签推断，待详情核查"},
                },
                "manufacturer_suggested_retail_cny": None,
                "independent_durability_test": False,
            }
    # 原目录时间和新目录时间保守取较早者，不能冒充全部事实都当天采集。
    known_date = date.fromisoformat(known_catalog["recorded_on"])
    recorded = min(known_date, captured.date())
    public_catalog = {
        "schema_version": 1, "source_kind": "manufacturer_public_pages",
        "recorded_on": recorded.isoformat(), "market_region": "CN",
        "catalog_discovery": "brother_public_index_historical_snapshot",
        "products": list(by_model.values()),
    }
    return {
        "status": "manufacturer_model_candidates_with_partial_facts",
        "source_url": snapshot["source_url"], "source_sha256": snapshot["response_sha256"],
        "source_observed_at": captured.isoformat(), "source_replayed_offline": True,
        "source_complete": False, "discovered_count": len(by_model),
        "new_model_count": sum(mid not in original_by_id for mid in by_model),
        "catalog": public_catalog,
        "quotes_verified": 0, "transactions_enabled": False,
        "limitations": [
            "历史官网目录快照回放，不是本轮联网实时检索，也不证明全市场覆盖",
            "厂商类别标签不等于逐型号无线/微信/扫描/耗材/售后已经证实",
            "不携带电商SKU、库存、用户折扣或地区实时到手价",
        ],
    }


def compare_public_snapshot(*, required: dict[str, bool], preferred: dict[str, bool] | None = None,
                            budget_max_cny: int | None = None,
                            snapshot_path: Path = BROTHER_SNAPSHOT,
                            known_path: Path | None = None,
                            today: date | None = None) -> dict:
    """用原 compare_products 的三态比较语义进行公开型号对照，不签购买结论。"""
    snapshot = _read_bounded_json(snapshot_path)
    known = load_official_catalog(known_path) if known_path else load_official_catalog()
    today = today or date.today()
    view = catalog_from_brother_snapshot(
        snapshot, known_catalog=known,
        now=datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc))
    result = compare_products(view["catalog"], category="printer", required=required,
                              preferred=preferred or {}, budget_max_cny=budget_max_cny,
                              today=today, target_region="CN")
    for row in result["candidates"]:
        row["source_kind"] = "manufacturer_model_not_marketplace_listing"
        row["source_observed_at"] = view["source_observed_at"]
        row["original_fact_catalog_model"] = any(
            p["model_id"] == row["model_id"] for p in known["products"])
        row["purchasable"] = False
    return {
        "operation": "public_catalog_model_comparison",
        "discovery": {k: v for k, v in view.items() if k != "catalog"},
        "comparison": result, "approved_purchase_count": 0,
        "purchase_recommendation_approved": False, "transactions_enabled": False,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="历史厂商目录型号发现并进入原三态比较（不联网）")
    parser.add_argument("--budget", type=int, default=1000)
    parser.add_argument("--require-wireless", action="store_true")
    parser.add_argument("--require-wechat", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    required = {"monochrome_print": True}
    if args.require_wireless:
        required["wireless"] = True
    if args.require_wechat:
        required["wechat_miniprogram"] = True
    result = compare_public_snapshot(required=required, budget_max_cny=args.budget)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
