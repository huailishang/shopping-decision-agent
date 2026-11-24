"""Independent scope and good-neighbour checks using the real shared comparator."""

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


def main():
    prior = TASK.parent / "GENERIC-CONFIRMED-REQUIREMENTS-20261124"
    transfer = runpy.run_path(str(prior / "VERIFY_TRANSFER.py"))
    model = transfer["MODEL"]
    other = model + "-EU"
    bundle, requirements = transfer["base_case"]()
    bundle["candidates"].insert(0, {"id": other})
    bundle["requirements"].reverse()
    height, volume = bundle["facts"]
    height_source = bundle["sources"][0]
    height_source["scope_models"] = [model]
    padded_source = dict(height_source, id="padded-scope",
                         scope_models=[model, other + " "])
    bundle["sources"].insert(0, padded_source)
    height["scope_models"] = [model]
    bundle["facts"] = [
        dict(height, id="invalid-oversize", source_id="padded-scope", value="400"),
        dict(height, id="foreign-scope", candidate_id=other, scope_models=[other]),
        dict(volume, id="other-volume", candidate_id=other),
        volume,
        height,
    ]
    pristine = deepcopy(bundle)
    result = publish_confirmed_comparison(
        bundle, requirements, as_of=transfer["TODAY"], deployment_region=transfer["DEPLOYMENT"])
    claims = {(c["candidate_id"], c["dimension"]): c for c in result["claims"]}
    good_height = claims[model, transfer["HEIGHT"]]
    unknown_height = claims[other, transfer["HEIGHT"]]
    states = {item["candidate_id"]: item["research_status"] for item in result["assessments"]}
    checks = {
        "padded_source_list_cannot_conflict_with_valid_height":
            good_height["status"] == "met" and good_height["supporting_fact_ids"] == ["with-base"]
            and states[model] == "eligible_for_research",
        "source_scope_and_fact_scope_must_intersect":
            unknown_height["status"] == "unknown" and states[other] == "pending_evidence",
        "valid_capacity_remains_for_both": all(
            claims[candidate, "capacity"]["status"] == "met" for candidate in (model, other)),
        "input_audit_stays_unchanged": bundle == pristine,
        "safety_flags_stay_false": all(result[key] is False for key in SAFE_FLAGS),
    }
    print(json.dumps({"checks": checks, "inputs": pristine, "requirements": requirements,
                      "result": result}, ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
