"""One action ordering over admitted public claims, never raw facts."""
from .evidence_comparison import digest

# Feature gating before usage/price; unknown hard conditions always precede soft.
PRIORITY = {name: i for i, name in enumerate((
    "color_print", "scan", "auto_duplex", "initial_setup_without_app_or_scan",
    "wechat_transfer_to_app", "wechat_miniprogram", "wechat_reuse", "cost",
    "starter_toner_yield","replacement_toner_yield","drum_yield",
    "replace_on_unacceptable_quality","separate_drum","starter_included","replacement_137a_x"))}

def order_actions(public, requirements, actions=None):
    reqs = {r["id"]: r for r in requirements}
    claims = {(c["candidate_id"], c["requirement_id"]): c for c in public["claims"]}
    survivors = {a["candidate_id"] for a in public["assessments"]
                 if a["research_status"] != "excluded_for_research"}
    items = []
    for action in public["next_actions"] if actions is None else actions:
        cid, rid = action["candidate_id"], action["requirement_id"]
        if cid not in survivors or rid not in reqs or (cid, rid) not in claims:
            continue
        r, c = reqs[rid], claims[(cid, rid)]
        if r.get("research_relevant") is False and r["importance"] != "hard":
            continue
        hard_open = r["importance"] == "hard" and c["status"] in ("unknown","conflict")
        priority = (0 if hard_open else 1 if r["importance"] == "hard" else 2,
                    PRIORITY.get(r["dimension"], 100), r["dimension"], cid, rid)
        items.append((priority, dict(action)))
    return [action for _, action in sorted(items, key=lambda pair: pair[0])]

def disposition(rows, requirements):
    hard = {r["id"] for r in requirements if r["importance"] == "hard"}
    states = [r["status"] for r in rows if r["requirement_id"] in hard]
    return ("excluded_for_research" if "failed" in states else
            "pending_evidence" if any(s in ("unknown","conflict") for s in states)
            else "eligible_for_research")

def action_id(public, action):
    return digest({"input": public["input_sha256"], "action": action})

def bind_decision(public, requirements, bundle):
    """Preserve the effective user contract, not the provider's proposed requirements."""
    public["decision_binding"] = {
        "request_id": bundle["request_id"],
        "category": bundle.get("category"),
        "dialogue_version": bundle.get("dialogue_version"),
        "confirmed_values_sha256": bundle.get("confirmed_values_sha256"),
        "requirements": [{**{k: r[k] for k in ("id","dimension","unit","op","value","importance")},
                          "research_relevant": r.get("research_relevant", True)}
                         for r in requirements],
        "authorization": {"purchase": False, "transactions": False, "live_price_verified": False},
    }
    return public



def apply_session_policy(public, requirements, values, deferred=(), withdrawn=()):
    """One user-owned clarification policy; facts cannot answer for the user."""
    if values is None or values.get("category")!="printer":
        return public
    fields=set(values)|set(deferred)|set(withdrawn)|{"requires_scan","requires_auto_duplex","wechat_required","wechat_workflow","accepts_initial_setup","needs_color","budget_max_cny","budget_scope","delivery_region","device_deployment_region","monthly_pages_range","usage"}
    states={k:("confirmed" if k in values else "withdrawn" if k in withdrawn else "deferred" if k in deferred else "unanswered") for k in sorted(fields)}
    public["decision_binding"]["session"]={"fields":states,"deferred":sorted(set(deferred)),"withdrawn":sorted(set(withdrawn))}
    public["input_sha256"]=digest({"admitted":public["input_sha256"],"session":public["decision_binding"]["session"]})
    survivors=sorted(a["candidate_id"] for a in public["assessments"] if a["research_status"]!="excluded_for_research")
    if len(survivors)<2:
        return public
    reqs={r["id"]:r for r in requirements}
    actions=public["next_actions"]
    if actions and reqs[actions[0]["requirement_id"]]["dimension"] not in ("wechat_miniprogram","wechat_reuse","cost"):
        return public
    for field,dim,label in (("requires_scan","scan","扫描"),("requires_auto_duplex","auto_duplex","自动双面")):
        rid=next((r["id"] for r in requirements if r["dimension"]==dim),None)
        if states[field]!="unanswered" or rid is None:
            continue
        if not any(c["requirement_id"]==rid and c["candidate_id"] in survivors and c["status"]=="met" for c in public["claims"]):
            continue
        clarification={"kind":"clarify","candidate_id":survivors[0],"requirement_id":rid,
                       "description":"确认是否必须"+label+"；若必须则按有据能力筛选，若无需则不为该功能额外付费。"}
        public["next_actions"]=[clarification]+[a for a in actions if (a["candidate_id"],a["requirement_id"])!=(survivors[0],rid)]
        break
    return public
