"""P0.7: 厂商公开详情页只读核证；将网页字符串限制成可追溯的型号级主张。

不是用户评论、独立耐用性测评、平台SKU、实时价格或购买许可。
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
from urllib.request import Request, build_opener

from .official_model_discovery import discover
from .official_source_check import _SafeRedirect, MAX_BYTES, is_allowed
from .official_detail_text import VisibleText, supported_phrase
from .product_compare import compare_products, load_official_catalog
from .public_catalog import catalog_from_brother_snapshot

_MODEL = re.compile(r"^HL-[A-Z0-9-]{2,32}$")
_CONSUMABLE = re.compile(r"\b(?:TN|DR|TNB|DRB)[A-Z0-9]{2,8}\b")


def _detail_url(model: str) -> str:
    if not isinstance(model, str) or not _MODEL.fullmatch(model):
        raise ValueError("invalid_manufacturer_model")
    return "https://www.brother.cn/printer/prt/" + model.lower()


def parse_detail(model: str, body: bytes, *, observed_at: datetime) -> dict:
    """仅接受绑定确切型号的 Brother 产品主内容；无确证不补假值。"""
    url = _detail_url(model)
    if observed_at.tzinfo is None or observed_at > datetime.now(timezone.utc):
        raise ValueError("naive_or_future_observation_time")
    if not isinstance(body, bytes) or not 100 <= len(body) <= MAX_BYTES:
        raise ValueError("invalid_detail_body")
    source_text = body.decode("utf-8", "replace")
    parser = VisibleText(source_text)
    parser.feed(source_text)
    # 未支持的隐藏CSS可能影响标题/事实可见性：拒绝该页，避免把隐藏文字升级为确定事实。
    if parser.visibility_uncertain:
        raise ValueError("unresolved_css_hidden_visibility")
    content = parser.text()
    heading = re.search(re.escape(model) + r"\s+" + re.escape(model) +
                        r"\s+黑白激光打印机\b", content, re.IGNORECASE)
    if heading is None:
        raise ValueError("model_page_heading_not_matched")
    # 忽略前面的全站导航和后面的FAQ/相关推荐，避免跨型号/菜单误提取。
    tail = content.find("服务支持", heading.end())
    main = content[heading.start():tail if tail >= 0 else min(len(content), heading.start() + 11000)]
    if len(main) > 12000:
        main = main[:12000]
    facts = {}
    def present(feature: str, label: str, note: str) -> None:
        facts[feature] = {"value": True, "source_url": url,
                          "note": "厂商产品页文字主张（非实机/第三方验证）：" + note + "；原文标识：" + label}
    present("monochrome_print", "黑白激光打印机", "仅证明黑白打印类别")
    facts["color_print"] = {"value": False, "source_url": url,
                            "note": "厂商标注黑白激光打印机；不支持彩印的类别级判断"}
    wireless_tokens = ("支持无线网络连接", "无线/有线网络", "无线、有线网络功能",
                       "网络连接（有线、无线）", "支持2.4GHz/5GHz无线网络打印")
    wlan = supported_phrase(main, wireless_tokens, model=model, feature_hint="无线")
    if wlan is not None:
        present("wireless", wlan, "厂商支持无线连接的主张，未验证用户网络")
    wechat_tokens = ("微信小程序直连，支持远程打印", "微信小程序打印 可实现远程打印",
                     "通过微信小程序可支持远程打印")
    wechat = supported_phrase(main, wechat_tokens, model=model, feature_hint="微信")
    if wechat is not None:
        present("wechat_miniprogram", wechat, "官网声称微信小程序打印，未做设备绑定实验")
    duplex = supported_phrase(main, ("标配A4自动双面打印",), model=model, feature_hint="自动双面")
    if duplex:
        present("auto_duplex", duplex, "厂商自动双面规格")
    billing = (supported_phrase(main, ("按页付费",), model=model, feature_hint="按页付费") is not None
               and supported_phrase(main, ("购买打印页数",), model=model, feature_hint="购买打印页数") is not None)
    if billing:
        present("pay_per_page_consumables", "按页付费/购买打印页数", "打印页数收费模式，不能假定耗材免费等于无长期成本")
    before_spec = main.split("产品规格", 1)[0]
    consumables = []
    if "相关耗材" in before_spec:
        segment = before_spec.split("相关耗材", 1)[1]
        for code in dict.fromkeys(_CONSUMABLE.findall(segment)):
            consumables.append({"model": code, "source_url": url,
                                "note": "仅核对厂商页面出现的耗材型号，未核实零售包装/价格"})
    return {
        "model_id": model, "source_url": url,
        "observed_at": observed_at.isoformat(),
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "response_bytes": len(body), "fact_origin": "manufacturer_public_detail",
        "facts": facts, "consumables": consumables,
        "billing_model": "buy_print_pages_to_claim_consumables" if billing else "unknown",
        "limitations": ["厂商文字主张不等于第三方耐用性验证",
                        "未证实的功能保持未知；未获得零售SKU、地区当前价格、实际库存",
                        "只有绑定型号的详情页证据，不证明该机符合购买预算"],
    }


def archive_public_detail(model: str, body: bytes, *, archive_root: Path | None = None) -> str:
    """保存当前公开官网HTML用于复算；原始网页仅存本地 data/raw（git忽略）。"""
    _detail_url(model)
    if not isinstance(body, bytes) or not 100 <= len(body) <= MAX_BYTES:
        raise ValueError("invalid_archivable_detail")
    digest = hashlib.sha256(body).hexdigest()
    root = archive_root or Path(__file__).resolve().parent.parent / "data/raw/p0_8_official_details"
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"{digest}.html"
    if out.exists():
        if out.read_bytes() != body:
            raise ValueError("source_digest_collision_or_file_conflict")
    else:
        with out.open("xb") as f:
            f.write(body)
    return str(out)


def fetch_detail(model: str, *, timeout: float = 7.0) -> dict:
    if not 1 <= timeout <= 15:
        raise ValueError("invalid_timeout")
    url = _detail_url(model)
    if not is_allowed(url):
        raise ValueError("unsafe_url")
    request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
    with build_opener(_SafeRedirect()).open(request, timeout=timeout) as response:
        if response.url != url or "text/html" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("unexpected_detail_response")
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("detail_too_large")
    record = parse_detail(model, body, observed_at=datetime.now(timezone.utc))
    record["raw_html_local_path"] = archive_public_detail(model, body)
    return record


_REVIEWED_P08_REPLAY = {
    # 固定三份历史原文、已核字段、套餐和原始观察时刻；不能用可编辑清单刷新历史证据。
    # 四元组：SHA-256、已核正向字段、套餐模式、P0.8 原始观察时刻（UTC）。
    "HL-10W": ("3d3a08760305db1f22c82cac514216f7d33646791775ab2490709871b2e04dff",
               frozenset(("monochrome_print", "wireless", "wechat_miniprogram", "pay_per_page_consumables")),
               "buy_print_pages_to_claim_consumables", "2026-11-09T14:01:03.133068+00:00"),
    "HL-B2188DW": ("ee0c6963a4b2962d71911010aac53bf949736e8435d701be6fa5a393295d75fb",
                   frozenset(("monochrome_print", "wireless", "wechat_miniprogram", "auto_duplex")),
                   "unknown", "2026-11-09T14:01:03.875727+00:00"),
    "HL-B2158W": ("37fba167920c15d0be31caedfdfd057248d6ab86f659b0fe7118f82688ddc20a",
                  frozenset(("monochrome_print", "wireless", "wechat_miniprogram")),
                  "unknown", "2026-11-09T14:01:04.511646+00:00"),
}


def _require_frozen_observation(model: str, observed_at: datetime) -> None:
    """历史审阅资格绑定原观察事件，而不是调用方可自行修改的清单时间。"""
    reviewed = _REVIEWED_P08_REPLAY.get(model)
    if reviewed is None:
        raise ValueError("detail_not_in_frozen_reviewed_set")
    frozen_at = datetime.fromisoformat(reviewed[3])
    if (observed_at.tzinfo is None
            or observed_at.astimezone(timezone.utc) != frozen_at):
        raise ValueError("reviewed_detail_observation_time_mismatch")


def enrich_discovered_catalog(view: dict, detail_records: list[dict], *,
                              reviewed_local_replay: bool = False) -> dict:
    """新网页仅保留待核主张；只有固定哈希、原件重读和字段核对的历史回放可进入硬条件比较。"""
    updated = deepcopy(view["catalog"])
    found = {x["model_id"]: x for x in updated["products"]}
    old = set(view.get("old_model_ids", []))
    seen = set()
    for d in detail_records:
        model = d.get("model_id")
        if model in seen or model not in found or model in old:
            raise ValueError("unrecognized_or_duplicate_detail")
        seen.add(model)
        if (d.get("source_url") != _detail_url(model)
                or not re.fullmatch(r"[0-9a-f]{64}", str(d.get("response_sha256", "")))
                or d.get("fact_origin") != "manufacturer_public_detail"):
            raise ValueError("invalid_detail_provenance")
        for key, fact in d["facts"].items():
            if (key not in {"monochrome_print", "color_print", "wireless",
                            "wechat_miniprogram", "auto_duplex", "pay_per_page_consumables"}
                    or type(fact.get("value")) is not bool
                    or fact.get("source_url") != d["source_url"]):
                raise ValueError("untrusted_detail_fact")
        if not (d["facts"].get("monochrome_print", {}).get("value") is True
                and d["facts"].get("color_print", {}).get("value") is False):
            raise ValueError("detail_category_not_verified")
        # 详情的获取时间是独立证据，不能被目录快照日期替代或伪造为未来。
        try:
            detail_at = datetime.fromisoformat(str(d["observed_at"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid_detail_observed_at") from exc
        if (detail_at.tzinfo is None or detail_at > datetime.now(timezone.utc)
                or detail_at.year < 2020):
            raise ValueError("future_or_invalid_detail_observed_at")
        if d.get("billing_model") not in ("buy_print_pages_to_claim_consumables", "unknown"):
            raise ValueError("invalid_billing_mode")
        if not isinstance(d.get("consumables"), list):
            raise ValueError("invalid_consumables")
        item = found[model]
        # 未复核的新网页即使带有厂商域名、型号及哈希，也只能是“待核主张”，
        # 不能把猜出的 true/false 注入 facts 让比较器错误判断硬条件。
        if not reviewed_local_replay:
            item["manufacturer_claim_pending_review"] = {
                "status": "awaiting_per_field_review",
                "source_url": d["source_url"],
                "response_sha256": d["response_sha256"],
                "observed_at": detail_at.astimezone(timezone.utc).isoformat(),
                "claim_fields": sorted(d["facts"]),
            }
            continue
        reviewed = _REVIEWED_P08_REPLAY.get(model)
        if reviewed is None or d["response_sha256"] != reviewed[0]:
            raise ValueError("detail_not_in_frozen_reviewed_set")
        _require_frozen_observation(model, detail_at)
        # 只有固定三份原件的字节哈希、逐字段名单、原观察时刻和抽取结果同时匹配才能准入。
        source_path = (Path(__file__).resolve().parent.parent / "data/raw/p0_8_official_details"
                       / (reviewed[0] + ".html"))
        body = source_path.read_bytes()
        if hashlib.sha256(body).hexdigest() != reviewed[0]:
            raise ValueError("reviewed_detail_raw_hash_mismatch")
        recovered = parse_detail(model, body, observed_at=detail_at)
        positives = {key for key, fact in recovered["facts"].items() if fact["value"] is True}
        # Z 与 +00:00 表示同一瞬间；比较记录时只规范化时间写法，不放宽事实字段。
        normalized_input = deepcopy(d)
        normalized_input["observed_at"] = detail_at.isoformat()
        if (recovered != normalized_input or positives != reviewed[1]
                or d["billing_model"] != reviewed[2]):
            raise ValueError("reviewed_detail_fact_binding_mismatch")
        item["facts"].update(deepcopy(d["facts"]))
        item["consumables"] = deepcopy(d["consumables"])
        item["manufacturer_detail_evidence"] = {
            "observed_at": detail_at.astimezone(timezone.utc).isoformat(),
            "source_url": d["source_url"], "response_sha256": d["response_sha256"],
            "billing_model": d["billing_model"], "admission": "frozen_p0_8_local_field_review"}
    return updated


def load_reviewed_local_replay() -> dict:
    """从P0.8逐型号原始HTML按哈希重建详情；不再读取P0.7无原文对应的旧摘要。"""
    from .public_catalog import _read_bounded_json, BROTHER_SNAPSHOT

    root = Path(__file__).resolve().parent.parent
    report_path = root / "reports/p0_8_refetched_official_sources_20261109.json"
    if not report_path.is_file():
        raise FileNotFoundError("p0_8_source_manifest_not_found")
    manifest = _read_bounded_json(report_path, limit=100_000)
    if manifest.get("operation") != "p0_8_read_only_official_source_recheck":
        raise ValueError("unrecognized_p0_8_source_manifest")
    rows = manifest.get("models")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("incomplete_p0_8_source_manifest")

    details = []
    seen = set()
    archive = root / "data/raw/p0_8_official_details"
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid_p0_8_source_record")
        model = row.get("model_id")
        digest = row.get("response_sha256")
        if (not isinstance(model, str) or model in seen
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or row.get("source_url") != _detail_url(model)):
            raise ValueError("invalid_p0_8_source_identity")
        seen.add(model)
        raw_path = archive / (digest + ".html")
        if not raw_path.is_file():
            raise FileNotFoundError("p0_8_raw_detail_missing")
        body = raw_path.read_bytes()
        if hashlib.sha256(body).hexdigest() != digest:
            raise ValueError("p0_8_raw_detail_hash_mismatch")
        try:
            observed_at = datetime.fromisoformat(str(row["observed_at"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid_p0_8_source_observed_at") from exc
        _require_frozen_observation(model, observed_at)
        detail = parse_detail(model, body, observed_at=observed_at)
        positive = [key for key, fact in detail["facts"].items() if fact["value"] is True]
        if (detail["source_url"] != row["source_url"]
                or positive != row.get("extracted_positive_features")
                or detail["billing_model"] != row.get("billing_model")):
            raise ValueError("p0_8_source_replay_mismatch")
        details.append(detail)

    known = load_official_catalog()
    view = catalog_from_brother_snapshot(_read_bounded_json(BROTHER_SNAPSHOT),
                                         known_catalog=known, now=datetime.now(timezone.utc))
    view["old_model_ids"] = [p["model_id"] for p in known["products"]]
    catalog = enrich_discovered_catalog(view, details, reviewed_local_replay=True)
    catalog["local_evidence_mode"] = "recorded_manufacturer_detail_replay_no_network"
    catalog["local_evidence_manifest"] = "reports/p0_8_refetched_official_sources_20261109.json"
    return catalog


def live_compare(*, limit: int = 3, required: dict[str, bool] | None = None,
                 budget_max_cny: int | None = 1000) -> dict:
    """目录->发现未预置型号->逐详情抽取->同一比较器；失败保留为失败。"""
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError("invalid_limit")
    required = required if required is not None else {
        "monochrome_print": True, "wireless": True, "wechat_miniprogram": True}
    snapshot = discover()
    known = load_official_catalog()
    discovered = catalog_from_brother_snapshot(
        snapshot, known_catalog=known, now=datetime.now(timezone.utc))
    discovered["old_model_ids"] = [p["model_id"] for p in known["products"]]
    targets = [r["model_id"] for r in snapshot["models"]
               if r["model_id"] not in set(discovered["old_model_ids"])][:limit]
    records, failures = [], []
    for model in targets:
        try:
            records.append(fetch_detail(model))
        except (ValueError, OSError, TimeoutError) as exc:
            failures.append({"model_id": model, "error_type": type(exc).__name__})
    catalog = enrich_discovered_catalog(discovered, records)
    comparison = compare_products(
        catalog, category="printer", required=required, budget_max_cny=budget_max_cny,
        target_region="CN")
    for candidate in comparison["candidates"]:
        candidate["purchasable"] = False
    return {
        "operation": "p0_7_live_discovery_detail_and_comparison",
        "discovery": {"source_url": snapshot["source_url"],
                      "response_sha256": snapshot["response_sha256"],
                      "discovered_at": snapshot["discovered_at"],
                      "found_count": snapshot["found_count"],
                      "new_model_count": snapshot["new_model_count"]},
        "target_model_ids": targets, "details": records, "fetch_failures": failures,
        "comparison": comparison,
        "purchase_recommendation_approved": False, "transactions_enabled": False,
        "live_price_verified": 0, "independent_validation": "pending",
    }


def main() -> None:
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    result = live_compare(limit=args.limit)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
