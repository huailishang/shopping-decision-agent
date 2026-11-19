"""已授权的海纳MCP能力只读小样本探测。真实工具调用需显式逐case执行，不重试，不保存原始商品数据。
所有商品链接只取域名，ID只记哈希/路径，评价正文不存。
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import time
from urllib.parse import urlsplit
from reports.haina_mcp_tool_catalog_probe_20261114 import ROOT, load_key, req, parse_json_or_sse

CASES={
    "hp_sku":("product_sku_search",{"query":"惠普 M232dw"}),
    "brother_sku":("product_sku_search",{"query":"兄弟 HL-L1238W"}),
    "hp_sku_detail":("product_sku_search",{"query":"惠普 M232dw"}),
    "brother_sku_detail":("product_sku_search",{"query":"兄弟 HL-L1238W"}),
    "brother_alt_sku":("product_sku_search",{"query":"兄弟 HL-B2158W"}),
    "hp_basic":("product_basic_search",{"query":"惠普 M232dw"}),
    "hp_param":("product_parameter_search",{"query":"惠普 M232dw"}),
    "hp_comment":("product_comment_search",{"query":"惠普 M232dw","comment_limit":3}),
    "brother_basic":("product_basic_search",{"query":"兄弟 HL-L1238W"}),
    "brother_param":("product_parameter_search",{"query":"兄弟 HL-L1238W"}),
    "brother_comment":("product_comment_search",{"query":"兄弟 HL-L1238W","comment_limit":3})
}
OUTPUT_DIR=ROOT/"reports"

def structure(v,prefix="",depth=0,limit=220):
    results=[]
    if depth>9:
        return results
    if isinstance(v,dict):
        for k,x in list(v.items())[:75]:
            key=str(k)
            p=prefix+"."+key if prefix else key
            results.append({"path":p,"type":type(x).__name__,"length":len(x) if isinstance(x,(list,dict)) else None})
            if len(results)>=limit:
                break
            results+=structure(x,p,depth+1,limit-len(results))
            if len(results)>=limit:
                break
    elif isinstance(v,list):
        if v: results+=structure(v[0],prefix+"[]",depth+1,limit)
    return results[:limit]

def audit_values(obj,prefix="",depth=0,cap=100):
    if depth>8:return []
    output=[]
    if isinstance(obj,dict):
        for k,v in list(obj.items())[:150]:
            p=prefix+"."+str(k) if prefix else str(k)
            low=str(k).lower()
            if ("sku" in low or "spu" in low or low in ("item_id","product_id","goods_id","variant_id")) and not isinstance(v,(dict,list)) and v is not None:
                val=str(v)
                output.append({"field":p,"kind":type(v).__name__,"len":len(val),"sha256":hashlib.sha256(val.encode("utf-8")).hexdigest()})
            if isinstance(v,(dict,list)):
                output+=audit_values(v,p,depth+1,cap-len(output))
            if len(output)>=cap:break
    elif isinstance(obj,list):
        for i,v in enumerate(obj[:6]):
            output+=audit_values(v,prefix+"[]",depth+1,cap-len(output))
            if len(output)>=cap:break
    return output[:cap]

def safe_descriptions(obj,depth=0,limit=12):
    if depth>10 or limit<=0:return []
    out=[]
    if isinstance(obj,dict):
        for k,v in list(obj.items())[:80]:
            if str(k).lower() in ("title","product_name","sku_name","name","brand_name","shop_name","mall_name") and isinstance(v,str) and len(v)<=500:
                out.append({"field":str(k),"value_excerpt":v[:95]})
            elif isinstance(v,(dict,list)):
                out+=safe_descriptions(v,depth+1,limit-len(out))
            if len(out)>=limit:break
    elif isinstance(obj,list):
        for v in obj[:3]:
            out+=safe_descriptions(v,depth+1,limit-len(out))
            if len(out)>=limit:break
    return out[:limit]

def parse_content(msg):
    if not isinstance(msg,dict):return {}
    result=msg.get("result")
    if not isinstance(result,dict):return {}
    if isinstance(result.get("structuredContent"),(dict,list)):
        return result.get("structuredContent")
    for c in result.get("content",[]):
        if not isinstance(c,dict) or c.get("type")!="text":continue
        raw=c.get("text")
        if not isinstance(raw,str):continue
        try:
            return json.loads(raw)
        except ValueError:
            continue
    return {}

def sku_summary(business):
    if not isinstance(business,dict) or not isinstance(business.get("data"),list):
        return []
    result=[]
    for entity in business["data"][:5]:
        if not isinstance(entity,dict): continue
        raw=entity.get("sku_result")
        if not isinstance(raw,dict): continue
        skus=raw.get("sku_list")
        item={"entity_name":str(entity.get("entity_name") or "")[:70],
              "spu_id_present":bool(raw.get("spu_id")),
              "spu_name_excerpt":str(raw.get("spu_name") or "")[:100],
              "sku_count_reported":raw.get("sku_count") if type(raw.get("sku_count")) is int else None,
              "sku_list_length":len(skus) if isinstance(skus,list) else None,
              "skus":[]}
        for sku in skus[:4] if isinstance(skus,list) else []:
            if not isinstance(sku,dict): continue
            prods=sku.get("sku_products")
            x={"sku_id_present":bool(sku.get("sku_id")),
               "sku_id_length":len(str(sku.get("sku_id") or "")),
               "axes_keys":list(sku.get("sku_axes") or {})[:10] if isinstance(sku.get("sku_axes"),dict) else [],
               "sku_products_count_reported":sku.get("sku_products_count") if type(sku.get("sku_products_count")) is int else None,
               "sku_products_length":len(prods) if isinstance(prods,list) else None,
               "products":[]}
            for p in prods[:4] if isinstance(prods,list) else []:
                if not isinstance(p,dict):continue
                v=str(p.get("id") or "")
                try: host=urlsplit(p.get("url") or "").hostname
                except (TypeError,ValueError):host=None
                x["products"].append({"item_id_field_present":bool(v),"item_id_length":len(v),
                                      "item_id_all_digits":v.isdigit(),"item_id_sha256":hashlib.sha256(v.encode()).hexdigest() if v else None,
                                      "title_excerpt":str(p.get("title") or "")[:105],
                                      "mall_name":str(p.get("mall_name") or "")[:60],
                                      "shop_name":str(p.get("shop_name") or "")[:70],
                                      "shop_type":str(p.get("shop_type") or "")[:30],
                                      "sku_prop_excerpt":str(p.get("sku_prop") or "")[:60],
                                      "url_host":host,
                                      "price_provider_unverified":str(p.get("final_price") or "")[:22]})
            item["skus"].append(x)
        result.append(item)
    return result

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("case",choices=sorted(CASES))
    a=ap.parse_args()
    out=OUTPUT_DIR/("haina_mcp_probe_20261114_"+a.case+".json")
    if out.exists():raise SystemExit("out_exists_no_overwrite")
    key=load_key()
    tool,args=CASES[a.case]
    start=time.monotonic()
    init=req(key,{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"shopping-decision-readonly-probe","version":"0.1"}}})
    obj=parse_json_or_sse(init["raw"])
    success=isinstance(obj.get("result"),dict) and init["http"]==200
    report={"operation":"mcp_tool_call_once","case":a.case,"tool":tool,"input_query":args["query"],"observed_at":datetime.now(timezone.utc).isoformat(),
            "initialization_http":init["http"],"initialization_success":success,
            "raw_response_saved":False,"credential_logged":False,"full_product_url_saved":False,
            "purchase_recommendation_approved":False,"transactions_enabled":False,"attempted_business_tool_calls":0,"automatic_retries":0}
    if success:
        session=init["session"]
        notification=req(key,{"jsonrpc":"2.0","method":"notifications/initialized"},session)
        report["initialized_notification_http"]=notification["http"]
        report["attempted_business_tool_calls"]=1
        tool_response=req(key,{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":tool,"arguments":args}},session)
        report["rpc_http"]=tool_response["http"]
        report["response_len"]=len(tool_response["raw"])
        report["response_sha256"]=hashlib.sha256(tool_response["raw"]).hexdigest() if tool_response["raw"] else None
        rpc=parse_json_or_sse(tool_response["raw"])
        rpc_result=rpc.get("result") if isinstance(rpc,dict) else None
        report["rpc_is_error"]=rpc_result.get("isError") if isinstance(rpc_result,dict) else None
        report["rpc_error_present"]="error" in rpc
        business=parse_content(rpc)
        report["parsed_result_type"]=type(business).__name__
        report["business_code"]=business.get("error_code") if isinstance(business,dict) and type(business.get("error_code")) is int else None
        report["structure"]=structure(business)
        report["identity_field_occurrences"]=audit_values(business)
        report["title_brand_store_excerpts"]=safe_descriptions(business)
        report["sku_entities"]=sku_summary(business)
        report["business_container_keys"]=list(business)[:40] if isinstance(business,dict) else None
    report["elapsed_seconds"]=round(time.monotonic()-start,3)
    rendered=json.dumps(report,ensure_ascii=False,indent=2)
    if key in rendered:raise SystemExit("redaction_failed")
    with out.open("x",encoding="utf-8") as f:f.write(rendered+"\n")
    print(json.dumps({"case":a.case,"tool":tool,"init":success,"http":report.get("rpc_http"),"rpc_is_error":report.get("rpc_is_error"),"business_code":report.get("business_code"),"parsed_result_type":report.get("parsed_result_type"),"structure_paths":[x["path"] for x in report.get("structure",[])][:70],"identity_field_count":len(report.get("identity_field_occurrences",[])),"out":str(out.relative_to(ROOT))},ensure_ascii=False))

if __name__=="__main__":
    main()
