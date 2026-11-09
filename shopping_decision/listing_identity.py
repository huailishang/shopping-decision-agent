"""跨平台销售项的保守型号校验（只读、离线）。

只检验身份线索及误绑；既不调用业务 API，也不批准真实报价或购买。
标题命中型号依然只是候选，不能代替平台实际所售配置的核验。
"""
from __future__ import annotations

from datetime import datetime, timezone
import re

PLATFORMS = frozenset({"JD_UNION", "TAOBAO_TBK"})


def _has_exact_anchor(title: str, alias: str) -> bool:
    # 中文品牌名常与型号紧邻；只禁止ASCII型号字母/数字的延长。
    return bool(re.search(r"(?<![A-Za-z0-9_-])" + re.escape(alias)
                          + r"(?![A-Za-z0-9_-])", title, re.I))


def assess_listing_identity(listing: dict, *, expected_model_id: str,
                            known_aliases: dict[str, list[str]],
                            now: datetime | None = None) -> dict:
    """以审核过的厂商型号别名识别商品标题；不跨平台转换 itemId/SKU。"""
    result = {"status": "needs_verification", "model_id": expected_model_id,
              "listing_key": None, "identity_verified": False,
              "quote_verified": False, "purchasable": False, "reasons": []}
    if (not isinstance(listing, dict) or not isinstance(known_aliases, dict)
            or expected_model_id not in known_aliases):
        result.update(status="invalid_input", reasons=["missing_model_registry_or_listing"])
        return result
    platform, item_id = listing.get("platform"), listing.get("platform_item_id")
    if (platform not in PLATFORMS or not isinstance(item_id, str)
            or not item_id.strip() or len(item_id) > 128):
        result.update(status="invalid_input", reasons=["unsupported_platform_or_item_id"])
        return result
    result["listing_key"] = {"platform": platform, "platform_item_id": item_id}
    title = listing.get("displayed_title")
    if not isinstance(title, str) or not title.strip():
        result.update(status="invalid_input", reasons=["missing_displayed_title"])
        return result
    if not isinstance(listing.get("source_id"), str) or not listing["source_id"].strip():
        result.update(status="invalid_input", reasons=["missing_source_id"])
        return result
    try:
        observed = datetime.fromisoformat(listing["observed_at"])
        current = now or datetime.now(timezone.utc)
        if observed.tzinfo is None or observed > current:
            raise ValueError("observation timestamp invalid")
    except (KeyError, ValueError, TypeError):
        result.update(status="invalid_input", reasons=["missing_or_future_observation_time"])
        return result

    matched = set()
    for model_id, aliases in known_aliases.items():
        if not isinstance(aliases, list) or not aliases:
            result.update(status="invalid_input", reasons=["invalid_model_alias_registry"])
            return result
        if any(isinstance(a, str) and a.strip() and _has_exact_anchor(title, a) for a in aliases):
            matched.add(model_id)
    selected = listing.get("selected_model_id")
    if (len(matched) > 1 or (selected and selected != expected_model_id)
            or (matched and expected_model_id not in matched)):
        result.update(status="model_conflict", reasons=["wrong_or_multiple_model_anchors"])
        return result
    if not matched:
        result["reasons"].append("model_title_anchor_missing")
    # 标题可能是“适用于该型号的粉盒/硒鼓”，型号命中并非打印机本体。
    if listing.get("item_kind") not in (None, "printer"):
        result.update(status="non_printer_listing", reasons=["accessory_or_non_printer"])
        return result
    if listing.get("item_kind") is None:
        result["reasons"].append("missing_platform_item_kind")
    if not isinstance(listing.get("seller_id"), str) or not listing["seller_id"].strip():
        result["reasons"].append("seller_unknown")
    if listing.get("variant_or_bundle") != "single_new_printer":
        result["reasons"].append("variant_or_bundle_requires_verification")
    if not selected:
        result["reasons"].append("selected_model_requires_platform_detail")
    if not isinstance(listing.get("region"), str) or not listing["region"].strip():
        result["reasons"].append("region_unknown")
    if not result["reasons"]:
        result.update(status="candidate_unverified", reasons=["authorization_and_source_not_verified"])
    return result
