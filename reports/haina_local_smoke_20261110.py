"""一次经用户授权的只读连通测试；不回显密钥，不保存原始响应，不自动重试。"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
import hashlib
import json
import time
import uuid

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports/haina_local_smoke_20261110.json"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    credential = ROOT / "data/private/haina.env"
    values = [line.split("=", 1)[1].strip() for line in
              credential.read_text(encoding="utf-8-sig").splitlines()
              if line.strip().startswith("HAINA_API_KEY=")]
    if len(values) != 1 or not values[0]:
        raise SystemExit("credential_format_invalid")
    secret = values[0]
    if len(secret) >= 2 and secret[0] == secret[-1] and secret[0] in ("'", '"'):
        secret = secret[1:-1]
    if not secret or any(c.isspace() for c in secret) or "在本机" in secret:
        raise SystemExit("credential_value_invalid")

    def safe(value, limit=300):
        if value is None or isinstance(value, (bool, int, float)):
            return value
        raw = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        return raw.replace(secret, "[REDACTED]")[:limit]

    payload = {
        "request_from": "shopping_decision_local_smoke",
        "question_id": "local-smoke-" + uuid.uuid4().hex,
        "product_query": "惠普 黑白激光打印机", "query_process": 1, "size": 5,
        "fields": "title,brand_name,mall_id,mall_name,shop_name,shop_type,url,price,page_price,union_spec",
    }
    request = Request("https://gw-openapi.zhidemai.com/product/v1",
                      data=json.dumps(payload).encode("utf-8"),
                      headers={"x-api-key": secret, "Content-Type": "application/json"},
                      method="POST")
    result = {
        "operation": "user_authorized_haina_local_smoke",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "query": payload["product_query"], "requested_size": 5,
        "request_limit": 1, "requests_attempted": 1, "automatic_retries": 0,
        "credential_value_logged": False, "raw_response_saved": False,
        "purchase_recommendation_approved": False, "transactions_enabled": False,
    }
    start = time.monotonic()
    try:
        with build_opener(NoRedirect()).open(request, timeout=35) as response:
            result["http_status"] = response.status
            body = response.read(2_000_001)
    except HTTPError as exc:
        result.update(status="http_error", http_status=exc.code)
        body = exc.read(2_000_001)
    except (URLError, TimeoutError, OSError):
        result.update(status="transport_error", error_detail="not_logged_to_protect_credentials")
        body = b""
    result["elapsed_seconds"] = round(time.monotonic() - start, 3)
    result["response_bytes"] = len(body)
    result["response_sha256"] = hashlib.sha256(body).hexdigest() if body else None
    if len(body) > 2_000_000:
        result["status"] = "response_too_large"
    elif body:
        try:
            data = json.loads(body)
        except (ValueError, UnicodeError):
            result["status"] = "non_json_response"
        else:
            if isinstance(data, dict):
                result["top_level_fields"] = [safe(k) for k in data.keys()]
                result["business_code"] = safe(data.get("error_code"))
                # 不记录错误正文：服务端有可能回显请求头或凭证。
                successful = result.get("http_status") == 200 and data.get("error_code") == 0
                result["status"] = "success" if successful else "business_or_http_error"
                inner = data.get("data")
                rows = inner.get("rows") if isinstance(inner, dict) else None
                result["data_fields"] = [safe(k) for k in inner.keys()] if isinstance(inner, dict) else None
                result["returned_rows"] = len(rows) if isinstance(rows, list) else None
                summaries = []
                for row in (rows[:5] if successful and isinstance(rows, list) else []):
                    if not isinstance(row, dict):
                        continue
                    summary = {k: safe(row.get(k)) for k in
                               ("title", "brand_name", "mall_name", "shop_name", "shop_type", "price", "page_price")}
                    summary["returned_fields"] = [safe(k) for k in row.keys()]
                    try:
                        summary["link_host"] = urlsplit(row.get("url") or "").hostname
                    except (ValueError, TypeError):
                        summary["link_host"] = "invalid"
                    summary["union_spec_type"] = type(row.get("union_spec")).__name__
                    summary["union_spec_excerpt"] = safe(row.get("union_spec"), 1200)
                    summaries.append(summary)
                result["product_summaries"] = summaries
            else:
                result["status"] = "unexpected_response_shape"
    result["limitations"] = [
        "一次最多5条的供应商检索测试，不证明所有已开通接口或稳定性",
        "供应商价格不等于用户地区到手价，标题及规格不等于平台销售项身份已核验",
        "未调用商品基础信息、SKU、参数或评论接口；用途许可未由此批准",
    ]
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if secret in rendered:
        raise SystemExit("redaction_validation_failed")
    OUT.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
