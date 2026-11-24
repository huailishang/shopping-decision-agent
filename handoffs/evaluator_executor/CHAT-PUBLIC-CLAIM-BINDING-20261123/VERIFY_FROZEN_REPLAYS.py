"""Replay the previous evaluator's fixtures without writing to prior evidence."""

from datetime import date
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from shopping_decision.chat_bridge import render_chat


PREVIOUS_EVIDENCE = Path(__file__).resolve().parent.parent / "GENERIC-PUBLIC-ENTRY-COVERAGE-20261120" / "evidence"
SAFETY_FLAGS = ("purchase_recommendation_approved", "transactions_enabled", "live_price_verified")
LEGACY_PROSE = ("1300<1000", "立刻下单", "已验证河南现价", "所有证据已证实")


def load_fixture(relative_path):
    return json.loads((PREVIOUS_EVIDENCE / relative_path).read_text(encoding="utf-8"))


def replay(case):
    with (
        patch("shopping_decision.chat_bridge.date") as clock,
        patch("shopping_decision.chat_bridge._analysis", return_value=case["analysis"]),
    ):
        clock.today.return_value = date(2026, 11, 23)
        view = render_chat(case["state"])
    report = json.loads(view["report_json"])
    public = report["public_decision"] or {}
    return {
        "result_text": view["result_text"],
        "claims": public.get("claims", []),
        "safe_flags": {key: report[key] for key in SAFETY_FLAGS},
        "public_flags": {key: public[key] for key in SAFETY_FLAGS if key in public},
    }


def met_requirements(result):
    return {c["requirement_id"] for c in result["claims"] if c["status"] == "met"}


def visible_positive(result):
    return any(c["requirement_id"] == "cost" and c["status"] == "met"
               and c["claim_id"] in result["result_text"] for c in result["claims"])


def pending(result, requirement_id):
    matching = [c["status"] for c in result["claims"] if c["requirement_id"] == requirement_id]
    return matching == ["unknown"] or (not result["claims"] and "待核研究" in result["result_text"])


def main():
    r1 = load_fixture("evaluator-r1/chat-fixtures.json")
    r2 = load_fixture("evaluator-r2/chat-inputs.json")
    results = {name: replay(case) for name, case in (r1 | r2).items()}
    budget = results["budget_on_other_dimension"]
    mixed = results["mixed_quote_and_wrong_usage_region"]
    checks = {
        "purchase_budget_kept": "cost" not in met_requirements(budget)
            and "1300 ≤ 1500" not in budget["result_text"],
        "mixed_usage_keeps_its_own_region": visible_positive(mixed) and pending(mixed, "use"),
        "standalone_out_of_region_usage_pending": pending(
            results["wrong_usage_region_without_quote"], "use"),
        "future_observation_pending": pending(results["quote_observation_after_display_date"], "cost"),
        "matching_quote_visible": visible_positive(results["delivery_positive"]),
        "original_synthetic_claim_visible": visible_positive(results["positive_synthetic"]),
        "original_negative_cases_pending": all(
            pending(results[name], "cost") for name in r1 if name != "positive_synthetic"
        ),
        "legacy_prose_not_released": all(
            not any(phrase in result["result_text"] for phrase in LEGACY_PROSE)
            for result in results.values()
        ),
        "no_purchase_transaction_or_live_price_verification": all(
            value is False for result in results.values() for field in ("safe_flags", "public_flags")
            for value in result[field].values()
        ),
    }
    print(json.dumps({"checks": checks, "results": results}, ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
