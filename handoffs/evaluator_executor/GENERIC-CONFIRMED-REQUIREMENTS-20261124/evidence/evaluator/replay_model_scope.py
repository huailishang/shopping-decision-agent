"""Check adjacent offline variants of the public comparison's exact-model binding."""

from copy import deepcopy
import json
from pathlib import Path
import runpy
import sys


TASK = Path(__file__).resolve().parents[2]
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))

from shopping_decision.confirmed_comparison import publish_confirmed_comparison
from shopping_decision.evidence_comparison import SAFE_FLAGS


def evaluate(transfer, fact_scope):
    bundle, requirements = transfer["base_case"]()
    short = "lab-kettle-x"
    exact = "lab-kettle-x-plus"
    bundle["candidates"] = [{"id": exact}, {"id": short}]
    bundle["requirements"].reverse()
    for source in bundle["sources"]:
        source.update(type="official_exact_model_document", scope_models=[short, exact],
                      observed_at="2026-11-21T09:00:00+08:00",
                      url="https://catalog.invalid/test-only")
    height, volume = bundle["facts"]
    height.update(id="short-height", candidate_id=short, kind="official_feature")
    if fact_scope is not None:
        height["scope_models"] = fact_scope
    volume.update(id="short-volume", candidate_id=short, kind="official_feature")
    bundle["facts"] = [dict(volume, id="exact-volume", candidate_id=exact),
                       height,
                       dict(height, id="exact-height", candidate_id=exact, scope_models=[exact]),
                       volume]
    result = publish_confirmed_comparison(
        deepcopy(bundle), deepcopy(requirements), as_of=transfer["TODAY"],
        deployment_region=transfer["DEPLOYMENT"])
    return {"bundle": bundle, "requirements": requirements, "result": result}


def status(case, candidate, dimension):
    return next((row["status"] for row in (case["result"] or {}).get("claims", [])
                 if row["candidate_id"] == candidate and row["dimension"] == dimension), None)


def qualification(case, candidate):
    return next((row["research_status"] for row in (case["result"] or {}).get("assessments", [])
                 if row["candidate_id"] == candidate), None)


def main():
    transfer = runpy.run_path(str(TASK / "VERIFY_TRANSFER.py"))
    short = "lab-kettle-x"
    exact = "lab-kettle-x-plus"
    height = transfer["HEIGHT"]
    cases = {
        "candidate_bound_as_list": evaluate(transfer, [short]),
        "other_exact_model_as_list": evaluate(transfer, [exact]),
        "other_exact_model_as_string": evaluate(transfer, exact),
    }
    malformed = cases["other_exact_model_as_string"]
    clean = cases["candidate_bound_as_list"]
    narrow = cases["other_exact_model_as_list"]
    chat_replay = runpy.run_path(str(
        TASK.parent / "PRINTER-CHAT-CONTEXT-20261124" / "evidence" / "evaluator" /
        "replay_session_conditions.py"))
    state, bundle = chat_replay["cases"]()["positive_control"]
    bundle["facts"][1]["scope_models"] = "review-model-plus"
    chat = chat_replay["replay"](state, bundle)
    checks = {
        "valid_list_and_reordered_candidates_keep_their_claims":
            status(clean, short, height) == status(clean, exact, height) == "met",
        "foreign_exact_scope_in_list_leaves_short_model_pending":
            status(narrow, short, height) == "unknown"
            and qualification(narrow, short) == "pending_evidence"
            and status(narrow, exact, height) == "met"
            and status(narrow, short, "capacity") == "met",
        "foreign_exact_scope_in_string_cannot_prove_short_model":
            status(malformed, short, height) != "met"
            and qualification(malformed, short) != "eligible_for_research",
        "printing_chat_cannot_use_a_foreign_model_feature":
            chat_replay["status"](chat, "wx") != "met"
            and all(row["research_status"] != "eligible_for_research"
                    for row in chat["assessments"]),
        "safety_flags": all(all(comparison[key] is False for key in SAFE_FLAGS)
                            for case in cases.values()
                            if (comparison := case["result"]) is not None),
    }
    print(json.dumps({"checks": checks, "cases": cases,
                      "printer": {"state": state, "bundle": bundle, "chat": chat}},
                     ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
