"""从本机 Swing 手动商城发现窗导入用户选择的商品链接（完全离线）。

只能构造官方公开搜索 URL，并校验用户粘贴的 JD 商品详情链接。
不接管浏览器登录状态、无平台 API、无页面抓取、无自动下单。
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import sys
from urllib.parse import quote

from .discovery_ingest import ingest_user_jd_item_link

MAX_QUERY_CHARS = 100
MAX_LINKS = 5


def shop_search_url(query: str, *, platform: str = "jd") -> str:
    """用固定域名构造仅供用户主动打开的公开搜索页，不触发访问。"""
    if (not isinstance(query, str) or not 1 <= len(query.strip()) <= MAX_QUERY_CHARS
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in query)):
        raise ValueError("搜索词须为1至100字，不包含控制字符")
    escaped = quote(query.strip(), safe="")
    if platform == "jd":
        return "https://search.jd.com/Search?keyword=" + escaped
    if platform == "taobao":
        return "https://s.taobao.com/search?q=" + escaped
    raise ValueError("不支持的商城")


def review_user_links(query: str, pasted: str, *, now: datetime | None = None) -> dict:
    """只读整理链接，禁止使用网页价格或 URL 编号作购买依据。"""
    url = shop_search_url(query)
    if not isinstance(pasted, str) or len(pasted) > 12000:
        raise ValueError("商品链接文本过长")
    lines = [s.strip() for s in pasted.splitlines() if s.strip()]
    if not 1 <= len(lines) <= MAX_LINKS:
        raise ValueError("请粘贴1至5条京东商品详情页链接（每行一条）")
    current = now or datetime.now(timezone.utc)
    seen = set()
    entries = []
    rejected = []
    for idx, line in enumerate(lines, 1):
        result = ingest_user_jd_item_link(line, observed_at=current.isoformat(), now=current)
        if result.get("status") != "discovered_unverified":
            rejected.append({"line": idx, "reason": "not_verified_jd_product_url"})
            continue
        key = (result["platform"], result["platform_item_id"])
        if key in seen:
            rejected.append({"line": idx, "reason": "duplicate_product_link"})
            continue
        seen.add(key)
        # 仅返回可供核验的链接，不让粘贴的链接直接影响原价格/购买批准。
        entries.append(result)
    return {
        "status": "candidates_unverified" if entries else "no_valid_candidates",
        "operation": "user_selected_marketplace_link_review",
        "search_query": query.strip(), "search_url": url,
        "candidate_count": len(entries), "rejected_count": len(rejected),
        "candidates": entries, "rejected": rejected,
        "limitations": [
            "这是用户自己打开商城搜索后选取的链接，系统未调用京东官方搜索API",
            "仅从网址抽取可能的京东商品编号，未证明真实在售、准确型号和商品类别",
            "卖家、选中套餐、地区库存、券后价、运费及售后均待平台核验",
            "此结果不进入原购买批准门禁，不会产生订单或支付操作",
        ],
        "verified_quote_count": 0, "authorized_api_calls": 0,
        "purchase_recommendation_approved": False, "transactions_enabled": False
    }


def _output(values: dict[str, str]) -> None:
    for k, v in values.items():
        print(k + "\t" + base64.b64encode(str(v).encode("utf-8")).decode("ascii"))


def main() -> None:
    try:
        if len(sys.argv) != 3:
            raise ValueError("需要两个Base64参数：搜索词、商品链接")
        raw = [base64.b64decode(s, validate=True).decode("utf-8") for s in sys.argv[1:]]
        result = review_user_links(raw[0], raw[1])
        msg = [f"状态：{result['status']}", f"商品线索：{result['candidate_count']}条",
               f"拒绝/重复：{result['rejected_count']}条"]
        for item in result["candidates"]:
            msg.append(f"京东商品编号（未核）：{item['platform_item_id']}  {item['canonical_url']}")
        msg.append("实际价格/库存/店铺/型号均未核实；暂不构成购买建议。")
        _output({"status": result["status"], "summary": "\n".join(msg),
                 "report_json": json.dumps(result, ensure_ascii=False, indent=2)})
    except (ValueError, UnicodeError) as exc:
        _output({"error": str(exc)})


if __name__ == "__main__":
    main()
