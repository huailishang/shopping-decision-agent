"""可审查知识卡：H05 强制证据资格门禁；仍不作外部网页真实性或版权法律鉴定。"""
from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from .evidence_policy import metadata_gate

CARDS_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "printer_cards.json"

@dataclass(frozen=True)
class KnowledgeCard:
    id: str
    topic: str
    source_kind: str
    source_name: str
    url: str
    published_on: str
    captured_on: str
    applies_when: str
    route_effect: str | None
    claim: str
    exceptions: str
    counter_evidence: str
    promotion: bool
    reuse_basis: str
    scope: str
    category: str = "printer"
    region: str = "CN"
    review_status: str = "pending"
    permitted_uses: tuple[str, ...] = ()
    reviewed_on: str | None = None
    recheck_on: str | None = None
    route_inference_review: str = "pending"
    source_group: str = ""
    claim_scope: str = ""
    sample_scope: str = ""
    use_note: str = ""
    scope_level: str = ""
    model_ids: tuple[str, ...] = ()
    fact_audit_status: str = "pending"
    fact_audit_on: str = ""
    fact_audit_anchor: str = ""
    fact_audit_role: str = ""
    fact_audit_limit: str = ""
    decision_support_approval: str = "not_granted"
    approval_authority: str = ""
    approval_evidence_ref: str = ""

def load_cards(path: Path = CARDS_PATH) -> tuple[KnowledgeCard, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    result = tuple(KnowledgeCard(**{**c, "permitted_uses": tuple(c.get("permitted_uses", ())),
                                    "model_ids": tuple(c.get("model_ids", ()))}) for c in raw["cards"])
    ids = [c.id for c in result]
    if len(ids) != len(set(ids)):
        raise ValueError("知识卡 ID 重复")
    for c in result:
        if not c.claim or not c.exceptions or not c.counter_evidence or not c.scope:
            raise ValueError(f"卡片结构缺失: {c.id}")
        if c.source_kind == "regulator" and c.route_effect:
            raise ValueError("监管抽检不能背书购买路线")
    return result

def card_applies(request, card: KnowledgeCard) -> bool:
    c = card.applies_when
    if c == "any":
        return True
    if c == "idle":
        return request.idle_weeks is not None and request.idle_weeks >= 3
    if c == "wireless":
        return bool(request.requires_wireless)
    if c == "high":
        return request.monthly_pages is not None and request.monthly_pages >= 150
    if c == "high_bw":
        return request.monthly_pages is not None and request.monthly_pages >= 150 and request.needs_color is False
    if c == "home_color":
        return request.needs_color is True and request.accepts_outsourced_color is False
    return False

def card_qualification(request, card: KnowledgeCard, *, today: date | None = None) -> tuple[str, ...]:
    if not card_applies(request, card):
        return ("not_applicable",)
    issues = list(metadata_gate(url=card.url, region=card.region,
        target_region=getattr(request, "market_region", "CN"),
        captured_on=card.captured_on, published_on=card.published_on,
        reviewed_on=card.reviewed_on, recheck_on=card.recheck_on,
        review_status=card.review_status, allowed_uses=tuple(card.permitted_uses),
        purpose="decision_support", today=today or date.today(), source_group=card.source_group))
    if card.category != request.category:
        issues.append("category_mismatch")
    if card.fact_audit_status not in ("supported_limited", "supported_after_rewrite"):
        issues.append("fact_not_checked")
    if (card.decision_support_approval != "approved"
        or card.approval_authority != "independent_evaluator"
        or not card.approval_evidence_ref):
        issues.append("missing_independent_decision_approval")
    if not card.claim_scope or not card.sample_scope or card.scope_level not in (
        "historical_comparison", "model_specific", "regulatory_batches", "category_principle"):
        issues.append("unknown_source_scope")
    if card.scope_level == "model_specific" and (
        not getattr(request, "model_id", None)
        or request.model_id not in card.model_ids):
        issues.append("model_scope_mismatch")
    if card.promotion:
        issues.append("promotion")
    if card.source_kind == "regulator":
        issues.append("regulatory_not_route_support")
    if card.route_effect is not None and card.route_inference_review != "reviewed":
        issues.append("route_inference_unreviewed")
    return tuple(dict.fromkeys(issues))

def screen_cards(request, cards: tuple[KnowledgeCard, ...], *,
                 today: date | None = None) -> tuple[tuple[KnowledgeCard, ...], tuple[tuple[str, tuple[str, ...]], ...]]:
    accepted, rejected = [], []
    for c in cards:
        if not card_applies(request, c):
            continue
        reasons = card_qualification(request, c, today=today)
        if reasons:
            rejected.append((c.id, reasons))
        else:
            accepted.append(c)
    return tuple(accepted), tuple(rejected)

def matching_cards(request, cards: tuple[KnowledgeCard, ...], *,
                   today: date | None = None) -> tuple[KnowledgeCard, ...]:
    return screen_cards(request, cards, today=today)[0]
