"""Independent local audit of archived Haina evidence; no network or credentials."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))
def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()

index_path = "reports/haina_api_deep_probe_index_20261114.json"
catalog_path = "reports/haina_mcp_tool_catalog_20261114.json"
index, catalog = read(index_path), read(catalog_path)
checks = []
for group in ("product_probes", "mcp_probes"):
    for row in index[group]:
        source = read(row["path"])
        checks.append({
            "path": row["path"],
            "archive_sha256": sha(row["path"]),
            "archive_digest_matches_index": sha(row["path"]) == row["sha256"],
            "claimed_raw_response_sha256": source.get("response_sha256"),
            "http": source.get("rpc_http", source.get("http_status")),
            "business_code": source.get("business_code"),
            "raw_response_saved": source.get("raw_response_saved"),
        })
assert len(checks) == 18
assert all(x["archive_digest_matches_index"] for x in checks)
assert len(catalog["tools"]) == catalog["tools_count"] == 10

details = {}
for key in ("brother", "hp"):
    path = f"reports/haina_mcp_probe_20261114_{key}_sku_detail.json"
    data = read(path)
    assert data["business_code"] == 0 and data["rpc_http"] == 200
    assert data["raw_response_saved"] is False
    skus = [s for e in data["sku_entities"] for s in e["skus"]]
    products = [p for s in skus for p in s["products"]]
    details[key] = {
        "path": path, "archive_sha256": sha(path),
        "observed_at": data["observed_at"], "sku_groups": len(skus),
        "referenced_product_records": sum(s["sku_products_length"] for s in skus),
        "saved_product_excerpts": len(products),
        "sku_id_lengths": [s["sku_id_length"] for s in skus],
        "missing_item_id_records": sum(not p["item_id_field_present"] for p in products),
        "title_variant_dwc_records": sum("232dwc" in p["title_excerpt"].lower() for p in products),
        "multiple_model_title_records": sum("233" in p["title_excerpt"].lower() for p in products),
        "raw_response_available": False,
        "platform_identity_verified": False, "regional_quote_verified": False,
    }
assert details["brother"]["referenced_product_records"] == 2
assert details["hp"]["referenced_product_records"] == 7
assert details["hp"]["sku_id_lengths"] == [32, 32]

from shopping_decision.haina_mcp_ingest import ingest_haina_mcp_bundle, load_haina_mcp_report, SYNTHETIC_FIXTURE_PATH
from shopping_decision.sale_configuration_evidence import REAL_SALE_EVIDENCE_ENABLED
fixed_now = datetime(2026, 11, 16, 0, 0, tzinfo=timezone.utc)
blocked = ingest_haina_mcp_bundle({"source_mode":"real_response", "calls":[{"payload":object()}]}, now=fixed_now)
synthetic = load_haina_mcp_report(SYNTHETIC_FIXTURE_PATH, now=fixed_now)
assert blocked["status"] == "blocked_real_data_use_not_approved"
assert synthetic["source_mode"] == "synthetic_test" and synthetic["entity_count"] == 2
assert synthetic["platform_identity_verified_count"] == synthetic["quote_verified_count"] == 0
assert not REAL_SALE_EVIDENCE_ENABLED
for obj in (blocked, synthetic):
    assert not obj["purchase_recommendation_approved"] and not obj["transactions_enabled"]
hash_paths = [index_path, catalog_path,
    "reports/supplier_haina_mcp_docs_20261109.json",
    "reports/supplier_haina_beta_notice_20261109.json",
    "reports/P0_9_海纳数据用途矩阵与真实样本阻塞_20261110.md",
    "reports/海纳真实商品分级认定_漏检更正_20261116.md",
    "shopping_decision/haina_mcp_ingest.py",
    "shopping_decision/haina_ingest.py",
    "shopping_decision/sale_configuration_evidence.py",
    "shopping_decision/discovery_pool.py",
    "tests/fixtures/haina_mcp_synthetic_bundle.json"]
result = {
    "audit_date": "2026-11-16", "role": "independent_evaluator",
    "head": subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip(),
    "indexed_business_records": len(checks), "archive_digest_consistency": "18/18",
    "digest_limit": "index hashes match redacted archive file bytes; raw-response hashes are unverified claims without raw bytes",
    "tool_count": len(catalog["tools"]), "details": details, "archives": checks,
    "input_hashes": {p: sha(p) for p in hash_paths},
    "runtime": {"real_input_status": blocked["status"], "synthetic_entity_count": synthetic["entity_count"],
                "synthetic_status": synthetic["status"], "strict_sale_gate_enabled": REAL_SALE_EVIDENCE_ENABLED},
    "external_business_calls_this_audit": 0,
    "platform_identity_verified_this_audit": 0, "regional_quote_verified_this_audit": 0,
    "purchase_recommendation_approved": False, "transactions_enabled": False,
}
print(json.dumps(result, ensure_ascii=True, indent=2))
