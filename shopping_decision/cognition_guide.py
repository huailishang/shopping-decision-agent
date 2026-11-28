"""Read-only printer guide; evidence examples do not certify products or demands."""
from datetime import date
from pathlib import Path
import json
import hashlib

from .evidence_comparison import digest

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
REVIEW = "handoffs/evaluator_executor/PRINTER-CANDIDATE-TRADEOFF-20261125/evidence/evaluator/source-review.md"

REVIEW_SHA256 = "a31f590fc0cc3b0278265e4745aed88990a101c8b7474a0d284369e1fad04736"
# Exact prior reviewed source/fact bytes, not arbitrary self-declared review status.
REVIEWED_EXAMPLES = {
    "guide-functions": "7b065ace8140bea52e23dc88e003454daf8603c5210d3426e48f4dfbc402d48e",
    "guide-consumables": "119df2453df70c6d0282bea3067b68a6b657a83ca409f21055d04b41ab28a9ba",
    "guide-yield": "965a7e259ea020484c42a0006eb69cd62e863636f8d90fde6af4884853f42b6c",
}

# Narrow examples independently reviewed in the predecessor. The review is
# evidence of these examples only, not permission to approve other claims.
EXAMPLES = (
    ("guide-functions", "有的打印机兼有扫描和自动双面；选购时应分别核实功能，不能只看打印机名称。",
     "hp-cn-home", ("hp-scan", "hp-auto-duplex"),
     "以 M232dw 官方规格为例", "不能推断其他型号、微信复用或实际体验"),
    ("guide-consumables", "部分激光打印机鼓粉分离；长期费用不能只看墨粉价格，还要核对硒鼓等耗材。",
     "brother-cn-202405-brochure", ("brother-separate-drum",),
     "以 HL-L1238W 系列规格册为例", "不推断所有激光机的结构或实际维护费用"),
    ("guide-yield", "标称耗材页数有测试条件，不等于家里一定能打这么多页。",
     "brother-cn-202405-brochure", ("brother-tn118-yield", "brother-dr118-yield"),
     "限规格册所述 ISO 测试及单页作业口径", "随箱量、家庭实测产量和维护费未知"),
)

