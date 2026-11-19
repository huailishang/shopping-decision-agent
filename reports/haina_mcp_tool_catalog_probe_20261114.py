"""仅探测海纳MCP工具元数据，不调用任何具体业务工具。
使用本机已受保护的HAINA_API_KEY，不输出密钥、会话ID或原始响应。
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler
from datetime import datetime, timezone
import time

ROOT = Path(__file__).resolve().parent.parent
URI = "https://gw-openapi.zhidemai.com/ai-mcp/streamable/mcp"
OUTPUT = ROOT / "reports/haina_mcp_tool_catalog_20261114.json"

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def load_key():
    p = ROOT / "data/private/haina.env"
    values = [x.split("=",1)[1].strip() for x in p.read_text(encoding="utf-8-sig").splitlines() if x.strip().startswith("HAINA_API_KEY=")]
    if len(values)!=1:
        raise SystemExit("credential_unavailable")
    v=values[0]
    if len(v)>1 and v[0]==v[-1] and v[0] in ("'",chr(34)):
        v=v[1:-1]
    if not v or any(c.isspace() for c in v):
        raise SystemExit("credential_invalid")
    return v

def parse_json_or_sse(raw):
    text = raw.decode("utf-8",errors="replace")
    try:
        return json.loads(text)
    except ValueError:
        events = [x[5:].strip() for x in text.splitlines() if x.startswith("data:")]
        for x in events:
            try:
                obj=json.loads(x)
                if isinstance(obj,dict) and ("result" in obj or "error" in obj):
                    return obj
            except ValueError:
                continue
    return {}

def req(key, payload, session=None):
    body=json.dumps(payload,ensure_ascii=False).encode("utf-8")
    headers={"x-api-key":key,"Content-Type":"application/json","Accept":"application/json, text/event-stream","MCP-Protocol-Version":"2025-06-18"}
    if session:
        headers["Mcp-Session-Id"]=session
    r=Request(URI,data=body,headers=headers,method="POST")
    try:
        with build_opener(NoRedirect()).open(r,timeout=25) as h:
            raw=h.read(400_001)
            return {"http":h.status,"raw":raw,"session":h.headers.get("Mcp-Session-Id"),"content_type":h.headers.get("Content-Type")}
    except HTTPError as e:
        return {"http":e.code,"raw":e.read(400_001),"session":None,"content_type":None}
    except (URLError,TimeoutError,OSError):
        return {"http":None,"raw":b"","session":None,"content_type":None}

def main():
    if OUTPUT.exists():
        raise SystemExit("out_exists_no_overwrite")
    key=load_key()
    start=time.monotonic()
    init=req(key,{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"shopping-decision-readonly-audit","version":"0.1"}}})
    obj=parse_json_or_sse(init["raw"])
    result={"observed_at":datetime.now(timezone.utc).isoformat(),"operation":"mcp_initialize_and_tools_list_metadata_only","api_business_tool_calls":0,"credential_logged":False,"raw_response_saved":False,
            "initialize_http":init["http"],"initialize_body_sha256":hashlib.sha256(init["raw"]).hexdigest() if init["raw"] else None,
            "initialize_success":isinstance(obj.get("result"),dict),"negotiated_protocol":(obj.get("result") or {}).get("protocolVersion") if isinstance(obj.get("result"),dict) else None,
            "server_name":((obj.get("result") or {}).get("serverInfo") or {}).get("name") if isinstance(obj.get("result"),dict) else None}
    if result["initialize_success"]:
        session=init["session"]
        # 标准MCP initialized 通知，不触发业务工具
        notify=req(key,{"jsonrpc":"2.0","method":"notifications/initialized"},session)
        result["initialized_notification_http"]=notify["http"]
        listing=req(key,{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}},session)
        result["tools_list_http"]=listing["http"]
        result["tools_list_body_sha256"]=hashlib.sha256(listing["raw"]).hexdigest() if listing["raw"] else None
        payload=parse_json_or_sse(listing["raw"])
        toolset=(payload.get("result") or {}).get("tools") if isinstance(payload.get("result"),dict) else None
        result["tools_count"]=len(toolset) if isinstance(toolset,list) else None
        result["tools"]=[{"name":str(t.get("name",""))[:120],
                         "description_excerpt":str(t.get("description",""))[:350],
                         "input_property_names":list((t.get("inputSchema") or {}).get("properties",{}))[:80],
                         "input_required":list((t.get("inputSchema") or {}).get("required",[]))[:40]} for t in toolset if isinstance(t,dict)][:30] if isinstance(toolset,list) else []
    result["elapsed_seconds"]=round(time.monotonic()-start,3)
    rendered=json.dumps(result,ensure_ascii=False,indent=2)
    if key in rendered:
        raise SystemExit("redaction_failed")
    with OUTPUT.open("x",encoding="utf-8") as f:
        f.write(rendered+"\n")
    print(json.dumps({"initialize_http":result["initialize_http"],"initialize_success":result["initialize_success"],"tools_list_http":result.get("tools_list_http"),"tools_count":result.get("tools_count"),"names":[x["name"] for x in result.get("tools",[])],"out":str(OUTPUT.relative_to(ROOT))},ensure_ascii=False))

if __name__=="__main__":
    main()
