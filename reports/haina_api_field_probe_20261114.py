"""2026-11-14 海纳商品检索Pro小样本字段探测：不缓存原始响应/密钥/推广链接。
必须由用户显式授权运行；每个case一次真实业务调用，零自动重试。
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
import uuid

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "reports"
URI = "https://gw-openapi.zhidemai.com/product/v1"
ID_KEYS = ("platform_item_id", "sku_id", "skuId", "skuid", "item_id", "itemId", "spu_id", "spuId", "product_id", "productId", "goods_id", "source_item_id")
BASE_FIELDS = "title,brand_name,mall_id,mall_name,shop_name,shop_type,url,union_spec,price,page_price"
ASK_IDS = BASE_FIELDS + "," + ",".join(ID_KEYS)
CASES = {
    "brother_full": {"product_query": "兄弟 HL-L1238W 打印机", "size": 3, "fields": ""},
    "hp_full": {"product_query": "惠普 M232dw 打印机", "size": 3, "fields": ""},
    "brother_ids": {"product_query": "兄弟 HL-L1238W 打印机", "size": 3, "fields": ASK_IDS},
    "hp_ids": {"product_query": "惠普 M232dw 打印机", "size": 3, "fields": ASK_IDS},
    "brother_jd": {"product_query": "兄弟 HL-L1238W 打印机", "size": 3, "fields": BASE_FIELDS, "mall_id": "183"},
    "hp_jd": {"product_query": "惠普 M232dw 打印机", "size": 3, "fields": BASE_FIELDS, "mall_id": "183"},
    "brother_broad_full": {"product_query": "兄弟 黑白激光打印机", "size": 3, "fields": ""},
    "brother_broad_ids": {"product_query": "兄弟 黑白激光打印机", "size": 3, "fields": ASK_IDS},
    "brother_broad_jd": {"product_query": "兄弟 黑白激光打印机", "size": 3, "fields": BASE_FIELDS, "mall_id": "183"},
}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def get_key() -> str:
    path = ROOT / "data/private/haina.env"
    if not path.is_file():
        raise SystemExit("local_private_key_file_missing")
    lines = [x.split("=", 1)[1].strip() for x in path.read_text(encoding="utf-8-sig").splitlines() if x.strip().startswith("HAINA_API_KEY=")]
    if len(lines) != 1:
        raise SystemExit("private_key_format_invalid")
    key = lines[0].strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in ("'", chr(34)):
        key = key[1:-1]
    if not key or any(c.isspace() for c in key) or "在本机" in key:
        raise SystemExit("private_key_invalid")
    return key

def brief(value, max_len=95) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return None
    return str(value)[:max_len]

def shape_paths(obj, depth=0, prefix="") -> list[str]:
    if depth > 4:
        return []
    if isinstance(obj, dict):
        items = []
        for k, v in list(obj.items())[:70]:
            if not isinstance(k, str):
                continue
            p = (prefix + "." + k) if prefix else k
            items.append(p)
            items.extend(shape_paths(v, depth+1, p)[:150])
        return items[:200]
    if isinstance(obj, list) and obj:
        return shape_paths(obj[0], depth+1, prefix+"[]")[:70]
    return []

def summarize_item(item: dict) -> dict:
    result = {
        "returned_field_names": sorted(k for k in item if isinstance(k, str)),
        "returned_field_types": {k: type(v).__name__ for k, v in item.items() if isinstance(k, str)},
        "title_excerpt": brief(item.get("title"), 110),
        "brand": brief(item.get("brand_name"), 45),
        "mall": brief(item.get("mall_name"), 40),
        "seller": brief(item.get("shop_name"), 75),
        "price_reported_unverified": brief(item.get("price"), 35),
        "page_price_reported_unverified": brief(item.get("page_price"), 35),
    }
    try:
        result["url_domain_only"] = (urlsplit(item.get("url") or "").hostname or "")[:80]
    except (TypeError, ValueError):
        result["url_domain_only"] = "invalid"
    found = {}
    for k in ID_KEYS:
        if k in item and item[k] is not None:
            v = str(item[k])
            found[k] = {"type": type(item[k]).__name__, "len": len(v), "sha256": hashlib.sha256(v.encode("utf-8")).hexdigest()}
    result["explicit_item_or_sku_fields"] = found
    spec = item.get("union_spec")
    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
        except (json.JSONDecodeError, ValueError):
            spec = None
    result["union_spec_type"] = type(spec).__name__
    result["union_spec_field_paths"] = shape_paths(spec)[:100]
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case", choices=sorted(CASES))
    args = ap.parse_args()
    out = OUT_DIR / ("haina_probe_20261114_" + args.case + ".json")
    if out.exists():
        raise SystemExit("output_exists_no_overwrite")
    key = get_key()
    config = CASES[args.case]
    payload = dict(request_from="shopping_decision_readonly_20261114", question_id="fieldprobe-"+uuid.uuid4().hex, query_process=1, **config)
    request = Request(URI, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"x-api-key": key,"Content-Type":"application/json"}, method="POST")
    result = {
        "probe_case": args.case,
        "source": "official_haina_product_search_pro",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "request_query": config["product_query"],
        "request_size": config["size"],
        "request_mall_id": config.get("mall_id"),
        "field_strategy": ("all_default_fields" if not config.get("fields") else "explicit_id_probes" if args.case.endswith("_ids") else "known_fields"),
        "requested_fields": config.get("fields", ""),
        "request_attempts": 1,
        "auto_retries": 0,
        "raw_response_saved": False,
        "credentials_saved": False,
        "promotional_url_saved": False,
        "purchase_recommendation_approved": False,
        "transactions_enabled": False
    }
    start = time.monotonic()
    body = b""
    try:
        with build_opener(NoRedirect()).open(request, timeout=30) as resp:
            result["http_status"] = resp.status
            body = resp.read(1_500_001)
    except HTTPError as exc:
        result["http_status"] = exc.code
        body = exc.read(1_500_001)
        result["status"] = "http_error"
    except (URLError, TimeoutError, OSError):
        result["status"] = "transport_error"
    result["elapsed_seconds"] = round(time.monotonic()-start, 3)
    result["response_size"] = len(body)
    result["response_sha256"] = hashlib.sha256(body).hexdigest() if body else None
    if len(body)>1_500_000:
        result["status"] = "response_too_large"
    elif body:
        try:
            obj=json.loads(body)
        except (ValueError, UnicodeError):
            result["status"] = "not_json"
        else:
            if isinstance(obj, dict):
                result["top_level_keys"] = list(obj)[:50]
                result["business_code"] = obj.get("error_code") if type(obj.get("error_code")) is int else None
                result["status"] = "success" if result.get("http_status")==200 and obj.get("error_code")==0 else "business_error"
                d = obj.get("data")
                result["data_keys"] = list(d)[:50] if isinstance(d, dict) else None
                rows = d.get("rows") if isinstance(d, dict) else None
                result["rows_returned"] = len(rows) if isinstance(rows, list) else None
                if result["status"]=="success" and isinstance(rows, list):
                    result["summaries"] = [summarize_item(x) for x in rows[:3] if isinstance(x, dict)]
                    result["explicit_item_or_sku_field_count"] = sum(bool(x.get("explicit_item_or_sku_fields")) for x in result["summaries"])
            else:
                result["status"] = "unexpected_json_shape"
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if key in rendered:
        raise SystemExit("redaction_failure_not_saved")
    with out.open("x", encoding="utf-8") as stream:
        stream.write(rendered+"\n")
    print(json.dumps({"case":args.case,"status":result.get("status"),"http":result.get("http_status"),"business_code":result.get("business_code"),"rows":result.get("rows_returned"),"field_presence":[x["returned_field_names"] for x in result.get("summaries",[])],"explicit_id_rows":result.get("explicit_item_or_sku_field_count"),"output":str(out.relative_to(ROOT))},ensure_ascii=False))

if __name__=="__main__":
    main()
