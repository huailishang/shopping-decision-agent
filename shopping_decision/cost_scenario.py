"""Explicit, session-bound offline cost scenario; never a live quote."""
from decimal import DecimalException
from copy import deepcopy
from .evidence_comparison import digest

SCOPE="hardware_consumables_maintenance"
ASSUMPTION_LABELS={"hardware":"主机价","starter":"随箱实际可用页数","toner_yield":"替换墨粉实际页数",
                   "toner_price":"替换墨粉单价","separate_drum":"鼓粉结构","drum_yield":"替换鼓实际页数",
                   "drum_price":"替换鼓单价","drum_starter":"随箱鼓实际页数","maintenance":"维护总费用"}

def dependency_fingerprints(public, candidate):
    return {e["fact_id"]:e["evidence_sha256"] for c in public["claims"]
            if c["candidate_id"]==candidate and c["status"]=="met"
            for e in c["source_audit"] if e["admitted"] and e["fact_id"] in c["supporting_fact_ids"]}

def evaluate_scenario(public, scenario):
    if scenario is None:
        return {"status":"unknown","reason":"actual_inputs_missing"}
    if not isinstance(scenario,dict) or set(scenario) not in ({"schema_version","binding","models"},{"schema_version","binding","models","prior_assumption"}) or type(scenario["schema_version"]) is not int or scenario["schema_version"]!=1:
        return {"status":"invalid","reason":"invalid_scenario_schema"}
    try:
        scenario_sha=digest(scenario)
    except (ValueError,TypeError,OverflowError,RecursionError):
        return {"status":"invalid","reason":"noncanonical_scenario"}
    binding=public["decision_binding"]
    expected={k:binding.get(k) for k in ("category","dialogue_version","confirmed_values_sha256","session")}
    if scenario["binding"]!=expected:
        return {"status":"stale","reason":"session_changed"}
    if binding["category"]!="printer":
        return {"status":"invalid","reason":"wrong_category"}
    from .cognition_comparison import lifecycle_cost,compare_lifecycle_costs
    states={a["candidate_id"]:a["research_status"] for a in public["assessments"]}
    models=scenario["models"]
    if not isinstance(models,dict) or set(models)!=set(states) or len(models)!=2:
        return {"status":"invalid","reason":"candidate_set_mismatch"}
    prior=scenario.get("prior_assumption")
    if "prior_assumption" in scenario:
        if (not isinstance(prior,dict) or set(prior)!={"candidate","field","value"}
                or not isinstance(prior["candidate"],str) or prior["candidate"] not in models
                or not isinstance(prior["field"],str) or prior["field"] not in ASSUMPTION_LABELS):
            return {"status":"invalid","reason":"invalid_prior_assumption"}
        try:
            from .decision_worksheet import _number
            _number(prior["field"],prior["value"])
        except (ValueError,TypeError,OverflowError,DecimalException):
            return {"status":"invalid","reason":"invalid_prior_assumption"}
    results={}
    reasons={}
    for candidate,row in models.items():
        try:
            if not isinstance(row,dict) or set(row)!={"inputs","dependency_fact_ids","dependency_fingerprints","kind"} or row["kind"]!="synthetic_scenario":
                raise ValueError("unsupported_input_provenance")
            params=row["inputs"]
            if not isinstance(params,dict):
                raise ValueError("invalid_cost_inputs")
            if not all(params.get(k) is not None for k in ("months","currency","fee_scope","pages","scenario_version")):
                reasons[candidate]="missing_cost_inputs"
                results[candidate]=None
                continue
            ids=row["dependency_fact_ids"]
            if not isinstance(ids,list) or not all(isinstance(i,str) for i in ids) or len(set(ids))!=len(ids):
                raise ValueError("invalid_dependencies")
            admitted=dependency_fingerprints(public,candidate)
            fingerprints=row["dependency_fingerprints"]
            if not isinstance(fingerprints,dict) or set(fingerprints)!=set(ids):
                raise ValueError("dependency_fingerprints_required")
            if not set(ids)<=set(admitted):
                reasons[candidate]="dependency_not_admitted"
                results[candidate]=None
                continue
            if any(fingerprints[fid]!=admitted[fid] for fid in ids):
                reasons[candidate]="dependency_version_changed"
                results[candidate]=None
                continue
            # Production entry does not assume an included full-life drum.
            if params.get("separate_drum") is True and params.get("drum_starter") is None:
                reasons[candidate]="missing_cost_inputs"
                results[candidate]=None
                continue
            result=lifecycle_cost(**params)
            if result is not None:
                result["dependency_fact_ids"]=ids
                result["dependency_fingerprints"]=fingerprints
            else:
                reasons[candidate]="missing_cost_inputs"
            results[candidate]=result
        except (ValueError,TypeError,KeyError,OverflowError,DecimalException) as exc:
            reasons[candidate]=str(exc)
            results[candidate]=None
    names=sorted(results)
    status=compare_lifecycle_costs(*(results[n] for n in names))
    winner=names[0] if status=="a" else names[1] if status=="b" else None
    eligible=all(s=="eligible_for_research" for s in states.values())
    result={"status":status if eligible or status in ("unknown","incomparable") else "hard_conditions_first",
            "arithmetic_status":status,"scenario_preference":winner if eligible else None,
            "assumption_only":True,"models":results,"reasons":reasons,
            "scenario_sha256":scenario_sha}
    if prior and eligible and status in ("a","b","tie"):
        cid,field=prior["candidate"],prior["field"]
        old=prior["value"]
        current=models[cid]["inputs"].get(field)
        if old is not None and current is not None and old!=current:
            previous=deepcopy(scenario)
            previous.pop("prior_assumption")
            previous["models"][cid]["inputs"][field]=old
            before=evaluate_scenario(public,previous)
            if before.get("status") in ("a","b","tie") and before["status"]!=status:
                result["decisive_assumption"]={"candidate":cid,"field":field,"before":old,"after":current,
                    "preference_before":before["scenario_preference"],"preference_after":result["scenario_preference"],
                    "totals_before":{n:r["total"] for n,r in before["models"].items()},
                    "totals_after":{n:r["total"] for n,r in results.items()},
                    "scope":"single_explicit_assumption_points_only"}
    return result

