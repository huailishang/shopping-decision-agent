"""Independently constructed offline fixtures for the public chat result."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys


TASK = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("frozen_replays", TASK / "VERIFY_FROZEN_REPLAYS.py")
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)


def bundle(case):
    return case["analysis"]["verified_research_bundle"]


def fixtures():
    old = frozen.load_fixture("evaluator-r2/chat-inputs.json")
    controls = {}
    reference = deepcopy(old["mixed_quote_and_wrong_usage_region"])
    controls["separate_henan_quote_and_japan_usage"] = reference

    unrelated_quote = deepcopy(reference)
    quote = deepcopy(bundle(unrelated_quote)["facts"][0])
    quote.update(id="unrelated_quote", dimension="wechat_print")
    bundle(unrelated_quote)["facts"].append(quote)

    compatible = deepcopy(reference)
    bundle(compatible)["sources"][1]["scope_region"] = "日本"
    bundle(compatible)["facts"][1]["scope_region"] = "日本"
    controls["confirmed_japan_feature"] = compatible
    compatible_contaminated = deepcopy(compatible)
    bundle(compatible_contaminated)["facts"].append(deepcopy(quote))

    duplicate = deepcopy(compatible)
    bundle(duplicate)["requirements"][1]["id"] = "cost"
    missing_source = deepcopy(old["delivery_positive"])
    bundle(missing_source)["sources"][0]["id"] = ["s"]
    negative_price = deepcopy(old["delivery_positive"])
    bundle(negative_price)["facts"][0]["value"] = -1

    return controls | {
        "wrong_unit_quote_cannot_admit_wrong_usage_region": unrelated_quote,
        "wrong_unit_quote_cannot_hide_correct_usage_region": compatible_contaminated,
        "duplicate_requirement_ids_fail_closed": duplicate,
        "malformed_source_id_falls_back": missing_source,
        "negative_purchase_price_is_pending": negative_price,
    }


def attempt(case):
    try:
        return frozen.replay(case)
    except (ValueError, TypeError, KeyError) as exc:
        return {"exception": type(exc).__name__, "message": str(exc)}


def status(result, requirement):
    return [claim["status"] for claim in result.get("claims", [])
            if claim["requirement_id"] == requirement]


def pending(result, requirement):
    return "exception" not in result and frozen.pending(result, requirement)


def main():
    cases = fixtures()
    results = {name: attempt(case) for name, case in cases.items()}
    scope = results["wrong_unit_quote_cannot_admit_wrong_usage_region"]
    eligible = results["wrong_unit_quote_cannot_hide_correct_usage_region"]
    reference = results["separate_henan_quote_and_japan_usage"]
    compatible = results["confirmed_japan_feature"]
    duplicate = results["duplicate_requirement_ids_fail_closed"]
    malformed = results["malformed_source_id_falls_back"]
    negative = results["negative_purchase_price_is_pending"]
    checks = {
        "separate_henan_quote_and_japan_usage": status(reference, "cost") == ["met"]
            and status(reference, "use") == ["unknown"],
        "confirmed_japan_feature": status(compatible, "cost") == ["met"]
            and status(compatible, "use") == ["met"],
        "wrong_unit_quote_cannot_admit_wrong_usage_region": status(scope, "cost") == ["met"]
            and status(scope, "use") == ["unknown"],
        "wrong_unit_quote_cannot_hide_correct_usage_region": status(eligible, "cost") == ["met"]
            and status(eligible, "use") == ["met"],
        "duplicate_requirement_ids_fail_closed": pending(duplicate, "cost") and not duplicate.get("claims"),
        "malformed_source_id_falls_back": pending(malformed, "cost") and not malformed.get("claims"),
        "negative_purchase_price_is_pending": pending(negative, "cost"),
        "safety_flags_for_rendered_cases": all(
            set(result["safe_flags"]) == set(frozen.SAFETY_FLAGS)
            and all(value is False for field in ("safe_flags", "public_flags") for value in result[field].values())
            for result in results.values() if "exception" not in result),
    }
    print(json.dumps({"checks": checks, "cases": cases, "results": results}, ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    sys.exit(main())
