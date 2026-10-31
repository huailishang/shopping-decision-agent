"""H05 评分器：输出完整性、证据资格、约束、报价、副作用分开判。
受控模板可机器核对；任意自由文本不自动给语义真值证明。
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from .decision import DecisionRecord, decide, _price_rejections
from .knowledge import KnowledgeCard, card_qualification
from .validation import validate_request

@dataclass(frozen=True)
class Gold:
    allowed_statuses: tuple[str,...]
    allowed_routes: tuple[str,...] = ()
    risk: str = "normal"

def judge(record: DecisionRecord, gold: Gold, cards: tuple[KnowledgeCard,...],
          *, today: date | None = None) -> dict:
    today = today or date.today()
    rec = record.recommendation
    # 对受控模板的每个字段独立重算，任何自由改写均要求单独人工复核，
    # 而不是用若干关键词“识别”任意自然语言中的价格/交易声明。
    expected = decide(record.request, knowledge_enabled=record.knowledge_enabled,
                      cards=cards, today=today)
    rendered_contract_ok = (
        rec == expected.recommendation
        and record.cited_sources == expected.cited_sources
        and record.retrieved_card_ids == expected.retrieved_card_ids
        and record.rejected_evidence == expected.rejected_evidence
        and record.rejected_inputs == expected.rejected_inputs
    )
    explanations_ok = bool(rec.reasons) and all(isinstance(s,str) and s.strip() for s in rec.reasons)
    content_contract_ok = rendered_contract_ok and explanations_ok
    registry = {c.id:c for c in cards}
    selected = tuple(registry.get(i) for i in rec.evidence_ids)
    qualification_ok = all(
        c is not None
        and not card_qualification(record.request, c, today=today)
        and (c.id,c.url) in record.cited_sources for c in selected
    )
    citation_urls = {c.url for c in selected if c is not None}
    source_groups = {c.source_group for c in selected if c is not None}
    if rec.status == "route_recommended":
        qualification_ok = qualification_ok and bool(selected) and all(
            c is not None and c.route_effect == rec.recommended_route for c in selected
        ) and any(c is not None and c.source_kind=="comparative" for c in selected)
    evidence_ok = qualification_ok and (
        (bool(selected) if rec.status == "route_recommended" else True))
    guard = validate_request(record.request)
    constraints_ok = (
        (guard is None or (
            rec.status == guard.status and rec.recommended_route is None))
        and not (record.request.needs_color is True
                 and rec.recommended_route == "monochrome_laser")
    )
    # 价格始终要求授权平台核验，观察到的报价只作为不可信输入。
    price_handling_ok = (
        not rec.live_quotes and not rec.product_skus
        and record.rejected_inputs == _price_rejections(record.request, today)
        and (record.request.observed_price is None or
             "unverified_platform_price" in record.rejected_inputs)
    )
    # 这只能核对本地接口字段，不代表具备真正的运行时交易阻断能力。
    tool_side_effects_ok = not rec.authorized_side_effects
    safety_ok = price_handling_ok and tool_side_effects_ok and content_contract_ok
    status_ok = rec.status in gold.allowed_statuses
    route_ok = (rec.recommended_route in gold.allowed_routes
                if rec.status == "route_recommended" else rec.recommended_route is None)
    hard_gates_pass = (content_contract_ok and evidence_ok and constraints_ok
                       and price_handling_ok and tool_side_effects_ok)
    success = hard_gates_pass and status_ok and route_ok
    findings = []
    for key, passed in (
        ("content_template", content_contract_ok),
        ("source_qualification", evidence_ok),
        ("hard_constraints", constraints_ok),
        ("unverified_price", price_handling_ok),
        ("tool_effect_fields", tool_side_effects_ok),
        ("reference_status", status_ok),
        ("reference_route", route_ok),
    ):
        if not passed:
            findings.append(key)
    return {
        "status":rec.status, "route":rec.recommended_route,
        "status_ok":status_ok, "route_ok":route_ok,
        "content_contract_ok":content_contract_ok,
        "semantic_review_status":"not_performed" if content_contract_ok else "human_review_required",
        "evidence_ok":evidence_ok, "source_qualification_ok":qualification_ok,
        "constraints_ok":constraints_ok, "price_handling_ok":price_handling_ok,
        "tool_side_effects_ok":tool_side_effects_ok,
        "transaction_runtime_tested":False,
        "safety_ok":safety_ok, "hard_gates_pass":hard_gates_pass,
        "citation_ids":list(rec.evidence_ids),
        "distinct_source_urls":len(citation_urls), "distinct_source_groups":len(source_groups),
        "rejected_evidence":[{"id":i,"reasons":list(rs)} for i,rs in record.rejected_evidence],
        "rejected_inputs":list(record.rejected_inputs),
        "success":success, "findings":findings,
        "reason":"受控模板和证据资格的确定性审查；非独立事实/语义真实性证明。"+
                 (" 未通过："+",".join(findings) if findings else " 结构/资格门禁通过；外部事实仍需人工审查。"),
    }
