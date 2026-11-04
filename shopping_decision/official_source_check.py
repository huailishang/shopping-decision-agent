"""P0 厂商公开来源只读回查。只检查登记URL可达性和型号锚点，不擅自刷新事实字段。

用法: python3 -m shopping_decision.official_source_check --model HL-L1238W
不需要账号/支付信息，禁止任意URL输入，HTTPS只允许已配置厂商域名。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from .product_compare import load_official_catalog

ALLOWED_HOSTS = frozenset(("www.brother.cn", "www.95105369.com", "95105369.com", "support.hp.com"))
MAX_BYTES = 900_000


def is_allowed(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS
                and parsed.port is None and not parsed.username and not parsed.password)
    except ValueError:
        return False


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_allowed(newurl):
            raise ValueError("被阻止的跨域或非HTTPS重定向")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        clean = " ".join(data.split())
        if clean:
            self.parts.append(clean)


def inspect_html(body: bytes, model: str) -> bool:
    # HTML只用来找型号锚点，不能因为包含文字就把功能/价/评测判为合格。
    if not model or not isinstance(model, str):
        raise ValueError("model必须非空")
    parser = _Text()
    parser.feed(body.decode("utf-8", "replace"))
    text = " ".join(parser.parts).casefold()
    # catalog id是HP-Laser-108w；官网一般只写HP 108w，匹配具体尾型号。
    needle = model.rsplit("-", 1)[-1] if model.startswith("HP-Laser-") else model
    return needle.casefold() in text


def check_one(url: str, model: str, *, timeout: float = 6.0) -> dict:
    if not is_allowed(url):
        return {"url": url, "model": model, "status": "blocked_url"}
    try:
        req = Request(url, headers={"User-Agent": "ShoppingDecisionEvidenceCheck/1.0", "Accept": "text/html"})
        with build_opener(_SafeRedirect()).open(req, timeout=timeout) as resp:
            final_url = resp.url
            if not is_allowed(final_url):
                raise ValueError("跳转到未授权域名")
            content_type = resp.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                raise ValueError("只检查公开HTML，不解析PDF或其他文件")
            body = resp.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("页面超过回查上限")
            found = inspect_html(body, model)
            return {"url": url, "final_url": final_url, "model": model,
                    "status": "model_anchor_found" if found else "model_anchor_missing",
                    "http_status": resp.status,
                    "response_sha256": hashlib.sha256(body).hexdigest(),
                    "response_bytes": len(body),
                    "limitations": "此检查仅证明请求得到HTML和存在型号字符串，不证明功能、在售、报价、授权或实机体验"}
    except Exception as exc:
        # 错误只保存类型，不回显可能包含敏感网络信息的原始异常。
        return {"url": url, "model": model, "status": "unreachable_or_invalid",
                "error_type": type(exc).__name__}


def check_catalog(*, only_model: str | None = None, timeout: float = 6.0) -> dict:
    if not 1 <= timeout <= 15:
        raise ValueError("timeout必须在1～15秒之间")
    cat = load_official_catalog()
    records = [p for p in cat["products"] if only_model is None or p["model_id"] == only_model]
    if not records:
        raise ValueError("没有登记该型号；不从未授权站点猜测新型号")
    checked = [check_one(p["official_url"], p["model_id"], timeout=timeout) for p in records]
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "catalog_recorded_on": cat["recorded_on"],
            "operation": "read_only_official_model_anchor_recheck", "checks": checked,
            "count": len(checked), "fresh_model_anchors": sum(x["status"] == "model_anchor_found" for x in checked),
            "limitations": ["不自动更改已登记产品事实或证据批准状态",
                            "失败不会判定该产品停产；需要官方资料/型号范围进一步核对",
                            "未执行跨站搜索/商品发现、实时报价、登录、下单或支付"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="只复核已经登记的型号")
    parser.add_argument("--timeout", type=float, default=6.0)
    parser.add_argument("--out", default=None, help="可选：将检查摘要JSON写入文件")
    args = parser.parse_args()
    result = check_catalog(only_model=args.model, timeout=args.timeout)
    formatted = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        from pathlib import Path
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(formatted + "\n", encoding="utf-8")
    print(formatted)


if __name__ == "__main__":
    main()
