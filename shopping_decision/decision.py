"""H05 离线决策：使用共享证据准入，不使用未经核准的原网页卡强推荐。"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from .contracts import PurchaseRequest, Recommendation
from .evidence_policy import valid_https_url
from .knowledge import KnowledgeCard, load_cards, screen_cards
from .validation import validate_request

@dataclass(frozen=True)
class DecisionRecord:
    request: PurchaseRequest
    recommendation: Recommendation
    knowledge_enabled: bool
    cited_sources: tuple[tuple[str, str], ...]
    retrieved_card_ids: tuple[str, ...]
    calls: int
    provenance: str = "H05 离线推理，无实时报价/实际交易功能"
    rejected_evidence: tuple[tuple[str, tuple[str, ...]], ...] = ()
    rejected_inputs: tuple[str, ...] = ()

def _price_rejections(req: PurchaseRequest, today: date) -> tuple[str, ...]:
    q = req.observed_price
    if q is None:
        return ()
    reasons = ["unverified_platform_price"]
    try:
        recorded = date.fromisoformat(q.observed_on)
        if recorded != today:
            reasons.append("stale_or_future_quote")
    except (ValueError, TypeError):
        reasons.append("invalid_quote_date")
    if not valid_https_url(q.source_url):
        reasons.append("invalid_quote_source")
    if type(q.price_minor) is not int or q.price_minor < 0 or not q.sku:
        reasons.append("invalid_quote_fields")
    if q.claims_current:
        reasons.append("unverified_current_price_claim")
    # 没有接入授权电商服务时，即使日期是今天也不能核准其现价真实性
    return tuple(reasons)

def decide(req: PurchaseRequest, *, knowledge_enabled: bool = True,
           cards: tuple[KnowledgeCard, ...] | None = None,
           today: date | None = None) -> DecisionRecord:
    today = today or date.today()
    price_rejected = _price_rejections(req, today)
    check = validate_request(req)
    if check is not None:
        return DecisionRecord(req, check, knowledge_enabled, (), (), 0,
                              rejected_inputs=price_rejected)
    if req.monthly_pages is None or req.needs_color is None:
        qs = []
        if req.monthly_pages is None:
            qs.append("每月大约打印多少张？")
        if req.needs_color is None:
            qs.append("彩色是否必要、能否外包？")
        return DecisionRecord(req, Recommendation("clarify", None,
            ("缺少关键条件，暂不推荐。",), questions=tuple(qs)),
            knowledge_enabled, (), (), 0, rejected_inputs=price_rejected)

    unknowns = []
    if req.budget_max_cny is not None:
        unknowns.append("预算是否覆盖实际机型、耗材与售后，尚未核实")
    if req.requires_wireless:
        unknowns.append("具体机型的无线/微信打印兼容性尚未核验")
    if req.requires_scan:
        unknowns.append("具体机型的扫描功能尚未核验")
    if price_rejected:
        unknowns.append("已拒绝未经授权平台核实的历史/声称现价报价，不能用作购买依据")
    if req.requirements:
        ignored = ("必须在家彩印","必须在家打印彩色","必须家用彩印","必须彩色",
                   "不需要彩色","不能彩印","只打黑白","给我直接下单","自动下单")
        unknowns.extend("尚未核验自由文本约束：" + s for s in req.requirements
                        if s.strip() and not any(t in s for t in ignored))

    if not knowledge_enabled:
        return DecisionRecord(req, Recommendation("compare_routes", None,
            ("知识开关关闭：无已核准的品类证据，仅给出待比较的路线，不声称推荐可靠。",),
            unknowns=tuple(unknowns),
            alternative_routes=("monochrome_laser","color_inkjet","outsource_color")),
            False, (), (), 0, rejected_inputs=price_rejected)

    active, rejected = screen_cards(req, cards if cards is not None else load_cards(), today=today)
    source_pairs = tuple((c.id, c.url) for c in active)
    route = None
    relevant: tuple[KnowledgeCard, ...] = ()
    if req.needs_color is False and req.monthly_pages >= 150:
        relevant = tuple(c for c in active if c.id in ("CN-001","CN-003"))
        if any(c.id == "CN-001" for c in relevant):
            route = "monochrome_laser"
    elif req.needs_color is True and req.accepts_outsourced_color is False:
        relevant = tuple(c for c in active if c.id == "CN-002")
        if relevant:
            route = "color_inkjet"
    elif req.needs_color is False and req.idle_weeks is not None and req.idle_weeks >= 3:
        relevant = tuple(c for c in active if c.id in ("CN-008","CN-009"))
        if len(relevant) >= 2:
            route = "monochrome_laser"

    # 两篇同一厂商的FAQ不能成为独立横评；route_effect 是复核后的推论而非原文事实。
    if route and not any(c.source_kind == "comparative" for c in relevant):
        route = None
    if route and relevant:
        reasons = tuple(c.claim + "（局限：" + c.exceptions + "）" for c in relevant)
        cite = tuple(c.id for c in relevant)
        if unknowns:
            outcome = Recommendation("compare_routes", None,
                reasons + ("技术路线可比较，但尚有未核实的购买约束，不锁定机型。",),
                evidence_ids=cite, unknowns=tuple(unknowns), alternative_routes=(route,))
        else:
            outcome = Recommendation("route_recommended", route,
                reasons + ("仅路线级历史比较；不代表现售型号、价格或官方推荐某品牌。",),
                evidence_ids=cite, alternative_routes=("compare_routes",))
    elif not active:
        outcome = Recommendation("defer", None,
            ("本次场景没有通过时间、适用范围和使用资格门禁的独立来源；保留为研究线索，暂缓唯一推荐。",),
            unknowns=tuple(unknowns))
    else:
        outcome = Recommendation("compare_routes", None,
            ("现有证据不足以确定唯一技术路线；需补独立测试、适用范围和长期成本。",),
            evidence_ids=tuple(c.id for c in relevant),
            unknowns=tuple(unknowns),
            alternative_routes=("monochrome_laser","color_inkjet","outsource_color"))
    return DecisionRecord(req, outcome, True, source_pairs, tuple(c.id for c in active), 1,
                          rejected_evidence=rejected, rejected_inputs=price_rejected)
