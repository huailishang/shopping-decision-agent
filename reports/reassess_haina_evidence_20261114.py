"""离线复核既有海纳实测材料；不读取凭证，不执行探针，不访问网络。

输出必须为新文件。文件哈希一致只证明本地记录对应，不能验证已丢弃的HTTP原文。
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    if len(sys.argv) != 3 or sys.argv[1] != "--output":
        raise SystemExit("usage: python -m reports.reassess_haina_evidence_20261114 --output NEW_FILE.json")
    output = Path(sys.argv[2]).resolve()
    if output.exists():
        raise SystemExit("output_exists_no_overwrite")
    index_path = REPORTS / "haina_api_deep_probe_index_20261114.json"
    index = read(index_path)
    catalog_path = ROOT / index["mcp_catalog"]["path"]
    entries = index["product_probes"] + index["mcp_probes"]
    protected = [index_path, catalog_path] + [ROOT / x["path"] for x in entries]
    protected += [REPORTS / n for n in (
        "haina_api_field_probe_20261114.py", "haina_mcp_tool_probe_20261114.py",
        "haina_mcp_tool_catalog_probe_20261114.py", "build_haina_probe_index_20261114.py")]
    protected += sorted((ROOT / "shopping_decision").rglob("*.py"))
    before = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in protected}
    records = []
    data = {}
    for entry in entries:
        path = ROOT / entry["path"]
        d = read(path)
        data[entry["case"]] = d
        is_mcp = "tool" in entry
        successful = d.get("business_code") == 0 and (
            d.get("rpc_http") == 200 and d.get("rpc_is_error") is False
            and d.get("rpc_error_present") is False if is_mcp else
            d.get("http_status") == 200 and d.get("status") == "success")
        records.append({
            "case": entry["case"], "path": entry["path"],
            "artifact_hash_matches_index": sha(path) == entry["sha256"],
            "stored_success_record": successful,
            "attempts": d.get("attempted_business_tool_calls") if is_mcp else d.get("request_attempts"),
            "observed_at": d.get("observed_at"),
            "response_sha256": d.get("response_sha256"),
        })
    catalog = read(catalog_path)
    hp = data["hp_sku_detail"]["sku_entities"][0]
    hp_products = [p for s in hp["skus"] for p in s["products"]]
    brother_entities = [data[c]["sku_entities"][0] for c in ("brother_sku_detail", "brother_alt_sku")]
    parameter_shapes = {}
    comment_shapes = {}
    for brand in ("hp", "brother"):
        parameter = data[brand + "_param"]
        comment = data[brand + "_comment"]
        parameter_shapes[brand] = {
            "reported_parameters": next(x["length"] for x in parameter["structure"]
                                        if x["path"] == "data[].entity_parameter"),
            "parameter_values_saved": False,
            "per_parameter_sources_saved": False,
        }
        titles = [x["value_excerpt"] for x in comment["title_brand_store_excerpts"] if x["field"] == "title"]
        comment_shapes[brand] = {
            "reported_dimensions": next(x["length"] for x in comment["structure"]
                                       if x["path"] == "data[].entity_comments"),
            "saved_title_excerpts": len(titles), "distinct_title_excerpts": len(set(titles)),
            "viewpoint_values_and_source_urls_saved": False,
            "independent_source_count": None,
        }

    # 不导入执行者网络探针。以现有真实脱敏记录核准入行为，不伪装成原始商品响应。
    from shopping_decision import discovery_pool, haina_ingest, sale_configuration_evidence
    from shopping_decision.h05_probes import run_negative_probes
    blocked = []
    with patch.object(socket.socket, "connect", side_effect=AssertionError("offline_review_network_forbidden")), \
            patch.object(socket, "create_connection", side_effect=AssertionError("offline_review_network_forbidden")):
        for case in ("hp_sku_detail", "brother_sku_detail", "brother_alt_sku"):
            pool = discovery_pool.build_discovery_pool([data[case]], now=datetime.now(timezone.utc))
            blocked.append({"case": case, "candidate_count": pool["candidate_count"],
                            "unverified_leads": pool["unverified_source_lead_count"],
                            "blocked_reports": pool["blocked_report_count"],
                            "purchase_recommendation_approved": pool["purchase_recommendation_approved"],
                            "transactions_enabled": pool["transactions_enabled"]})
        suite = unittest.defaultTestLoader.loadTestsFromNames([
            "tests.test_p0_9_trust", "tests.test_p0_9_r12_gate"])
        test_output = io.StringIO()
        tests = unittest.TextTestRunner(stream=test_output, verbosity=1).run(suite)
        negatives = run_negative_probes(today=date(2026, 11, 14))

    after = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in protected}
    mcp_data = [data[x["case"]] for x in index["mcp_probes"]]
    mcp_metadata = 3 + sum(int(d.get("initialization_success") is True)
                           + int(d.get("initialized_notification_http") == 202) for d in mcp_data)
    checks = {
        "18_record_files_match_index": len(records) == 18 and all(x["artifact_hash_matches_index"] for x in records),
        "18_success_records_and_single_attempt": all(x["stored_success_record"] and x["attempts"] == 1 for x in records),
        "catalog_hash_and_10_unique_tools": sha(catalog_path) == index["mcp_catalog"]["sha256"]
            and len(catalog["tools"]) == 10 and len({t["name"] for t in catalog["tools"]}) == 10,
        "original_artifacts_and_business_code_unchanged": before == after,
        "raw_mcp_audits_are_not_cli_reports": all(x["candidate_count"] == 0 and x["unverified_leads"] == 0
            and x["blocked_reports"] == 1 and not x["purchase_recommendation_approved"]
            and not x["transactions_enabled"] for x in blocked),
        "additional_focused_tests_pass": tests.wasSuccessful(),
        "existing_negative_cases_pass_at_review_date": negatives["summary"]["passed"] == negatives["summary"]["total"],
    }
    result = {
        "role": "independent_evaluator", "review_date": "2026-11-14",
        "scope": "offline_existing_audits_not_new_live_api_or_unseen_accuracy_evaluation",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "checks": checks, "records": records,
        "counts": {"rest_records": len(index["product_probes"]), "mcp_business_records": len(mcp_data),
                   "unique_sku_queries": len({d["input_query"] for d in mcp_data if d["tool"] == "product_sku_search"}),
                   "mcp_business_by_tool": dict(Counter(d["tool"] for d in mcp_data)),
                   "unique_response_hashes": len({x["response_sha256"] for x in records}),
                   "standalone_catalog_metadata_requests": 3,
                   "mcp_metadata_request_attempts_from_scripts_and_records": mcp_metadata,
                   "total_application_http_request_attempts_from_scripts_and_records": 18 + mcp_metadata,
                   "transport_wire_requests_and_billing": "not_independently_audited"},
        "hp_sku_evidence": {
            "nonempty_spu": hp["spu_id_present"],
            "nonempty_sku_groups": sum(s["sku_id_present"] for s in hp["skus"]),
            "reported_associated_products": sum(s["sku_products_length"] for s in hp["skus"]),
            "saved_product_summaries": len(hp_products),
            "saved_summaries_without_url_host": sum(p["url_host"] is None for p in hp_products),
            "saved_summaries_with_empty_sku_prop": sum(not p["sku_prop_excerpt"] for p in hp_products),
            "sku_axis_values_saved": False,
            "near_model_m232dwc_summaries": sum(bool(re.search(r"(?<![A-Z0-9])M?232DWC(?![A-Z0-9])", p["title_excerpt"].upper())) for p in hp_products),
            "platform_native_id_mapping_proven": False,
        },
        "brother_sku_evidence": [{
            "query": entity["entity_name"], "nonempty_spu": entity["spu_id_present"],
            "nonempty_sku_groups": sum(s["sku_id_present"] for s in entity["skus"]),
            "saved_products": sum(len(s["products"]) for s in entity["skus"]),
            "nonempty_product_ids": sum(p["item_id_field_present"] for s in entity["skus"] for p in s["products"]),
        } for entity in brother_entities],
        "parameter_evidence": parameter_shapes, "comment_evidence": comment_shapes,
        "current_business_gates": {"real_response_import_enabled": haina_ingest.REAL_RESPONSE_IMPORT_ENABLED,
            "real_sale_evidence_enabled": sale_configuration_evidence.REAL_SALE_EVIDENCE_ENABLED,
            "hp_model_syntax_supported": {
                "haina_ingest": haina_ingest._MODEL.search("HP M232dw") is not None,
                "discovery_pool": discovery_pool._HAINA_MODEL.fullmatch("M232dw") is not None,
                "sale_configuration": sale_configuration_evidence._MODEL.fullmatch("M232dw") is not None},
            "direct_mcp_audit_replays": blocked},
        "additional_focused_tests": {"modules": ["tests.test_p0_9_trust", "tests.test_p0_9_r12_gate"],
            "total": tests.testsRun, "failures": len(tests.failures), "errors": len(tests.errors),
            "stdout": test_output.getvalue()},
        "existing_negative_diagnostic": negatives,
        "protected_input_hashes": before,
        "limits": ["HTTP原文未保留，不能重算原响应哈希或证明服务端真实性",
                   "记录一致和既有负向回归不等于来源质量、覆盖率或推荐准确率",
                   "本轮未读取凭证、重跑业务API、修改业务门禁或执行交易"],
    }
    with output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"checks": checks, "additional_tests": tests.testsRun,
                      "negative_summary": negatives["summary"], "output": str(output)}, ensure_ascii=False))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
