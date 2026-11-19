"""汇总2026-11-14已落盘的海纳脱敏实测记录，不访问网络、不读取凭证。"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parent.parent
REPORT=ROOT/"reports"
OUT=REPORT/"haina_api_deep_probe_index_20261114.json"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if OUT.exists():raise SystemExit("index_exists_no_overwrite")
    product_files=sorted(REPORT.glob("haina_probe_20261114_*.json"))
    mcp_files=sorted(REPORT.glob("haina_mcp_probe_20261114_*.json"))
    catalog=REPORT/"haina_mcp_tool_catalog_20261114.json"
    products=[]
    for p in product_files:
        d=json.loads(p.read_text(encoding="utf-8"))
        products.append({"case":d["probe_case"],"status":d.get("status"),"http":d.get("http_status"),
                         "business_code":d.get("business_code"),"rows":d.get("rows_returned"),
                         "id_rows":d.get("explicit_item_or_sku_field_count"),
                         "sha256":sha(p),"path":str(p.relative_to(ROOT)).replace("\\","/")})
    mcp=[]
    for p in mcp_files:
        d=json.loads(p.read_text(encoding="utf-8"))
        item={"case":d["case"],"tool":d["tool"],"http":d.get("rpc_http"),"business_code":d.get("business_code"),
              "is_error":d.get("rpc_is_error"),"attempted_business_tool_calls":d.get("attempted_business_tool_calls"),
              "sha256":sha(p),"path":str(p.relative_to(ROOT)).replace("\\","/")}
        entities=d.get("sku_entities")
        if isinstance(entities,list):
            item["sku_entities"]=[{"name":e.get("entity_name"),
                                  "spu_id_present":e.get("spu_id_present"),
                                  "sku_count_reported":e.get("sku_count_reported"),
                                  "sku_list_length":e.get("sku_list_length"),
                                  "sku_positive":sum(bool(x.get("sku_id_present")) for x in e.get("skus",[])),
                                  "referenced_shop_products":sum(x.get("sku_products_length") or 0 for x in e.get("skus",[])),
                                  "platform_ids_all_numeric":[p.get("item_id_all_digits") for s in e.get("skus",[]) for p in s.get("products",[])]
                                  } for e in entities]
        mcp.append(item)
    index={"run_date":"2026-11-14","role":"executor","evidence":"actual_local_api_calls_with_credential_redacted",
           "business_calls":sum(int(x.get("attempted_business_tool_calls") or 0) for x in mcp)+len(products),
           "product_calls":len(products),"mcp_business_calls":len(mcp),"mcp_metadata_calls":3,
           "product_successes":sum(x["status"]=="success" and x["http"]==200 and x["business_code"]==0 for x in products),
           "mcp_successes":sum(x["http"]==200 and x["business_code"]==0 and x["is_error"] is False for x in mcp),
           "real_originals_ingested":0,"purchase_recommendation_approved":False,"transactions_enabled":False,
           "real_platform_sale_identity_verified":0,"regional_quote_verified":0,
           "raw_responses_saved":False,"credentials_logged":False,"retailer_pages_opened":0,"account_logins":0,"paid_calls":"not_audited_unknown_test_key_quota",
           "product_probes":products,"mcp_probes":mcp,
           "mcp_catalog":{"path":str(catalog.relative_to(ROOT)).replace("\\","/"),
                          "sha256":sha(catalog),"tools_count":json.loads(catalog.read_text(encoding="utf-8")).get("tools_count")}}
    rendered=json.dumps(index,ensure_ascii=False,indent=2)
    with OUT.open("x",encoding="utf-8") as f:f.write(rendered+"\n")
    print(json.dumps({"business_calls":index["business_calls"],"product_calls":index["product_calls"],"product_successes":index["product_successes"],"mcp_business_calls":index["mcp_business_calls"],"mcp_successes":index["mcp_successes"],"index":str(OUT.relative_to(ROOT))},ensure_ascii=False))

if __name__=="__main__":
    main()
