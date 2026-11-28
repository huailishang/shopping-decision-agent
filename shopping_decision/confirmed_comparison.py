"""Compare independently confirmed conditions with attributed evidence, offline."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, date as _calendar_date, datetime, timezone

from .claim_gate import publish_checked_comparison
from .evidence_comparison import digest, number, validate_bundle


def _quote_time_valid(source: dict, today: date) -> bool:
    """Source capture, timezone-aware observation and expiry must agree."""
    try:
        raw = source.get("observed_at")
        if not isinstance(raw, str):
            return False
        observed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if observed.tzinfo is None or observed.utcoffset() is None:
            return False
        local_day = observed.date()
        utc_day = observed.astimezone(timezone.utc).date()
        captured = _calendar_date.fromisoformat(source["captured_on"])
        expires = _calendar_date.fromisoformat(source["valid_until"])
    except (ValueError, TypeError, KeyError, OverflowError):
        return False
    return (local_day <= today and utc_day <= today
            and min(local_day, utc_day) <= captured <= today
            and max(local_day, captured) <= expires and today <= expires)


def _exact_model_scope(row: dict, candidate_id: str) -> bool:
    """Explicit scopes are nonempty lists of complete model IDs.

    Absence preserves existing claim-gate semantics; malformed or empty
    explicit scopes never mean unrestricted.
    """
    if "scope_models" not in row:
        return True
    models = row["scope_models"]
    return (isinstance(models, list) and bool(models)
            and all(isinstance(model, str) and bool(model.strip())
                    and model == model.strip() for model in models)
            and candidate_id in models)


def publish_confirmed_comparison(bundle, confirmed_requirements, *, as_of,
                                 deployment_region, delivery_region=None,
                                 budget_scope=None, session_values=None, deferred=(), withdrawn=()):
    """The confirmed rows alone govern thresholds, importance and eligibility.

    The complete provider bundle is checked first, even for unused rows.
    Each scoped calculation uses the existing deterministic publication gate.
    No product category or product-specific dimension is encoded here.
    """
    try:
        validate_bundle(bundle)
        requirements = deepcopy(confirmed_requirements)
        validated = deepcopy(bundle)
        validated["requirements"] = requirements
        validate_bundle(validated)
        date.fromisoformat(as_of)
    except (ValueError, TypeError, KeyError, OverflowError, AttributeError):
        return None
    facts, sources, candidates = (bundle[k] for k in ("facts", "sources", "candidates"))
    # A condition's role, not the presence of any fact, determines its
    # applicable region. Non-price facts use the device's deployment region;
    # real purchase quotes require an explicit delivery destination. The old
    # offline synthetic price probe may use deployment when no delivery is set.
    today = date.fromisoformat(as_of)
    delivery, deployment = delivery_region, deployment_region
    source_by_id = {s["id"]: s for s in sources}
    pieces = []
    try:
        for req in requirements:
            dimension = req["dimension"]
            price_condition = dimension == "cost" and req["unit"] == "CNY"
            applicable = (delivery or deployment) if price_condition else deployment
            region_known = isinstance(applicable, str) and bool(applicable.strip())
            scoped = deepcopy(bundle)
            scoped["requirements"] = [deepcopy(req)]
            scoped["facts"] = [deepcopy(f) for f in facts
                               if f["dimension"] == dimension and f["unit"] == req["unit"]
                               and not req.get("requires_manual_resolution")]
            scoped["region"] = applicable if region_known else bundle["region"]
            scoped["as_of"] = today.isoformat()

            for fact in scoped["facts"]:
                source = source_by_id[fact["source_id"]]
                wrong_region = (not region_known or
                                source.get("scope_region") != applicable or
                                (fact.get("scope_region") is not None and
                                 fact["scope_region"] != applicable))
                # Both explicit scopes must admit the same exact candidate.
                wrong_model = not (_exact_model_scope(fact, fact["candidate_id"])
                                   and _exact_model_scope(source, fact["candidate_id"]))
                quote = fact["kind"] == "live_quote"
                role_invalid = quote and not price_condition
                invalid_price = False
                if price_condition:
                    try:
                        invalid_price = number(fact["value"]) < 0
                    except (ValueError, TypeError):
                        invalid_price = True
                    # Component discounts, non-price features and untyped
                    # monetary facts cannot substitute for a purchase price.
                    invalid_price |= fact["kind"] not in ("live_quote", "synthetic_probe")
                    invalid_price |= fact.get("evidence_role", "price") != "price"
                    if quote:
                        invalid_price |= (not isinstance(delivery, str) or not delivery.strip()
                                          or source.get("quote_region") != delivery
                                          or not _quote_time_valid(source, today))
                total_incomplete = (price_condition and
                                    budget_scope in
                                    ("device_delivered", "device_and_extra_consumables"))
                if wrong_region or wrong_model or role_invalid or invalid_price or total_incomplete:
                    fact["revoked"] = True
            pieces.append(publish_checked_comparison(scoped, origin="rule"))
    except (ValueError, TypeError, KeyError, OverflowError, AttributeError):
        return None

    # Merge only gate-produced claims, comparisons and controlled next actions,
    # retaining original candidate/requirement order and each claim's region.
    public = deepcopy(pieces[0])
    public["input_sha256"] = digest({
        "confirmed_requirements": requirements,
        "scoped_inputs": [part["input_sha256"] for part in pieces]})
    public["claims"] = [claim for part in pieces for claim in part["claims"]]
    public["next_actions"] = []
    seen_actions = set()
    for part in pieces:
        for action in part["next_actions"]:
            key = (action["kind"], action["candidate_id"], action["requirement_id"])
            if key not in seen_actions:
                seen_actions.add(key)
                public["next_actions"].append(action)
    public["assessments"] = []
    for candidate in candidates:
        rows = []
        for part in pieces:
            matching = next(a for a in part["assessments"]
                            if a["candidate_id"] == candidate["id"])
            rows.extend(matching["comparisons"])
        from .decision_actions import disposition
        state = disposition(rows, requirements)
        public["assessments"].append({
            "candidate_id": candidate["id"], "research_status": state,
            "comparisons": rows})
    from .decision_actions import order_actions, bind_decision
    public["next_actions"] = order_actions(public, requirements)
    bind_decision(public, requirements, bundle)
    from .decision_actions import apply_session_policy
    return apply_session_policy(public, requirements, session_values, deferred, withdrawn)


