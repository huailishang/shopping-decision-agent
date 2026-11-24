"""Frozen offline comparison of the old entry and the shared confirmed-condition entry."""

import argparse
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import runpy
import sys


TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))

from shopping_decision.claim_gate import publish_checked_comparison
from shopping_decision.evidence_comparison import SAFE_FLAGS


TODAY = "2026-11-23"
DEPLOYMENT = "中国大陆"
MODEL = "synthetic-kettle"
ELIGIBLE = "eligible_for_research"
EXCLUDED = "excluded_for_research"
PENDING = "pending_evidence"
HEIGHT = "height_with_base"


def millimetres(value, unit):
    scale = {"cm": Decimal(10), "mm": Decimal(1)}
    return format(Decimal(str(value)) * scale[unit], "f")


def make_fact(fact_id, dimension, value, unit, source_id):
    return {
        "id": fact_id, "candidate_id": MODEL, "source_id": source_id,
        "dimension": dimension, "value": value, "unit": unit, "kind": "synthetic_probe",
        "statement": "冻结离线样例", "limitations": "无真实产品证明",
    }


def base_case():
    confirmed = [
        {"id": "shelf", "dimension": HEIGHT, "op": "lte",
         "value": millimetres(23, "cm"), "unit": "mm", "importance": "hard"},
        {"id": "volume", "dimension": "capacity", "op": "gte",
         "value": 1.5, "unit": "L", "importance": "hard"},
    ]
    source = {
        "url": "https://kettle-evaluation.invalid/spec", "captured_on": "2026-11-21",
        "scope_region": DEPLOYMENT, "allowed_use": "model_research_short_summary",
        "limitations": "合成规格表",
    }
    bundle = {
        "schema_version": 1, "request_id": "offline-kettle-fit", "category": "kettle",
        "as_of": TODAY, "region": DEPLOYMENT, "candidates": [{"id": MODEL}],
        "requirements": deepcopy(confirmed),
        "sources": [dict(source, id="spec-height"), dict(source, id="spec-volume")],
        "facts": [
            make_fact("with-base", HEIGHT, millimetres(230, "mm"), "mm", "spec-height"),
            make_fact("volume", "capacity", 1.8, "L", "spec-volume"),
        ],
    }
    return bundle, confirmed


def fixtures():
    variations = {
        "exact_boundary": ("met", ELIGIBLE),
        "above_limit": ("failed", EXCLUDED),
        "body_only": ("unknown", PENDING),
        "omitted_height": ("unknown", PENDING),
        "loosened_threshold": ("failed", EXCLUDED),
        "softened_height": ("failed", EXCLUDED),
        "expired_height": ("unknown", PENDING),
        "conflicting_height": ("conflict", PENDING),
        "confirmed_limit_changed": ("failed", EXCLUDED),
    }
    for name, expected in variations.items():
        bundle, confirmed = base_case()
        height = bundle["facts"][0]
        height_row = bundle["requirements"][0]
        if name in ("above_limit", "loosened_threshold", "softened_height"):
            height["value"] = millimetres(240, "mm")
        if name == "body_only":
            height.update(dimension="height_without_base", value=millimetres(21, "cm"))
        elif name == "omitted_height":
            bundle["requirements"].pop(0)
            bundle["facts"].pop(0)
        elif name == "loosened_threshold":
            height_row["value"] = millimetres(30, "cm")
        elif name == "softened_height":
            height_row["importance"] = "soft"
        elif name == "expired_height":
            bundle["sources"][0]["valid_until"] = "2026-11-22"
        elif name == "conflicting_height":
            bundle["facts"].append(dict(height, id="other-height", value=millimetres(24, "cm")))
        elif name == "confirmed_limit_changed":
            height["value"] = millimetres(220, "mm")
            confirmed[0]["value"] = millimetres(21, "cm")
        yield name, bundle, confirmed, expected


def pick_claim(result, dimension):
    return next((c for c in result.get("claims", [])
                 if c["candidate_id"] == MODEL and c["dimension"] == dimension), {})


def compare_case(compare, bundle, confirmed, expected):
    result = compare(deepcopy(bundle), deepcopy(confirmed)) or {}
    height = pick_claim(result, HEIGHT)
    capacity = pick_claim(result, "capacity")
    candidate = next((a for a in result.get("assessments", [])
                      if a["candidate_id"] == MODEL), {})
    height_status = height.get("status")
    scope_valid = (
        height_status == "unknown"
        or (height.get("claim_id") and height.get("source_audit")
            and height.get("scope", {}).get("region") == DEPLOYMENT)
    )
    passed = bool((height_status, candidate.get("research_status")) == expected
                  and height.get("claim_id")
                  and capacity.get("status") == "met" and capacity.get("claim_id")
                  and capacity.get("supporting_fact_ids") == ["volume"]
                  and scope_valid and all(result.get(key) is False for key in SAFE_FLAGS))
    return {"passed": passed, "expected_height_and_qualification": expected,
            "inputs": {"bundle": bundle, "confirmed": confirmed}, "comparison": result}


def shared_chat_call(function):
    script = TASK.parent / "PRINTER-CHAT-CONTEXT-20261124" / "evidence" / "evaluator" / (
        "replay_session_conditions.py")
    replay = runpy.run_path(str(script))
    state, bundle = replay["cases"]()["positive_control"]
    observed = []

    def profile(frame, event, _arg):
        if event == "call" and frame.f_code is function.__code__:
            observed.append(frame.f_code.co_name)

    prior = sys.getprofile()
    try:
        sys.setprofile(profile)
        output = replay["replay"](state, bundle)
    finally:
        sys.setprofile(prior)
    return {"passed": bool(observed) and any(
        claim["status"] == "met" and claim["claim_id"] in output["text"]
        for claim in output["claims"]), "calls": observed, "chat": output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    if args.baseline:
        def compare(bundle, _confirmed):
            return publish_checked_comparison(bundle)
    else:
        from shopping_decision.confirmed_comparison import publish_confirmed_comparison

        def compare(bundle, confirmed):
            return publish_confirmed_comparison(
                bundle, confirmed, as_of=TODAY, deployment_region=DEPLOYMENT)

    results = {name: compare_case(compare, bundle, confirmed, expected)
               for name, bundle, confirmed, expected in fixtures()}
    if not args.baseline:
        results["normal_printer_chat_uses_shared_function"] = shared_chat_call(
            publish_confirmed_comparison)
    checks = {name: result["passed"] for name, result in results.items()}
    print(json.dumps({"baseline": args.baseline, "checks": checks, "results": results},
                     ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