def build_guide(values, *, as_of=None):
    if values.get("category") != "printer":
        return None
    as_of = as_of or date.today()
    try:
        data = json.loads((KNOWLEDGE / "printer_cognition_comparison_v1.json").read_text(encoding="utf8"))
        if not isinstance(data,dict) or not all(isinstance(data.get(k),list) for k in ("sources","facts")):
            raise ValueError("invalid guide source")
        if any(not isinstance(r,dict) or not isinstance(r.get("id"),str) for k in ("sources","facts") for r in data[k]):
            raise ValueError("invalid guide source rows")
        if any(len({r["id"] for r in data[k]})!=len(data[k]) for k in ("sources","facts")):
            raise ValueError("duplicate guide source rows")
    except (OSError,ValueError,TypeError):
        data={"sources":[],"facts":[]}
    registry = {s["id"]: s for s in data["sources"]}
    facts = {f["id"]: f for f in data["facts"]}
    sources, claims = [], []
    from .guide_binding import source_lifecycle
    lifecycle=source_lifecycle()
    try:
        review_exists = hashlib.sha256((ROOT / REVIEW).read_bytes()).hexdigest()==REVIEW_SHA256
    except OSError:
        review_exists=False
    for cid,text,sid,fids,condition,exception in EXAMPLES:
        src = registry.get(sid)
        life=lifecycle[sid]
        available = bool(life["status"]=="active" and src and not src.get("revoked") and isinstance(src.get("valid_until"),str) and src["valid_until"] >= as_of.isoformat()
                         and review_exists and all(f in facts and facts[f].get("source_id")==sid for f in fids)
                         and digest({"source":src,"facts":[facts[f] for f in fids]})==REVIEWED_EXAMPLES[cid])
        if src and not any(s["id"]==sid for s in sources):
            sources.append({"id":sid,"type":src.get("type","unknown"),"url":src.get("url",""),
                "source_group":sid.split("-")[0],"captured_on":src.get("captured_on"),
                "published_on":"2024-05" if sid.startswith("brother") else None,
                "review_status":"prior_narrow_review" if available else "pending",
                "limitations":src.get("limitations","待核"),"locator":src.get("locator","待核"),
                "review_ref":REVIEW,"valid_until":src.get("valid_until"),"lifecycle":life})
        claims.append({"id":cid,"text":text,"source_ids":[sid] if src else [],
            "conditions":[condition],"exceptions":[exception],"counter_evidence":[exception],
            "evidence_status":"supported" if available else "pending", "lifecycle":life,
            "fact_ids":list(fids),"review_ref":REVIEW})
    # Public methodology read by the executor: a method, not domestic model evidence.
    method_ref="handoffs/evaluator_executor/PRINTER-COGNITION-FIRST-20261126/evidence/executor/PUB-READ-002.json"
    try:
        method_ok=hashlib.sha256((ROOT / method_ref).read_bytes()).hexdigest()=="e1b9392c04faf1438f1ce64af96b74b43fcd910e88c6b67e48717a4da95fea93"
    except OSError:
        method_ok=False
    method_life=lifecycle["rtings-cost-method-2021"]
    method_ok=method_ok and method_life["status"]=="active"
    sources.append(dict(id="rtings-cost-method-2021",type="independent_comparison_method",
                        url="https://www.rtings.com/printer/tests/printing/cost-per-print",
                        source_group="rtings",captured_on="2026-11-27",published_on="2021-09-21",
                        review_status="executor_read_pending_independent_review" if method_ok else "pending", lifecycle=method_life,
                        locator="Our Tests; Costs Not Related To Printing; What's Missing?",
                        limitations="2021年方法、美国为主样品、有联盟收入；不证明国内型号实价、长期可靠性或维护金额；不宣称为最新方法。",
                        review_ref=method_ref))
    claims.append(dict(id="guide-cost-method",text="单页耗材成本与长期总费用不同；比较时应另问维护费、随箱量和实际使用条件。",
                       source_ids=["rtings-cost-method-2021"],
                       conditions=["同测试口径的估算产量与耗材价格仅作方法参考"],
                       exceptions=["清洁耗墨、鼓组件、长期可靠性未纳入该测试成本"],
                       counter_evidence=["评测时价格与家庭真实产量可能不同；少量打印时单页成本未必是首要因素"],
                       evidence_status="supported" if method_ok else "pending",review_ref=method_ref,lifecycle=method_life))
    by_id={c["id"]:c for c in claims}
    def dimension(id,label,why,field,claim=None):
        c=by_id.get(claim,{})
        return dict(id=id,label=label,why_it_matters=why,question_field=field,
                    source_ids=c.get("source_ids",[]),claim_ids=[claim] if claim in by_id else [],evidence_status=c.get("evidence_status","pending"))
    dimensions=[
        dimension("color","彩色还是黑白","先想是否必须在家打印彩色；偶尔彩印能否外包也要本人决定。","needs_color"),
        dimension("function","扫描与双面","需要扫描纸质资料吗？希望机器自动翻面吗？两项分别核型号。","requires_scan","guide-functions"),
        dimension("usage","使用场景","估计月印量和使用间隔，不知道可暂缓；闲置影响尚缺专业比较证据。","monthly_pages_range"),
        dimension("idle","连续多周闲置","本人确认是否经常连续多周不用；实际维护与恢复条件需要资料验证，不凭印量推断。","idle_weeks_pattern","guide-cost-method" if method_ok else None),
        dimension("cost","长期耗材成本","除主机外，核对耗材种类、标称测试条件、随箱量和更换价格；不要先填虚构维护费。","budget_max_cny","guide-cost-method" if method_ok else "guide-consumables"),
    ]
    for dim in dimensions:
        dim["user_decides"] = dim["question_field"]
        dim["product_evidence"] = "具体型号适用事实须单独核验"
        dim["personal_assumption"] = "只在本人明确提供情景时采用，不代填实际数值"
    color=values.get("needs_color")
    routes=[
        dict(id="mono_laser",label="黑白激光",status="not_fit" if color is True else "consider",
             evidence_ids=[],conditions=["必须在家彩印时不适用"],limitations=["尚未核实各路线长期维护差异"]),
        dict(id="color_inkjet",label="喷墨或其他彩色路线",status="research_required" if color is True else "unknown",
             evidence_ids=[],conditions=["本人确认彩色需求后再查路线"],limitations=["未核专业比较资料，不排名"]),
        dict(id="outsourcing",label="外部打印或暂缓购买",status="consider" if values.get("accepts_outsourced_color") is True else "unknown",
             evidence_ids=[],conditions=["本人愿意外部打印时比较便利性与费用"],limitations=["未核当地费用与可达性"]),
    ]
    unknowns=["路线间独立专业试验尚待核源","真实维护费用、闲置后表现和家庭实际耗材量未核","具体型号、销售配置、价格及库存需单独验证"]
    for sid,life in lifecycle.items():
        if life["status"]!="active":unknowns.append("认知来源 "+sid+" 已撤回、待核或不可用；不再采用其旧主张。")
    guide=dict(schema_version=1,guide_id="printer-cognition-guide",category="printer",
               status="partial",decision_use="guidance_only",sources=sources,claims=claims,
               dimensions=dimensions,routes=routes,unknowns=unknowns)
    guide["version"]=digest({"sources":sources,"claims":claims,"dimensions":dimensions,"lifecycle":lifecycle})
    return guide

