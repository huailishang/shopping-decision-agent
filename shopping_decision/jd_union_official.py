"""京东联盟关键词商品查询：历史 JOS v1 请求构造、官方响应离线导入。

只处理用户已合法取得、主动提供的业务响应 JSON；无网络调用、无环境密钥读取。
业务接口权限、现行平台网关与应用用途必须先于任何真实请求完成核验。
“商品被搜索到”不代表用户地区到手价/库存/所选套餐已核价。
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, HTTPRedirectHandler, build_opener

JD_METHOD = "jd.union.open.goods.query"
WRAPPER_KEY = "jd_union_open_goods_query_responce"  # 官方旧 SDK 拼写就是 responce
CST = timezone(timedelta(hours=8))
_SKU = re.compile(r"[0-9]{5,20}")
MAX_SNAPSHOT_BYTES = 256_000


def _timestamp(value: str, *, now: datetime | None = None) -> datetime:
    if not isinstance(value, str):
        raise ValueError("observation_timestamp_invalid")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("observation_timestamp_invalid") from exc
    clock = now or datetime.now(timezone.utc)
    if stamp.tzinfo is None or clock.tzinfo is None or stamp > clock or stamp.year < 2000:
        raise ValueError("observation_timestamp_invalid")
    return stamp.astimezone(timezone.utc)


def build_legacy_jos_goods_query_form(
    keyword: str, *, app_key: str, app_secret: str,
    at: datetime, page_index: int = 1, page_size: int = 3,
) -> dict[str, str]:
    """仅构造历史 JOS v1 的签名表单，不调用接口；调用前必须重新核准现行文档。

    旧 SDK 使用 secret + 按 key 升序逐对连接的系统/业务参数 + secret，MD5大写。
    返回表单不包含 app_secret，但包含 AppKey 和可识别的签名：禁止输出到日志。
    """
    if (not isinstance(keyword, str) or not keyword.strip() or len(keyword.strip()) > 100
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in keyword)):
        raise ValueError("invalid_keyword")
    for value in (app_key, app_secret):
        if not isinstance(value, str) or not value or len(value) > 256 or value.strip() != value:
            raise ValueError("invalid_credentials")
    if (not isinstance(at, datetime) or at.tzinfo is None or type(page_index) is not int
            or type(page_size) is not int or not 1 <= page_index <= 20 or not 1 <= page_size <= 10):
        raise ValueError("invalid_request_parameters")
    goods = {"goodsReqDTO": {"keyword": keyword.strip(), "pageIndex": page_index, "pageSize": page_size}}
    fields = {
        "method": JD_METHOD, "app_key": app_key,
        "timestamp": at.astimezone(CST).strftime("%Y-%m-%d %H:%M:%S"),
        "format": "json", "v": "1.0", "sign_method": "md5",
        "360buy_param_json": json.dumps(goods, ensure_ascii=False, separators=(",", ":")),
    }
    material = app_secret + "".join(key + fields[key] for key in sorted(fields)) + app_secret
    fields["sign"] = hashlib.md5(material.encode("utf-8")).hexdigest().upper()
    return fields


def _sku_string(raw: object) -> str | None:
    if type(raw) is int:
        raw = str(raw)
    if not isinstance(raw, str) or not _SKU.fullmatch(raw):
        return None
    return raw


def import_goods_query_response(
    response: dict, *, keyword: str, observed_at: str,
    now: datetime | None = None, max_items: int = 10,
) -> dict:
    """以 fail-closed 方式读取官方响应形状。

    这里的响应是外部离线快照，不能证明它真实来自京东 API；
    即使能正常解析，也只能产生 unverified 候选，不批准价格或交易。
    """
    base = {
        "operation": "offline_jd_union_response_import",
        "platform": "JD_UNION_IMPORT_UNVERIFIED",
        "status": "invalid_response", "items": [], "rejected_count": 0,
        "warnings": [], "authorized_api_calls": 0,
        "verified_quote_count": 0, "purchase_recommendation_approved": False,
        "transactions_enabled": False,
    }
    if (not isinstance(response, dict) or not isinstance(keyword, str)
            or not keyword.strip() or len(keyword.strip()) > 100
            or type(max_items) is not int or not 1 <= max_items <= 20):
        base["warnings"].append("invalid_input")
        return base
    try:
        observed = _timestamp(observed_at, now=now)
    except ValueError:
        base["warnings"].append("invalid_observed_at")
        return base
    base.update(keyword=keyword.strip(), observed_at=observed.isoformat(),
                source_assurance="offline_import_not_platform_authorization",
                provenance_sha256=hashlib.sha256(
                    json.dumps(response, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")).hexdigest())
    if "error_response" in response:
        base.update(status="api_error", warnings=["gateway_error_no_products"])
        return base
    envelope = response.get(WRAPPER_KEY)
    if not isinstance(envelope, dict):
        base["warnings"].append("missing_expected_jd_wrapper")
        return base
    outer = envelope.get("code")
    if type(outer) not in (str, int) or str(outer) not in ("0", "200"):
        base.update(status="api_error", warnings=["gateway_response_not_success"])
        return base
    nested = envelope.get("queryResult")
    # 旧 JOS/SDK 为字符串包一层 JSON；其他形状不能猜字段。
    if not isinstance(nested, str) or len(nested.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
        base["warnings"].append("nested_result_not_json_string")
        return base
    try:
        body = json.loads(nested)
    except json.JSONDecodeError:
        base["warnings"].append("nested_json_invalid")
        return base
    if not isinstance(body, dict) or type(body.get("code")) not in (str, int):
        base["warnings"].append("business_result_shape_invalid")
        return base
    if str(body["code"]) not in ("200", "0"):
        base.update(status="api_error", warnings=["business_response_not_success"])
        return base
    items = body.get("data")
    if not isinstance(items, list) or len(items) > 100:
        base["warnings"].append("data_not_bounded_list")
        return base
    base["total_count_reported"] = (
        body.get("totalCount") if type(body.get("totalCount")) is int else None)
    if len(items) > max_items:
        base["warnings"].append("sample_truncated")
    seen = {}
    for raw in items[:max_items]:
        if not isinstance(raw, dict):
            base["rejected_count"] += 1
            continue
        sku = _sku_string(raw.get("skuId"))
        title = raw.get("skuName")
        if sku is None or not isinstance(title, str) or not title.strip() or len(title) > 500:
            base["rejected_count"] += 1
            continue
        shop = raw.get("shopInfo")
        shop = shop if isinstance(shop, dict) else {}
        shop_name = shop.get("shopName")
        shop_name = shop_name[:100] if isinstance(shop_name, str) else None
        shop_id = _sku_string(shop.get("shopId"))
        if sku in seen:
            previous = seen[sku]
            if previous["displayed_title"] != title.strip() or previous["seller_hint"] != shop_name:
                previous["status"] = "conflicting_snapshot_entries"
                previous["warnings"].append("duplicate_sku_conflict")
            continue
        result = {
            "platform": "JD_UNION_IMPORT_UNVERIFIED",
            "platform_namespace": "JD_UNION", "platform_item_id": sku,
            "canonical_url": f"https://item.jd.com/{sku}.html",
            "displayed_title": title.strip(), "seller_hint": shop_name,
            "seller_id_hint": shop_id,
            "source_id": f"jd_union_goods_query_snapshot:{sku}",
            "observed_at": observed.isoformat(),
            "source_assurance": "unverified_imported_snapshot",
            "status": "discovered_unverified",
            "identity_verified": False, "quote_verified": False, "purchasable": False,
            "price_field_exists_but_not_authorized_quote": isinstance(raw.get("priceInfo"), dict),
            "missing_fields": [
                "selected_model", "kind_and_bundle", "selected_sku_variant",
                "seller_verification", "delivery_region_and_stock",
                "coupons_and_shipping", "authorized_fresh_quote"
            ], "warnings": ["affiliate_goods_pool_not_entire_marketplace"],
        }
        seen[sku] = result
        base["items"].append(result)
    base["status"] = "candidates_unverified" if base["items"] else "no_valid_candidates"
    if ((now or datetime.now(timezone.utc)) - observed).days > 1:
        base["warnings"].append("snapshot_age_over_one_day")
    return base


class _DenyRedirect(HTTPRedirectHandler):
    """业务 API 不允许静默跳到登录页或任意新地址。"""
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("jd_platform_redirect_not_allowed")


def query_with_explicit_jd_union_grant(
    keyword: str, *, app_key: str, app_secret: str,
    approved_methods: frozenset[str], legacy_gateway_confirmed: bool,
    at: datetime | None = None, timeout: float = 8,
    transport=None,
) -> dict:
    """带清晰权限前置的真实 POST 功能（本项目默认不会调用）。

    仅限开发者在京东联盟后台核准 `goods.query` 权限、接口版本和用途后显式调用。
    本方法不读本机账号、环境密钥或浏览器 Cookie。transport 仅为测试注入。
    不跟随跳转，不记录请求表单。成功后也只产生不可购买的候选。
    """
    if (not isinstance(approved_methods, frozenset) or
            JD_METHOD not in approved_methods or legacy_gateway_confirmed is not True):
        raise PermissionError("jd_union_application_scope_or_legacy_gateway_not_confirmed")
    if type(timeout) not in (int, float) or not 1 <= timeout <= 12:
        raise ValueError("invalid_platform_timeout")
    instant = at or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("invalid_request_timestamp")
    if abs((datetime.now(timezone.utc) - instant.astimezone(timezone.utc)).total_seconds()) > 300:
        raise ValueError("jd_gateway_timestamp_out_of_window")
    fields = build_legacy_jos_goods_query_form(
        keyword, app_key=app_key, app_secret=app_secret, at=instant)
    endpoint = "https://api.jd.com/routerjson"  # 旧版 JOS 网关，必须在权限后台确认仍可用
    request = Request(
        endpoint, data=urlencode(fields).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                 "Accept": "application/json"},
    )
    injected_transport = transport is not None
    if transport is None:
        # 无重试、无静默重定向、只连固定端点。
        def transport(req, timeout):
            with build_opener(_DenyRedirect()).open(req, timeout=timeout) as response:
                if "json" not in response.headers.get("Content-Type", "").lower():
                    raise ValueError("jd_gateway_non_json")
                return response.read(MAX_SNAPSHOT_BYTES + 1)
    try:
        raw = transport(request, timeout)
    except Exception as exc:
        # 避免原始网络异常中的 URL、请求表单或外部字符串进入报告。
        raise ValueError("jd_gateway_request_failed") from None
    if not isinstance(raw, bytes) or len(raw) > MAX_SNAPSHOT_BYTES:
        raise ValueError("jd_gateway_response_size_or_type_invalid")
    try:
        data = json.loads(raw.decode("utf-8"),
                          parse_constant=lambda token: (_ for _ in ()).throw(ValueError("bad_constant")))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("jd_gateway_json_invalid") from None
    outcome = import_goods_query_response(
        data, keyword=keyword, observed_at=instant.astimezone(timezone.utc).isoformat())
    outcome["authorized_api_calls"] = 0 if injected_transport else 1
    outcome["api_transport"] = ("injected_test_transport" if injected_transport
                                else "caller_permitted_legacy_jos_https_post")
    outcome["source_assurance"] = ("synthetic_test_not_platform_proof" if injected_transport
                                    else "caller_asserted_scope_not_independently_audited")
    # 真实网关响应也只说明查到了推广候选，不证明价格、型号或店铺已核。
    for item in outcome["items"]:
        item["source_assurance"] = ("synthetic_test_not_platform_proof" if injected_transport
                                    else "official_transport_business_facts_unverified")
    return outcome


def main() -> None:
    parser = argparse.ArgumentParser(description="只解析已合法取得的京东联盟商品搜索JSON快照，不联网")
    parser.add_argument("--snapshot", required=True, help="已取得的官方响应 JSON 文件")
    parser.add_argument("--keyword", required=True, help="原检索关键词")
    parser.add_argument("--observed-at", required=True, help="取得快照的含时区 ISO 时间")
    parser.add_argument("--out", help="输出经过脱敏、永不含有效报价的候选摘要 JSON")
    args = parser.parse_args()
    path = Path(args.snapshot)
    if not path.is_file() or path.stat().st_size > MAX_SNAPSHOT_BYTES:
        parser.error("snapshot_missing_or_too_large")
    try:
        response = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        parser.error("snapshot_invalid_json")
    data = import_goods_query_response(
        response, keyword=args.keyword, observed_at=args.observed_at)
    safe_text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(safe_text, encoding="utf-8")
    print(safe_text, end="")


if __name__ == "__main__":
    main()
