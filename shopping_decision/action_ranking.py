"""Explicit offline suggestion injection; rule decisions survive every failure."""
from copy import deepcopy
import json
import time
from .context_builder import build_context
from .decision_actions import action_id
from .evidence_comparison import digest
from .model_adapter import normalize, ModelRoute

def accept_ranking(public, plan, answer, *, cognition_context=None):
    if plan.get("mode")!="model_rank_actions":
        raise ValueError("model_not_needed")
    required=plan["packet"]["required"]
    if required.get("cognition_context") != cognition_context:
        raise ValueError("stale_cognition_context")
    if public["input_sha256"]!=required["input_sha256"] or digest(
            {"binding":public["decision_binding"],"claims":public["claims"],
             "actions":public["next_actions"],"assessments":public["assessments"]})!=required["decision_sha256"]:
        raise ValueError("stale_context")
    if not isinstance(answer,dict) or set(answer)!={"context_id","action_ids"}:
        raise ValueError("unexpected_model_fields")
    if answer["context_id"]!=required["context_id"]:
        raise ValueError("context_binding_mismatch")
    ids=answer["action_ids"]
    if not isinstance(ids,list) or not 1<=len(ids)<=3 or not all(
            isinstance(i,str) and len(i)==64 for i in ids):
        raise ValueError("invalid_action_ids")
    if len(set(ids))!=len(ids) or not set(ids)<=set(plan["action_ids"]):
        raise ValueError("unknown_or_duplicate_action")
    originals={action_id(public,a):a for a in public["next_actions"]}
    if not set(ids)<=originals.keys():
        raise ValueError("stale_action")
    # Only the first equally prior group may be reordered. Preserve all other actions.
    return [deepcopy(originals[i]) for i in ids]+[deepcopy(a) for a in public["next_actions"]
                                                  if action_id(public,a) not in ids]

def rank_actions(public, route=None, transport=None, *, cognition_context=None, **budget):
    """No implicit transport, network, credentials, retries or purchase authorization."""
    ordered=deepcopy(public["next_actions"])
    audit={"mode":"rules_only","business_accepted":False,"external_api_calls":0,
           "rule_actions":deepcopy(ordered)}
    if route is None or transport is None:
        return ordered,audit
    if not isinstance(route,ModelRoute) or not route.fixture:
        audit.update(reason="unverified_or_nonfixture_route")
        return ordered,audit
    try:
        plan=build_context(public,route,cognition_context=cognition_context,**budget)
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        audit.update(reason=str(exc))
        return ordered,audit
    audit["plan"]=plan
    if plan["mode"]!="model_rank_actions":
        audit.update(reason=plan["reason"])
        return ordered,audit
    ctx=plan["packet"]["required"]["context_id"]
    request_id=digest({"context":ctx,"route":route.model,"protocol":route.protocol})
    start=time.monotonic()
    try:
        result=transport(deepcopy(plan["payload"]))
        if not isinstance(result,dict):
            raise ValueError("invalid_fixture_transport")
        receipt=normalize(route,http_status=result.get("http_status"),raw=result.get("raw"),
                          transport_error=result.get("transport_error"),request_id=request_id,
                          context_id=ctx,elapsed_ms=round((time.monotonic()-start)*1000))
    except (TimeoutError,OSError,ValueError,TypeError,KeyError) as exc:
        audit.update(reason="fixture_transport_error:"+type(exc).__name__)
        return ordered,audit
    audit["receipt"]=receipt
    if receipt["status"]!="complete" or receipt["identity"]!="matched":
        audit.update(reason=receipt["status"])
        return ordered,audit
    try:
        if len(receipt["text"])>4096:
            raise ValueError("model_text_over_limit")
        answer=json.loads(receipt["text"])
        ranked=accept_ranking(public,plan,answer,cognition_context=cognition_context)
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        audit.update(reason="business_rejected:"+str(exc))
        return ordered,audit
    audit.update(mode="fixture_ranked",business_accepted=True,
                 changed=ranked!=ordered,accepted_action_ids=answer["action_ids"])
    audit["receipt"]["business_accepted"]=True
    return ranked,audit