def usage_research(values, guide, *, deferred=(), withdrawn=()):
    field="idle_weeks_pattern"
    val=values.get(field)
    state="confirmed" if val is not None else "withdrawn" if field in withdrawn else "deferred" if field in deferred else "unanswered"
    source_ids=next(d["source_ids"] for d in guide["dimensions"] if d["id"]=="idle" and d["evidence_status"]=="supported") if any(d["id"]=="idle" and d["evidence_status"]=="supported" for d in guide["dimensions"]) else []
    if val=="often_long":
        question="核各适用路线在连续多周不用后的恢复步骤、清洁耗材和维护条件；需型号说明及有条件的独立测试，缺证不淘汰。"
    elif val=="usually_short":
        question="核各适用路线在通常每周使用时的耗材更换和清洁维护口径；仍不推断实际费用或可靠性。"
    else:
        question="使用间隔未确认；保留闲置与维护条件为未知，不预设使用频率。"
    return dict(field=field,answer=val,answer_state=state,status="research_required" if val is not None else "unknown",
                question=question,source_ids=source_ids,hard_requirement=False,
                limitation="资料仅支持维护与单页成本分开；没有可据此选择路线的闲置阈值。" if source_ids else "当前认知依据待核；仅按用户明确场景发起研究，不发布技术结论。")

def project(values, report=None, *, as_of=None, deferred=(), withdrawn=(), state_version=None):
    guide=build_guide(values,as_of=as_of)
    if guide is None:
        return {}
    report=report or {}
    cognition=report.get("cognition_comparison") or {}
    public=cognition.get("public") or report.get("public_decision") or {}
    candidate_facts=[{k:c[k] for k in ("candidate_id","dimension","status","supporting_fact_ids") if k in c}
                     for c in public.get("claims",[])]
    usage=usage_research(values,guide,deferred=deferred,withdrawn=withdrawn)
    context=dict(schema_version=1,guide_id=guide["guide_id"],guide_version=guide["version"],
                 user_confirmed=dict(values),cognition_claims=guide["claims"],
                 route_basis=guide["routes"],candidate_facts=candidate_facts,unknowns=guide["unknowns"],sources=guide["sources"],usage_research=usage,personal_assumptions=public.get("cost_comparison",{}))
    if public and type(state_version) is int:
        from .focus_guidance import public_focus
        focus=public_focus(values,state_version,guide,public)
        if focus is not None:
            context["guidance_focus"]=focus
    lines=["选购前先看（部分资料已核，路线比较仍待补证）" if any(c["evidence_status"]=="supported" for c in guide["claims"]) else "选购前先看（认知依据待核，暂不发布专业判断）",
           "先想家里实际需要做什么，不必先懂专业参数或填写维护费用。"]
    lines.extend(d["label"]+"："+d["why_it_matters"] for d in guide["dimensions"])
    route_labels={"not_fit":"不适用","consider":"可考虑（非购买建议）","research_required":"需要研究","unknown":"待确认"}
    lines.extend(r["label"]+"："+route_labels[r["status"]]+"；"+ "；".join(r["conditions"]+r["limitations"]) for r in guide["routes"])
    for c in guide["claims"]:
        if c["evidence_status"]=="supported":
            lines.append(c["text"]+"（"+"；".join(c["conditions"]+c["exceptions"]+c["counter_evidence"])+"）")
        else:
            lines.append("主张待核："+c["id"]+"；不采用旧结论。")
    for src in guide["sources"]:
        lines.append("来源："+src["id"]+"；发布："+str(src.get("published_on") or "未知")+"；获取："+str(src["captured_on"])+"；状态："+str(src.get("review_status"))+"；定位："+str(src.get("locator"))+"；"+src["url"]+"；"+str(src["limitations"]))
    lines.append("使用间隔：经常连续多周不用 / 通常每周都会用 / 暂不确定；在“目前理解/修改”中发送才确认。")
    lines.append(usage["question"])
    lines.extend("待核："+u for u in guide["unknowns"])
    lines.append("查看不会确认需求；参考答案需本人明确发送。")
    return {"guide_text":"\n".join(lines),"cognition_guide_json":json.dumps(guide,ensure_ascii=False),
            "cognition_context_json":json.dumps(context,ensure_ascii=False)}
