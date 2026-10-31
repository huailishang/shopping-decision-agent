"""按需品类证据规划器：只决定查什么/哪些资料可复用，不进行联网、不生成购买推荐。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal
from .evidence_policy import metadata_gate

Stage = Literal["route", "product", "checkout"]
EvidenceState = Literal["reviewed", "unverified", "disputed"]

# 这里只保留所有品类共用的研究问题，不包含打印机/空调专用选择规则。
ROUTE_TOPICS = ("category_map", "decision_factors", "exceptions")
PRODUCT_TOPICS = ("model_specs", "independent_comparison")
DYNAMIC_TOPICS = ("live_price", "availability", "seller_terms")

SOURCE_ROUTES = {
    "category_map": ("standard_register", "manufacturer_document", "technical_reference"),
    "decision_factors": ("consumer_comparison", "independent_laboratory", "standard_register"),
    "exceptions": ("consumer_comparison", "manufacturer_document", "repair_and_user_feedback"),
    "model_specs": ("manufacturer_document", "authorized_catalogue"),
    "independent_comparison": ("consumer_comparison", "independent_laboratory"),
    "live_price": ("authorized_catalogue",),
    "availability": ("authorized_catalogue",),
    "seller_terms": ("authorized_catalogue", "seller_official_policy"),
}

@dataclass(frozen=True)
class EvidenceIndexEntry:
    """已经人工核查过的证据索引；状态自报不代表系统独立完成了事实验证。"""
    evidence_id: str
    category: str
    topic: str
    source_url: str
    source_group: str
    region: str
    reviewed_on: str
    recheck_on: str
    state: EvidenceState = "reviewed"
    permitted_uses: tuple[str, ...] = ("research_index",)

@dataclass(frozen=True)
class ResearchPlan:
    category: str
    stage: Stage
    status: Literal["clarify", "reuse", "research", "review_required", "live_verification"]
    reusable_ids: tuple[str, ...]
    missing_topics: tuple[str, ...]
    recheck_ids: tuple[str, ...]
    live_check_topics: tuple[str, ...]
    source_routes: tuple[tuple[str, tuple[str, ...]], ...]
    limitations: tuple[str, ...]

def plan_research(category: str, *, stage: Stage = "route",
                  index: tuple[EvidenceIndexEntry, ...] = (),
                  region: str = "CN", today: date | None = None) -> ResearchPlan:
    """同一个规划器适用于任意品类；不依赖预建的品类专用知识库。"""
    if stage not in ("route", "product", "checkout"):
        raise ValueError("stage must be route/product/checkout")
    if not region.strip():
        raise ValueError("region must not be empty")
    name = category.strip()
    if not name:
        return ResearchPlan("", stage, "clarify", (), (), (), (), (), ("尚不知道购买品类，需要先澄清。",))
    today = today or date.today()
    required = ROUTE_TOPICS + (PRODUCT_TOPICS if stage in ("product", "checkout") else ())
    reusable: list[str] = []
    missing: list[str] = []
    recheck: list[str] = []
    limitations: list[str] = []

    for topic in required:
        applicable: list[EvidenceIndexEntry] = []
        candidates = [e for e in index if e.category == name and e.topic == topic]
        for e in candidates:
            reasons = metadata_gate(
                url=e.source_url, region=e.region, target_region=region,
                captured_on=e.reviewed_on, published_on=None, reviewed_on=e.reviewed_on,
                recheck_on=e.recheck_on, review_status=e.state,
                allowed_uses=tuple(e.permitted_uses), purpose="research_index",
                today=today, source_group=e.source_group)
            if reasons:
                recheck.append(e.evidence_id)
                continue
            applicable.append(e)
        if applicable:
            reusable.extend(e.evidence_id for e in applicable)
        else:
            missing.append(topic)
    # 结算前的动态信息永远要求再次实时核验，不能用本地知识卡代替报价和库存。
    live_check = DYNAMIC_TOPICS if stage == "checkout" else ()
    source_routes = tuple((t, SOURCE_ROUTES[t]) for t in missing + list(live_check))
    if live_check:
        status = "live_verification"
    elif missing:
        status = "review_required" if recheck else "research"
    else:
        status = "reuse"
    if recheck:
        limitations.append("部分历史资料超出复核日、来源无效、存在争议或地域不匹配；不能直接当成当前证据。")
    if missing:
        limitations.append("缺少可复用的已核查证据：只给研究方向，不给品牌/技术路线结论。")
    if live_check:
        limitations.append("实时价格、库存和商家条件必须由授权的当前来源核验；本规划器不会下单。")
    limitations.append("已标记reviewed只是输入元数据，必须由独立证据审查流程保证其真实性、范围及授权。")
    return ResearchPlan(name, stage, status, tuple(dict.fromkeys(reusable)), tuple(missing),
                        tuple(dict.fromkeys(recheck)), tuple(live_check),
                        source_routes, tuple(limitations))
