"""从厂商公开商品目录自动发现候选型号，发现不等于参数或购买资格审核。

目前实现 Brother CN 黑白激光产品列表的无账号只读发现；HP来源暂时只有经过查询的规格快照。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener

from .official_source_check import _SafeRedirect, MAX_BYTES, is_allowed
from .product_compare import load_official_catalog

BROTHER_LIST_URL = "https://www.brother.cn/printer/prt"


class _LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.href = None
        self.text_parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.text_parts = []

    def handle_data(self, data):
        if self.href is not None and data.strip():
            self.text_parts.append(" ".join(data.split()))

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(self.text_parts)))
            self.href = None
            self.text_parts = []


def discover_brother_monochrome(html: str) -> list[dict]:
    parser = _LinkCollector()
    parser.feed(html)
    result = []
    seen = set()
    for href, title in parser.links:
        url = urljoin(BROTHER_LIST_URL, href)
        parsed = urlsplit(url)
        if parsed.hostname != "www.brother.cn" or not parsed.path.startswith("/printer/prt/"):
            continue
        if "黑白激光" not in title:
            continue
        m = re.search(r"\bHL-[A-Z0-9-]+\b", title, re.IGNORECASE)
        if not m:
            continue
        model = m.group(0).upper()
        if model in seen:
            continue
        seen.add(model)
        result.append({"model_id": model, "brand": "Brother", "name": model,
                       "category": "printer", "category_hint": "mono_laser_from_website_label",
                       "official_url": url, "status": "discovered_unverified_facts",
                       "fact_confidence": "model_and_official_category_label_only"})
    return result


def discover(*, timeout: float = 8.0) -> dict:
    if not 1 <= timeout <= 15:
        raise ValueError("timeout须在1～15秒")
    if not is_allowed(BROTHER_LIST_URL):
        raise ValueError("商品目录不在厂商来源白名单")
    req = Request(BROTHER_LIST_URL, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
    with build_opener(_SafeRedirect()).open(req, timeout=timeout) as resp:
        if not is_allowed(resp.url):
            raise ValueError("目录发生不安全跳转")
        if "text/html" not in resp.headers.get("Content-Type", "").lower():
            raise ValueError("厂商目录不是HTML")
        body = resp.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("页面超过读取上限")
    found = discover_brother_monochrome(body.decode("utf-8", "replace"))
    known = {x["model_id"] for x in load_official_catalog()["products"]}
    for item in found:
        item["in_verified_fact_catalog"] = item["model_id"] in known
    return {"discovered_at": datetime.now(timezone.utc).isoformat(),
            "source_url": BROTHER_LIST_URL, "response_sha256": hashlib.sha256(body).hexdigest(),
            "provider": "Brother CN", "catalog_complete": False,
            "operation": "read_only_model_discovery",
            "found_count": len(found),
            "new_model_count": sum(not x["in_verified_fact_catalog"] for x in found),
            "models": found,
            "limitations": [
                "只覆盖兄弟官网当前黑白激光列表，不代表全部品牌、全部在售型号",
                "官网列出的型号不是零售平台有货，也不是符合预算",
                "新发现型号必须逐项取得功能、耗材、价格来源之后才能进入选购比较",
                "没有获取授权平台实时报价，也没有读取账号或执行任何交易",
            ]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="可选：写入发现摘要报告")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()
    data = discover(timeout=args.timeout)
    result = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        from pathlib import Path
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result, encoding="utf-8")
    print(result, end="")


if __name__ == "__main__":
    main()
