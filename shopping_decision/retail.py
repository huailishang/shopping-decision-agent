"""京东公开页只读回查与报价完整性检查。页面/搜索文案从不执行为指令。

此适配器当前只采集公开页访问与身份锚点，不具备完整实时核价能力。
完整报价契约的阳性测试仅为合成验证，不代表外部接口打通。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
RETAIL_PATH = ROOT / "knowledge" / "printer_retail_checks.json"
MAX_BYTES = 1_500_000
TARGETS = (
    {"model_id": "HL-L1238W", "expected_kind": "printer",
     "url": "https://item.jd.com/100126724020.html",
     "discovered_from": "https://dir.jd.com/guide/jd-geo-guide-xiong-di-da-yin-ji-v1"},
    {"model_id": "HL-L1238W", "expected_kind": "toner", "expected_consumable": "TN118",
     "url": "https://item.jd.com/100111044227.html",
     "discovered_from": "https://www.jd.com/jiage/670d39abab4f820e793.html"},
)
MISSING_FIELDS = ["seller", "exact_model_and_selected_configuration", "condition_new_or_used",
                  "price_and_currency", "promotion_eligibility", "shipping_and_required_extras",
                  "delivery_region_and_stock", "valid_until", "included_consumables", "after_sales"]


def allowed_product_url(url: str) -> bool:
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and p.hostname == "item.jd.com" and p.port is None
                and not p.username and not p.password and not p.query and not p.fragment
                and re.fullmatch(r"/[0-9]{6,20}\.html", p.path) is not None)
    except (TypeError, ValueError):
        return False


class PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_product_url(newurl):
            raise ValueError("不跟随登录/跨域重定向")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(" ".join(data.split()))


def inspect_public_page(body: bytes, model: str) -> dict:
    parser = VisibleText()
    parser.feed(body.decode("utf-8", "replace"))
    text = " ".join(parser.parts)
    # 完整型号边界；L1238W与L1238WXL不可混为同型号。型号锚点仍不是已选SKU证明。
    anchor = bool(re.search(r"(?<![A-Za-z0-9-])" + re.escape(model) + r"(?![A-Za-z0-9-])", text, re.I))
    restricted = any(s in text for s in ("高版本浏览器", "访问受限", "安全验证", "请登录", "验证码"))
    return {"model_anchor_found": anchor,
            "access_status": "restricted_or_login_page" if restricted else "partial_public_page",
            "identity_verified": False, "quote": None,
            "missing_fields": MISSING_FIELDS.copy(),
            "limitation": "可见型号文字不证明所选配置/卖家/新旧/报价；当前适配器不提取或批准实时价格"}


def check_public_product(target: dict, *, timeout: float = 8.0) -> dict:
    if not allowed_product_url(target["url"]):
        raise ValueError("只接受已登记的京东公开商品链接")
    now = datetime.now(timezone.utc).isoformat()
    result = {**target, "platform": "JD", "source_kind": "direct_platform_page",
              "retrieved_at": now, "valid_until": None,
              "product_id_from_url": urlsplit(target["url"]).path[1:-5],
              "product_id_is_verified_sku": False, "quote": None,
              "missing_fields": MISSING_FIELDS.copy()}
    try:
        request = Request(target["url"], headers={"User-Agent": "ShoppingDecisionReadOnlyCheck/1.0", "Accept": "text/html"})
        with build_opener(PublicRedirect()).open(request, timeout=timeout) as resp:
            if not allowed_product_url(resp.url) or "text/html" not in resp.headers.get("Content-Type", "").lower():
                raise ValueError("非允许的公开商品HTML")
            body = resp.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("页面超出上限")
            digest = hashlib.sha256(body).hexdigest()
            raw = ROOT / "data" / "raw" / "p0_2_retail" / (digest + ".html")
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(body)
            result.update(inspect_public_page(body, target.get("expected_consumable", target["model_id"])))
            result.update({"http_status": resp.status, "response_sha256": digest,
                           "response_bytes": len(body), "raw_snapshot": raw.relative_to(ROOT).as_posix()})
    except Exception as exc:
        result.update({"access_status": "unreachable_or_blocked", "error_type": type(exc).__name__,
                       "http_status": exc.code if isinstance(exc, HTTPError) else None,
                       "identity_verified": False})
    return result


def _instant(value):
    if not isinstance(value, str):
        raise ValueError("缺少时间")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("时间必须含时区")
    return parsed


def assess_quote(quote: dict | None, *, model_id: str, delivery_region: str | None,
                 budget_scope: str, budget_max_cny: int | None,
                 now: datetime | None = None) -> dict:
    """仅核对只读来源适配器给出的字段契约；不接受自然语言声称或用户报价注入。"""
    now = now or datetime.now(timezone.utc)
    reasons = []
    if not isinstance(quote, dict):
        return {"status": "unverified_no_authorized_live_quote", "reasons": ["missing_platform_quote"],
                "delivered_total_minor": None, "within_budget": None}
    if quote.get("source_kind") != "direct_platform_page" or not allowed_product_url(quote.get("source_url")):
        reasons.append("not_direct_platform_product_source")
    if quote.get("model_id") != model_id or quote.get("kind") != "printer":
        reasons.append("wrong_model_or_accessory")
    if quote.get("selected_model_id") != model_id or quote.get("package_kind") != "single_new_printer":
        reasons.append("selected_configuration_model_or_package_mismatch")
    sku = quote.get("sku_id")
    if not isinstance(sku, str) or not sku.isdigit() or not allowed_product_url(quote.get("source_url")) or urlsplit(quote["source_url"]).path != f"/{sku}.html":
        reasons.append("sku_url_mismatch")
    for field in ("seller", "selected_configuration", "included_consumables", "after_sales"):
        if not isinstance(quote.get(field), str) or not quote[field].strip():
            reasons.append("missing_" + field)
    if quote.get("condition") != "new":
        reasons.append("not_verified_new")
    if quote.get("currency") != "CNY":
        reasons.append("currency_not_cny")
    for field in ("price_minor", "shipping_minor", "required_extras_minor"):
        if type(quote.get(field)) is not int or quote[field] < 0:
            reasons.append("missing_or_invalid_" + field)
    if not delivery_region or quote.get("delivery_region") != delivery_region:
        reasons.append("delivery_region_unknown_or_mismatch")
    if quote.get("stock") != "in_stock":
        reasons.append("not_verified_in_stock")
    # 一律要求明确“无条件”或“适用且已核验”，不猜会员/国补/优惠券资格。
    if quote.get("promotion_eligibility") not in ("unconditional", "verified_eligible"):
        reasons.append("promotion_eligibility_unverified_or_ineligible")
    try:
        captured, expires = _instant(quote.get("retrieved_at")), _instant(quote.get("valid_until"))
        if not captured <= now < expires or expires - captured > timedelta(minutes=15):
            reasons.append("expired_future_or_excessive_validity")
    except (ValueError, TypeError):
        reasons.append("invalid_quote_validity")
    # 每个字段的引用必须绑定同一平台SKU及获取时刻。文案中的“已批准”无效。
    sources = quote.get("field_sources", {})
    for field in ("model_id", "selected_model_id", "package_kind", "kind", "sku_id", "seller", "selected_configuration", "condition",
                  "price_minor", "currency", "shipping_minor", "required_extras_minor", "delivery_region",
                  "stock", "promotion_eligibility", "included_consumables", "after_sales", "valid_until"):
        if not isinstance(sources, dict) or sources.get(field) != quote.get("source_url"):
            reasons.append("missing_field_source:" + field)
    if budget_scope != "device_delivered":
        reasons.append("budget_scope_unknown_or_extra_consumables_unpriced")
    if reasons:
        return {"status": "unverified_quote_rejected", "reasons": reasons,
                "delivered_total_minor": None, "within_budget": None}
    total = sum(quote[k] for k in ("price_minor", "shipping_minor", "required_extras_minor"))
    within = None if budget_max_cny is None else total <= budget_max_cny * 100
    return {"status": "verified_within_budget" if within is True else "verified_over_budget" if within is False else "verified_total_budget_unspecified",
            "reasons": [], "delivered_total_minor": total, "within_budget": within}


def load_retail_checks(path: Path = RETAIL_PATH) -> dict:
    if not path.is_file():
        return {"checks": [], "status": "not_checked"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("operation") != "read_only_jd_public_product_check":
            raise ValueError("来源检查格式错误")
        if not isinstance(data.get('checks'), list) or any(not isinstance(c, dict) for c in data['checks']):
            raise ValueError("来源检查不是列表")
        # 当前采集器没有完整核价能力。即使本地索引被塞入手填价格也拒绝。
        for check in data["checks"]:
            if (not allowed_product_url(check.get("url")) or check.get("quote") is not None
                    or check.get("identity_verified") is not False):
                raise ValueError("当前渠道不能产生有效完整报价")
            if (not any(check.get('url') == t['url'] and check.get('model_id') == t['model_id']
                        and check.get('expected_kind') == t['expected_kind'] for t in TARGETS)
                    or check.get('access_status') not in ('restricted_or_login_page', 'partial_public_page', 'unreachable_or_blocked')
                    or not isinstance(check.get('missing_fields'), list)
                    or any(f not in MISSING_FIELDS for f in check['missing_fields'])
                    or _instant(check.get('retrieved_at')) > datetime.now(timezone.utc)):
                raise ValueError('不完整或未来的零售访问记录')
        return data
    except (ValueError, TypeError, KeyError):
        return {"checks": [], "status": "invalid_check_index_rejected"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=RETAIL_PATH)
    args = parser.parse_args()
    result = {"schema_version": 1, "operation": "read_only_jd_public_product_check",
              "checked_at": datetime.now(timezone.utc).isoformat(),
              "provider_capability": "public_access_and_identity_anchor_only_not_live_quote",
              "checks": [check_public_product(target) for target in TARGETS],
              "transactions_enabled": False, "valid_live_quote_count": 0}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
