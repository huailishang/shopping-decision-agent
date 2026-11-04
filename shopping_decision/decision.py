"""H05 离线决策：使用共享证据准入，不使用未经核准的原网页卡强推荐。"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from .contracts import PurchaseRequest, Recommendation, monthly_page_bounds
from .evidence_policy import valid_https_url
from .knowledge import KnowledgeCard, load_cards, screen_cards
from .route_claims import load_route_claim_cards
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
    bounds = monthly_page_bounds(req)
    unknowns = []
    if req.budget_max_cny is not None:
        unknowns.append("预算是否覆盖实际机型、耗材与售后，尚未核实")
    if req.requires_wireless:
        unknowns.append("具体机型的普通无线/手机打印能力尚未核验")
    if any('微信' in text for text in req.requirements):
        unknowns.append("微信打印的具体方式与机型兼容性待确认；若要求从微信小程序直接打印，须另核实对应机型与绑定方法，普通Wi-Fi不代表支持微信打印")
    if req.requires_scan:
        unknowns.append("具体机型的扫描功能尚未核验")
    if price_rejected:
        unknowns.append("已拒绝未经授权平台核实的历史/声称现价报价，不能用作购买依据")
    if req.requirements:
        # 保守保留所有原文约束；命中颜色短语不表示整句话已被处理。
        unknowns.extend("尚未逐项核验自由文本约束：" + text for text in req.requirements if text.strip())

    if bounds is not None and bounds[0] != bounds[1]:
        unknowns.append(f"已记录月印量区间{bounds[0]}–{bounds[1]}页，不能用上界代替整个区间")
    if bounds is not None and bounds[0] < 150 <= bounds[1]:
        unknowns.append("该印量区间跨当前程序的条件分界，现有阈值未经专业独立批准，不得单点推断")
    if bounds is None or req.needs_color is None:
        qs = []
        if bounds is None:
            qs.append("每月大约打印多少张？可填写0–50这样的范围")
        if req.needs_color is None:
            qs.append("家里是否必须彩印？偶尔彩印可否到打印店？")
        return DecisionRecord(req, Recommendation("clarify", None,
            ("缺少关键条件，暂不推荐。",), questions=tuple(qs), unknowns=tuple(unknowns)),
            knowledge_enabled, (), (), 0, rejected_inputs=price_rejected)

    if not knowledge_enabled:
        return DecisionRecord(req, Recommendation("compare_routes", None,
            ("知识开关关闭：无已核准的品类证据，仅给出待比较的路线，不声称推荐可靠。",),
            unknowns=tuple(unknowns),
            alternative_routes=("monochrome_laser","color_inkjet","outsource_color")),
            False, (), (), 0, rejected_inputs=price_rejected)

    # 审批只限逐条主张，仍通过原有 screen_cards 资格门禁；普通路径不能信任研究索引。
    all_cards = cards if cards is not None else load_cards() + load_route_claim_cards()
    active, rejected = screen_cards(req, all_cards, today=today)
    source_pairs = tuple((c.id, c.url) for c in active)
    # 只对已有独立批准且当次适用的主张生成比较理由；不允许单条研究摘录形成唯一购买结论。
    reviewed_comparisons = tuple(c for c in active if c.use_note == "route_comparison_claim")
    route = None
    relevant: tuple[KnowledgeCard, ...] = ()
    if req.needs_color is False and bounds is not None and bounds[0] >= 150:
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
    if reviewed_comparisons:
        reasons = tuple(
            f"{c.id}（来源：{c.source_name}；发布日期：{c.published_on}；适用范围：{c.claim_scope}）："
            f"{c.claim}（局限：{c.exceptions}；反证/不能推出：{c.counter_evidence}）"
            for c in reviewed_comparisons)
        route_ids = tuple(dict.fromkeys(c.route_effect for c in reviewed_comparisons if c.route_effect))
        outcome = Recommendation("compare_routes", None,
            reasons + ("仅对获批准、在适用范围内的比较主张给出引用；尚未核验具体型号、兼容性或当前报价，不给唯一购买建议。",),
            evidence_ids=tuple(c.id for c in reviewed_comparisons),
            unknowns=tuple(unknowns),
            alternative_routes=route_ids)
    elif route and relevant:
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
        volume = f"{bounds[0]}–{bounds[1]}页" if bounds[0] != bounds[1] else f"约{bounds[0]}页"
        color_note = ("家里仅需黑白、彩印可外包" if req.needs_color is False and req.accepts_outsourced_color is True
                      else "家里需彩印、不能外包" if req.needs_color is True and req.accepts_outsourced_color is False
                      else "彩印与外包要求按确认条件比较")
        relevant_routes = ("建议比较满足黑白用途的激光与喷墨方案；彩印可外包，不强迫购买彩色机。"
                           if req.needs_color is False and req.accepts_outsourced_color is True
                           else "按用户确认的彩印/外包条件比较可行技术路线，不推定某路线必胜。")
        outcome = Recommendation("defer", None,
            (f"已记录使用条件：每月{volume}；{color_note}。",
             "本次场景没有通过适用性、时间和决策使用资格门禁的来源；只能作为研究线索，暂缓唯一推荐。",
             relevant_routes,
             "需核查长期耗材/维护、型号级兼容性、售后与相关独立比较；无获批准证据不能作当前品牌或型号结论。"),
            unknowns=tuple(unknowns), alternative_routes=("monochrome_laser", "inkjet", "external_printing"))
    else:
        outcome = Recommendation("compare_routes", None,
            ("现有证据不足以确定唯一技术路线；需补独立测试、适用范围和长期成本。",),
            evidence_ids=tuple(c.id for c in relevant),
            unknowns=tuple(unknowns),
            alternative_routes=("monochrome_laser","color_inkjet","outsource_color"))
    return DecisionRecord(req, outcome, True, source_pairs, tuple(c.id for c in active), 1,
                          rejected_evidence=rejected, rejected_inputs=price_rejected)
