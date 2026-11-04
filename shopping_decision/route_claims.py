"""H08 B 最小来源账本桥接：只把逐条可审核主张投影到已有 KnowledgeCard 门禁。
注意：本模块不审核来源真实性、许可证，也不会自行授予任何批准。
"""
from __future__ import annotations
import json
from pathlib import Path
from .knowledge import KnowledgeCard, load_cards

ROUTE_LEDGER_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "h08_b_evidence_review.json"
_ALLOWED_APPLIES = frozenset(("any", "idle", "high", "high_bw", "home_color", "wireless"))
_ALLOWED_ROUTES = frozenset(("monochrome_laser", "inkjet", "external_printing"))
_ALLOWED_SCOPE = frozenset(("category_principle", "historical_comparison", "model_specific"))


def load_route_claim_cards(path: Path | None = None) -> tuple[KnowledgeCard, ...]:
    """一次来源审查是多条主张的容器；批准只能逐 claim_id、用途和限定范围生效。

    缺字段的主张宁可跳过，不使用来源级的 independent_approval 替代单条批准。
    """
    target = path if path is not None else ROUTE_LEDGER_PATH
    if not target.is_file():
        return ()
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("evidence"), list):
        raise ValueError("来源账本格式错误")
    result = []
    seen = {card.id for card in load_cards()}  # 新主张不得与历史13卡冲突或覆盖其证据引用。
    for src in data["evidence"]:
        if not isinstance(src, dict):
            continue
        claims = src.get("decision_claims", [])
        if not isinstance(claims, list):
            raise ValueError("来源账本 decision_claims 必须是数组")
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            cid = claim.get("id")
            applies = claim.get("applies_when")
            scope_level = claim.get("scope_level")
            route = claim.get("route_effect")
            if (not isinstance(cid, str) or not cid
                or applies not in _ALLOWED_APPLIES
                or scope_level not in _ALLOWED_SCOPE
                or route not in (None, *_ALLOWED_ROUTES)
                or not all(isinstance(claim.get(k), str) and claim[k].strip()
                           for k in ("claim", "exceptions", "counter_evidence", "claim_scope", "sample_scope"))):
                continue
            if cid in seen:
                raise ValueError("来源账本主张ID重复：" + cid)
            seen.add(cid)
            approval = claim.get("approval") or {}
            if not isinstance(approval, dict):
                approval = {}
            # 审核记录按单条主张获取；缺审核字段不能从整个来源继承批准。
            result.append(KnowledgeCard(
                id=cid, topic=str(claim.get("topic", "decision_factors")),
                source_kind=str(src.get("source_kind", "")),
                source_name=str(src.get("source_org", "")),
                url=str(src.get("source_url", "")),
                published_on=src.get("published_on"),
                captured_on=src.get("captured_on"),
                applies_when=applies,
                route_effect=route,
                claim=claim["claim"],
                exceptions=claim["exceptions"],
                counter_evidence=claim["counter_evidence"],
                promotion=bool(src.get("promotion", False)),
                reuse_basis=str(src.get("reuse_basis", "")),
                scope=claim["claim_scope"],
                category=str(claim.get("category", "printer")),
                region=str((src.get("scope") or {}).get("region", "")),
                review_status=str(approval.get("review_status", "pending")),
                permitted_uses=tuple(approval.get("permitted_uses", ("research_index",))),
                reviewed_on=approval.get("reviewed_on"),
                recheck_on=approval.get("recheck_on"),
                route_inference_review=str(approval.get("route_inference_review", "pending")),
                source_group=str(src.get("source_group", "")),
                claim_scope=claim["claim_scope"],
                sample_scope=claim["sample_scope"],
                scope_level=scope_level,
                model_ids=tuple(claim.get("model_ids", ())),
                fact_audit_status=str(approval.get("fact_audit_status", "pending")),
                fact_audit_anchor=str(src.get("section_anchor", "")),
                decision_support_approval=str(approval.get("decision_support_approval", "not_granted")),
                approval_authority=str(approval.get("approval_authority", "")),
                approval_evidence_ref=str(approval.get("approval_evidence_ref", "")),
                use_note="route_comparison_claim",
            ))
    return tuple(result)