def bind_cost(public, scenario):
    result=evaluate_scenario(public,scenario)
    public["cost_comparison"]=result
    public["decision_binding"]["cost_scenario_sha256"]=result.get("scenario_sha256")
    # A stale or malformed scenario also invalidates prior context.
    public["decision_binding"]["cost_status"]=result["status"]
    # A cost assumption can prioritize verification, never grant eligibility.
    # Do not bypass unanswered/deferred hard requirements or a clarification.
    status = result.get("status")
    actions = public["next_actions"]
    if status in ("a","b","tie") and not (actions and actions[0]["kind"]=="clarify"):
        winner = result.get("scenario_preference")
        names = sorted(result.get("models",{}))
        decisive=result.get("decisive_assumption")
        target=decisive["candidate"] if decisive else winner or (names[0] if names else None)
        eligible = all(a["research_status"]=="eligible_for_research" for a in public["assessments"])
        claim = next((c for c in public["claims"] if c["candidate_id"]==target
                      and c["dimension"]=="starter_toner_yield"),None)
        if claim is None:
            claim = next((c for c in public["claims"] if c["candidate_id"]==target and c["dimension"]=="cost"),None)
        if eligible and claim is not None and len(names)==2:
            text = ("核实"+winner+"的随箱实际可用页数和同配置耗材价，确认当前假设优势是否成立；并非购买建议。"
                    if winner else "成本情景平局：先核实两款随箱实际可用页数，检验能否改变取舍。")
            if decisive:
                text=("核实"+target+"的"+ASSUMPTION_LABELS[decisive["field"]]+"：仅改变该个人假设，两个情景点的取舍发生变化；"
                      "需要同口径证据验证，不代表整个范围稳定或真实购买建议。")
            public["next_actions"] = [{"kind":"confirm_cost_assumption","candidate_id":target,
                                       "requirement_id":claim["requirement_id"],"description":text,
                                       **({"scenario_field":decisive["field"]} if decisive else {})}]
    return result

def render_cost(result):
    if result and result.get("reasons") and any(v not in ("missing_cost_inputs","dependency_not_admitted","dependency_version_changed") for v in result["reasons"].values()):
        return "成本情景无法采用：输入或口径不合法；保留当前规则决定。"
    if not result or result["status"]=="unknown":
        return "真实总成本仍未知：需同配置主机价、随箱量、实际产量、耗材及维护费用。"
    status=result["status"]
    if status=="stale":
        return "成本情景已失效：需求已变化，须重新确认口径。"
    if status=="invalid":
        return "成本情景无法采用：输入或口径不合法。"
    if status=="incomparable":
        return "成本不可比：先统一打印量、年限、币种、费用范围和情景版本；不选冠军。"
    if status=="hard_conditions_first":
        return "成本仅为假设背景，先解决候选硬条件，不按成本选冠军。"
    totals="；".join(n+" "+r["total"]+" "+r["comparison_basis"]["currency"] for n,r in result["models"].items() if r)
    choice=result.get("scenario_preference")
    return "合成成本情景（非真实报价）："+totals+"。"+("相同口径下"+choice+"情景成本较低；" if choice else "成本平局，改变随箱量或耗材价可打破平局；")+"不代表可购买。"
