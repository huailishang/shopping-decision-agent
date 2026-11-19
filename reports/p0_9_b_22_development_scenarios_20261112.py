"""P0.9-B 执行者逐样本期望对照；仅合成数据，不调用网络或账户。"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shopping_decision.sale_configuration_evidence import assess_sale_evidence_report
from tests.test_p0_9_b_evidence import MODELS, sample, report

def main():
    now = datetime.now(timezone.utc)
    seed = sample(now)
    no_anchor = deepcopy(seed["field_anchors"])
    no_anchor.pop("selected_model_id")
    # 预期由执行者独立静态标注，不通过被测函数生成；旧样本复测不计独立验收。
    scenarios = [
        ("normal_jd", {}, "accepted_synthetic"),
        ("normal_taobao_same_number", {"platform": "TAOBAO"}, "accepted_synthetic"),
        ("unsupported_platform", {"platform": "PDD"}, "platform_or_item_id_invalid"),
        ("missing_item_id", {"platform_item_id": ""}, "platform_or_item_id_invalid"),
        ("missing_selected_sku", {"selected_sku_id": None}, "selected_sku_id_missing"),
        ("invalid_sku_id", {"selected_sku_id": "bad"}, "sku_id_invalid"),
        ("multiple_models", {"title_models": ["HL-10W", "HL-B2158W"]}, "title_spec_or_selected_model_conflict"),
        ("title_spec_conflict", {"spec_models": ["HL-B2158W"]}, "title_spec_or_selected_model_conflict"),
        ("used_device", {"condition": "used"}, "not_single_new_printer"),
        ("bundle_not_single", {"selected_variant": "bundle"}, "not_single_new_printer"),
        ("consumable_not_host", {"item_kind": "toner"}, "not_single_new_printer"),
        ("missing_seller", {"seller_id": ""}, "source_or_seller_invalid"),
        ("corrupt_hash", {"source_sha256": "x" * 64}, "source_hash_invalid"),
        ("future_observation", {"observed_at": (now + timedelta(hours=1)).isoformat()}, "source_observation_invalid"),
        ("expired_field_review", {"review_valid_until": (now - timedelta(seconds=1)).isoformat()}, "review_expired"),
        ("withdrawn_review", {"review_status": "withdrawn"}, "review_withdrawn_or_unconfirmed"),
        ("uses_not_permitted", {"permitted_uses": []}, "required_local_uses_not_evidenced"),
        ("missing_model_anchor", {"field_anchors": no_anchor}, "platform_field_anchor_missing"),
        ("forged_identity_pass", {"identity_verified": True}, "unrecognized_or_forbidden_fields"),
        ("forged_price", {"price": 199}, "unrecognized_or_forbidden_fields"),
        ("url_in_evidence_reference", {"source_ref": "https://x.example"}, "source_or_seller_invalid"),
        ("model_not_in_reviewed_sources", {"selected_model_id": "HL-Z999W",
         "title_models": ["HL-Z999W"], "spec_models": ["HL-Z999W"]}, "manufacturer_model_not_reviewed"),
    ]
    checks = []
    for label, edits, expected in scenarios:
        altered = deepcopy(seed)
        altered.update(edits)
        result = assess_sale_evidence_report(report(altered), now=now, known_models=MODELS)
        actual = ("accepted_synthetic" if result["accepted_rows"] == 1
                  else result["rejected"][0]["reason"])
        passed = (actual == expected and result["real_identity_verified_count"] == 0
                  and result["verified_quote_count"] == 0
                  and result["purchase_recommendation_approved"] is False
                  and result["transactions_enabled"] is False)
        checks.append({"id": label, "modified_fields": sorted(edits), "expected": expected,
                       "actual": actual, "expectation_met": passed,
                       "real_identity_verified": 0, "new_api_calls": 0})
    output = {
        "role": "executor", "task": "P0.9-B",
        "source_mode": "synthetic_test", "observed_at": now.isoformat(),
        "development_scenarios": checks, "total": len(checks),
        "passed": sum(x["expectation_met"] for x in checks),
        "failed": [x["id"] for x in checks if not x["expectation_met"]],
        "real_identity_verified_count": 0, "real_sales_samples_processed": 0,
        "new_haina_business_api_calls": 0, "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "limits": ["人工期望只验证合成合同规则，不是独立评估者新样本",
                   "未读取原20条响应，未有平台权威所选SKU原件及合法本机用途",
                   "旧商城价格、供应商score与评论不进入硬条件或报价"],
    }
    out = ROOT / "reports/p0_9_b_22_development_scenarios_20261112.json"
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total": output["total"], "passed": output["passed"],
                      "failed": output["failed"]}, ensure_ascii=False))
    if output["failed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
