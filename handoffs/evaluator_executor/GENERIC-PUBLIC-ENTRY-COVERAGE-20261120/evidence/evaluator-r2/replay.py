"""Run from the repository root with python3 -X utf8 - < path/to/replay.py."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
from unittest.mock import patch

from shopping_decision.chat_bridge import confirmed_values, render_chat, submit_message
from shopping_decision.evidence_comparison import digest


out = Path("handoffs/evaluator_executor/GENERIC-PUBLIC-ENTRY-COVERAGE-20261120/evidence/evaluator-r2")
fixture_path = out.parent / "evaluator-r1" / "chat-fixtures.json"
fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
bundle_key = "verified_research_bundle"
flags = ("purchase_recommendation_approved", "transactions_enabled", "live_price_verified")
forbidden = ("1300<1000", "立刻下单", "已验证河南现价", "所有证据已证实")


def replay(state, analysis=None):
    with patch("shopping_decision.chat_bridge.date") as clock:
        clock.today.return_value = date(2026, 11, 23)
        if analysis is None:
            view = render_chat(state)
        else:
            with patch("shopping_decision.chat_bridge._analysis", return_value=analysis):
                view = render_chat(state)
    report = json.loads(view["report_json"])
    public = report["public_decision"] or {}
    return {
        "status": view["status"],
        "confirmed": report["confirmed_fields"],
        "text": view["result_text"],
        "claims": [
            {key: row[key] for key in ("requirement_id", "status", "claim_id", "scope",
                                       "source_grade", "rule_expression")}
            for row in public.get("claims", [])
        ],
        "audit_legacy_report": (report["research_result"] or {}).get("research_case", {}).get("report_text"),
        "flags": {key: report[key] for key in flags},
        "public_flags": {key: public[key] for key in flags if key in public},
    }


def run(case):
    return replay(case["state"], case["analysis"])


def met_ids(row):
    return {claim["requirement_id"] for claim in row["claims"] if claim["status"] == "met"}


def set_condition(case, field, value):
    case["state"] = submit_message(case["state"], field, value)
    case["analysis"][bundle_key].update(
        dialogue_version=case["state"]["version"],
        confirmed_values_sha256=digest(confirmed_values(case["state"])),
    )


results = {"frozen": {name: run(item) for name, item in fixtures.items()}}
frozen = results["frozen"]
checks = {
    "frozen_positive_has_visible_id": met_ids(frozen["positive_synthetic"]) == {"cost"} and
        all(c["claim_id"] in frozen["positive_synthetic"]["text"] for c in frozen["positive_synthetic"]["claims"]),
    "frozen_negatives_do_not_publish_met": all(not met_ids(row) for name, row in frozen.items()
                                              if name != "positive_synthetic"),
    "legacy_in_audit_only": all("立刻下单" in row["audit_legacy_report"] and
                                not any(word in row["text"] for word in forbidden) for row in frozen.values()),
}

suite = json.loads(Path("handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/cases.json")
                   .read_text(encoding="utf-8"))["cases"]
state = deepcopy(fixtures["positive_synthetic"]["state"])
delivered = {}
for index, count in enumerate((2, 1, 0)):
    state["research_context"] = deepcopy(suite[index]["input"]["research_context"])
    delivered[f"count_{count}"] = replay(state)
state["research_context"] = deepcopy(suite[0]["input"]["research_context"])
optional = submit_message(state, "wechat_required", "不是必须")
withdrawn = submit_message(state, "wechat_required", "暂不确定")
edited = submit_message(optional, "budget_max_cny", "800")
switched = submit_message(edited, "category", "手机")
delivered.update(optional=replay(optional), withdrawn=replay(withdrawn),
                 budget_edited=replay(edited), category_switched=replay(switched))
results["normal"] = delivered
checks["normal_research_and_current_answers"] = (
    all(f"{count}条待核研究记录" in delivered[f"count_{count}"]["text"] for count in (2, 1, 0)) and
    all(not row["claims"] for row in delivered.values()) and
    "微信打印是用户确认的必须条件" in delivered["count_2"]["text"] and
    "微信打印是用户确认的可选条件" in delivered["optional"]["text"] and
    "微信是否必须尚未确认" in delivered["withdrawn"]["text"] and
    "预算上限为800元" in delivered["budget_edited"]["text"] and
    "预算上限为1000元" not in delivered["budget_edited"]["text"] and
    delivered["category_switched"]["status"] == "unsupported" and
    "待核研究记录" not in delivered["category_switched"]["text"]
)

matching = deepcopy(fixtures["quote_missing_confirmed_delivery_region"])
quote = matching["analysis"][bundle_key]
quote["region"] = "河南"
quote["sources"][0].update(scope_region="河南", quote_region="河南", valid_until="2026-11-24")
cases = {"delivery_positive": matching}

budget = deepcopy(matching)
bundle = budget["analysis"][bundle_key]
bundle["requirements"][0].update(id="consumables", dimension="consumables")
bundle["facts"][0].update(dimension="consumables", value=100, statement="synthetic consumables 100")
bundle["requirements"].append(dict(bundle["requirements"][0], id="cost", dimension="cost", value=1500))
bundle["facts"].append(dict(bundle["facts"][0], id="purchase_quote", dimension="cost", value=1300,
                           statement="synthetic purchase quote 1300"))
cases["budget_on_other_dimension"] = budget

wrong_region = deepcopy(matching)
set_condition(wrong_region, "device_deployment_region", "日本")
bundle = wrong_region["analysis"][bundle_key]
bundle["requirements"].append({"id": "use", "dimension": "wechat_print", "op": "eq",
                               "value": True, "unit": "bool", "importance": "hard"})
bundle["sources"].append(dict(bundle["sources"][0], id="use_doc",
                              url="https://example.com/local-use",
                              limitations="synthetic manual for use in Henan only"))
bundle["facts"].append(dict(bundle["facts"][0], id="use_fact", dimension="wechat_print",
                            kind="official_feature", value=True, unit="bool", source_id="use_doc",
                            scope_region="河南", statement="synthetic feature, Henan only"))
cases["mixed_quote_and_wrong_usage_region"] = wrong_region
no_quote = deepcopy(wrong_region)
no_quote["analysis"][bundle_key]["facts"].pop(0)
cases["wrong_usage_region_without_quote"] = no_quote

future = deepcopy(matching)
future["analysis"][bundle_key]["sources"][0]["observed_at"] = "2026-11-24T08:00:00+08:00"
cases["quote_observation_after_display_date"] = future

results["additional"] = {name: run(item) for name, item in cases.items()}
additional = results["additional"]
checks.update(
    fresh_matching_quote=met_ids(additional["delivery_positive"]) == {"cost"},
    alternate_dimension_does_not_override_purchase_budget="cost" not in
        met_ids(additional["budget_on_other_dimension"]),
    off_region_usage_evidence_ignored_without_quote=not met_ids(additional["wrong_usage_region_without_quote"]),
    off_region_usage_evidence_ignored_with_quote="use" not in
        met_ids(additional["mixed_quote_and_wrong_usage_region"]),
    future_quote_cannot_be_current=not met_ids(additional["quote_observation_after_display_date"]),
    all_purchase_transaction_live_price_flags_false=all(
        value is False for rows in results.values() for row in rows.values()
        for field in ("flags", "public_flags") for value in row[field].values()),
)
for name, payload in (("chat-inputs.json", cases), ("chat-results.json", results), ("chat-checks.json", checks)):
    (out / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(checks, indent=2))
raise SystemExit(not all(checks.values()))
