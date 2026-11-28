"""One fail-closed publication boundary for rule, model and manual shopping research.

This certifies *deterministic entailment conditional on supplied typed facts*, never
the truth of an external web page, current stock, or permission to purchase.
Untrusted model prose and hand-written matrix verdicts are audit-only.
"""
from __future__ import annotations

from datetime import date, datetime
import json
from urllib.parse import urlsplit

from .evidence_comparison import (SAFE_FLAGS, _eligible, digest, number, require,
                                  rule_comparison, validate_model_result)

STATUS_TEXT = {
    "met": "根据纳入的结构化事实和比较规则，该条件在研究层面满足；不等于商品可购买。",
    "failed": "根据纳入的结构化事实和比较规则，该条件不满足；不得推荐购买。",
    "unknown": "缺少适用且具备足够来源、型号、地区和时效信息的事实，不能确认该条件。",
    "conflict": "适用事实的取值相互冲突，不能认定该条件满足。",
}
CURRENCY_UNITS = {"CNY", "USD", "EUR", "GBP", "JPY", "SGD", "HKD"}
SOURCE_TAGS = ("index", "snippet", "series", "category", "search", "screenshot")


def _iso_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.tzinfo is not None and parsed.utcoffset() is not None
    except ValueError:
        return False


def _price_requirement(request):
    return (request.get("evidence_role") == "price" or
            request.get("unit") in CURRENCY_UNITS)


def _source_assessment(fact, source, candidate_id, request, bundle):
    """Classify scope *before* allowing an external fact to support a claim.

    A URL, digest or source type alone never authenticates the content. A real
    price is usable as a conditional rule input only with an exact region,
    seller/SKU and a bounded quote; live_price_verified remains false.
    """
    if source.get("snapshot_required") or "snapshot" in source:
        from .evidence_snapshot import snapshot_valid
        if not snapshot_valid(source,fact):
            return "snapshot_unverified", False, "必要原文、版本或命题绑定失效"
    url = source.get("url", "")
    host = urlsplit(url).hostname or ""
    kind = fact.get("kind", "")
    if kind == "synthetic_probe" and host.endswith(".invalid"):
        return "synthetic_local", True, "合成测试事实；非真实商品证明"
    source_type = str(source.get("type", "")).lower()
    model_scope = str(source.get("model_scope", "")).lower()
    if any(word in source_type or word in model_scope for word in SOURCE_TAGS):
        return "insufficient_source_scope", False, "索引、摘录或系列级资料不能证明准确型号"
    if not _iso_timestamp(source.get("observed_at")):
        return "observation_time_unverified", False, "没有精确的原始观察时间"
    models = source.get("scope_models")
    if models is None:
        models = [source["model_scope"]] if source.get("model_scope") else []
    if (not isinstance(models, list) or not models or candidate_id not in models
            or any(not isinstance(m,str) or not m.strip() or m != m.strip() for m in models)):
        return "model_scope_unverified", False, "来源没有绑定准确候选型号"
    if "scope_models" in fact:
        scope = fact["scope_models"]
        if (not isinstance(scope,list) or not scope or candidate_id not in scope
                or any(not isinstance(m,str) or not m.strip() or m != m.strip() for m in scope)):
            return "model_scope_unverified", False, "事实没有绑定准确候选型号"
    observed = datetime.fromisoformat(source["observed_at"].replace("Z","+00:00"))
    if observed.date() > date.fromisoformat(bundle["as_of"]):
        return "observation_time_unverified", False, "观察时间晚于当前研究日期"
    if source.get("scope_region") != bundle["region"]:
        return "region_scope_unverified", False, "来源没有绑定需求地区"
    if _price_requirement(request):
        if kind != "live_quote":
            return "quote_not_verified", False, "展示价、目录价或旧价格不是地区有效报价"
        if not all(isinstance(source.get(field), str) and source[field].strip()
                   for field in ("quote_merchant", "quote_sku", "quote_region")):
            return "quote_identity_incomplete", False, "没有商家、SKU、报价地区三重绑定"
        if source["quote_region"] != bundle["region"] or not source.get("valid_until"):
            return "quote_scope_incomplete", False, "没有有效地区与报价有效期"
    return "qualified_structural", True, "仅验证结构与规则蕴含；外部资料内容尚未经独立核实"


def normalize_evidence_fact(fact, source, bundle, request):
    """Internal typed EvidenceFact. Raw limitations are never public wording."""
    grade, qualified, reason = _source_assessment(
        fact, source, fact["candidate_id"], request, bundle)
    return {"fact_id": fact["id"], "source_id": fact["source_id"],
            "candidate_id": fact["candidate_id"], "dimension": fact["dimension"],
            "value": fact["value"], "unit": fact["unit"],
            "scope": {"model": fact["candidate_id"],
                      "region": fact.get("scope_region", bundle["region"])},
            "observed_at": source.get("observed_at"),
            "valid_until": source.get("valid_until"),
            "grade": grade, "limitations": {"original_untrusted": fact["limitations"],
                                              "gate_reason": reason},
            "admitted": qualified and _eligible(fact, source, bundle, request)}


def publish_checked_comparison(bundle, model_result=None, *, origin="rule"):
    """Calculate and render verified/public text from typed facts, never raw prose.

    origin is exactly 'rule', 'model', or 'manual'. If a model response is
    supplied, validate its structured comparisons first, but never publish
    any of its prose (even where the response passes structural validation).
    """
    require(origin in ("rule", "model", "manual"), "unsupported_publication_origin")
    calculated = rule_comparison(bundle)
    if model_result is not None:
        validate_model_result(bundle, model_result)
        # Tradeoffs have no dimension field; demand that every cited fact
        # at least belongs to the stated candidate and an actual comparison.
        facts_by_id = {f["id"]: f for f in bundle["facts"]}
        for assessment in model_result["assessments"]:
            allowed = set()
            for cmp in next(a for a in calculated["assessments"]
                            if a["candidate_id"] == assessment["candidate_id"])["comparisons"]:
                allowed.update(cmp["fact_ids"])
            for tradeoff in assessment["tradeoffs"]:
                require(set(tradeoff["fact_ids"]) <= allowed and
                        all(facts_by_id[fid]["candidate_id"] == assessment["candidate_id"]
                            for fid in tradeoff["fact_ids"]),
                        "unbound_public_tradeoff")
    sources = {row["id"]: row for row in bundle["sources"]}
    facts = {row["id"]: row for row in bundle["facts"]}
    requirements = {row["id"]: row for row in bundle["requirements"]}
    assessments, claims, actions, seen_actions = [], [], [], set()

    def add_action(kind, candidate_id, requirement_id):
        key = (kind, candidate_id, requirement_id)
        if key in seen_actions:
            return
        seen_actions.add(key)
        descriptions = {
            "verify_price": "先取得对应商家、准确SKU、目的地区和有效时间的实时报价",
            "research": "补查当前条件缺失或冲突的来源事实，不据此下单",
            "clarify": "先确认尚未回答的用户条件",
        }
        actions.append({"kind": kind, "candidate_id": candidate_id,
                        "requirement_id": requirement_id, "description": descriptions[kind]})

    for assessment in calculated["assessments"]:
        candidate_id = assessment["candidate_id"]
        rows = []
        for comparison in assessment["comparisons"]:
            request_id = comparison["requirement_id"]
            request = requirements[request_id]
            evidence = []
            for fact_id in comparison["fact_ids"]:
                fact = facts[fact_id]
                source = sources[fact["source_id"]]
                if not _eligible(fact, source, bundle, request):
                    continue
                normalized = normalize_evidence_fact(fact, source, bundle, request)
                evidence.append({"fact_id": normalized["fact_id"],
                                 "source_id": normalized["source_id"],
                                 "source_grade": normalized["grade"],
                                 "evidence_sha256": digest({"fact":fact,"source":source}),
                                 "admitted": normalized["admitted"],
                                 "limit": normalized["limitations"]["gate_reason"]})
            admissible = [e for e in evidence if e["admitted"]]
            raw_status = comparison["status"]
            if raw_status == "conflict":
                status = "conflict" if len(admissible) == len(evidence) and len(evidence) > 1 else "unknown"
            elif raw_status in ("met", "failed"):
                status = raw_status if evidence and len(admissible) == len(evidence) else "unknown"
            else:
                status = "unknown"
            supporting = [e["fact_id"] for e in admissible] if status != "unknown" else []
            grades = sorted({e["source_grade"] for e in evidence})
            external = any(e["source_grade"] != "synthetic_local" for e in evidence)
            limit = ("仅对输入的结构化事实作规则推导，外部事实内容不保证真实"
                     if external else "仅用于本地合成验证，不代表真实商品")
            if status == "unknown":
                limit = "证据缺失、来源等级不足、地区/型号/时间不匹配或已撤销；保持待核"
            if status == "conflict":
                limit = "事实冲突，禁止选择性采用有利证据"
            claim_id = digest({"input": calculated["input_sha256"], "candidate": candidate_id,
                               "requirement": request_id, "status": status,
                               "facts": supporting})
            expression = None
            if status in ("met", "failed") and supporting and request["op"] in ("lte", "gte"):
                measured = facts[supporting[0]]["value"]
                if type(measured) in (int, float, str):
                    try:
                        symbol = "≤" if request["op"] == "lte" else "≥"
                        expression = (format(number(measured), "f") + " " + symbol + " " +
                                      format(number(request["value"]), "f"))
                    except ValueError:
                        pass
            claim = {"claim_id": claim_id, "candidate_id": candidate_id,
                     "requirement_id": request_id, "dimension": request["dimension"],
                     "status": status, "rule_id": request["op"],
                     "supporting_fact_ids": supporting,
                     "source_grade": grades or ["missing_source"],
                     "scope": {"model": candidate_id, "region": bundle["region"],
                               "as_of": bundle["as_of"]},
                     "limit": limit, "rule_expression": expression,
                     "verification": {"verified_structural": True,
                                      "source_traceable": bool(evidence),
                                      "scope_applicable": status != "unknown",
                                      "entailed_by_rule": status in ("met", "failed", "conflict"),
                                      "unverified_external_fact": external},
                     "source_audit": evidence}
            claims.append(claim)
            rows.append({"requirement_id": request_id, "claim_id": claim_id,
                         "status": status,
                         "text": (expression + "。" if expression else "") + STATUS_TEXT[status],
                         "supporting_fact_ids": supporting, "limit": limit})
            if status in ("unknown", "conflict"):
                add_action("verify_price" if _price_requirement(request) else "research",
                           candidate_id, request_id)
            elif _price_requirement(request) and not all(
                    facts[fid].get("kind") == "live_quote" for fid in supporting):
                add_action("verify_price", candidate_id, request_id)
        from .decision_actions import disposition
        state = disposition(rows, bundle["requirements"])
        assessments.append({"candidate_id": candidate_id, "research_status": state,
                            "comparisons": rows})
    public = {"schema_version": 1, "publication_schema": "verified-claims/v1",
            "origin": origin, "input_sha256": calculated["input_sha256"],
            "claims": claims, "assessments": assessments,
            "summary": "仅展示结构化事实与规则生成的研究结论；未经授权不产生购买建议。",
            "next_actions": actions, "raw_model_text_published": False,
            "manual_decision_gain_accepted": False,
            **{flag: False for flag in SAFE_FLAGS}}
    from .decision_actions import order_actions, bind_decision
    public["next_actions"] = order_actions(public, bundle["requirements"])
    bind_decision(public, bundle["requirements"], bundle)
    return public


def validate_research_claims(matrix):
    """Fail-closed adapter for the historical hand-authored research matrix.

    The old matrix has narrative statuses but no typed comparison value or
    precise source observation time. Never synthesize a positive 'true' fact
    from 'supported' or a URL. Future structured input must use the ordinary
    typed bundle and the same publish_checked_comparison entrypoint.
    """
    require(isinstance(matrix, dict) and isinstance(matrix.get("candidates"), list)
            and matrix["candidates"], "invalid_research_matrix")
    rows = matrix["candidates"]
    require(all(isinstance(r, dict) and isinstance(r.get("model_id"), str)
                and isinstance(r.get("dimensions"), dict) for r in rows),
            "invalid_research_candidate")
    dims = sorted({dimension for row in rows for dimension in row["dimensions"]})
    require(dims, "missing_research_dimensions")
    as_of = str(matrix.get("as_of_utc", ""))[:10]
    date.fromisoformat(as_of)
    user = matrix.get("fixed_user_input", {})
    region = user.get("region")
    require(isinstance(region, str) and region, "missing_research_region")
    source_map = {s["source_id"]: s for s in matrix.get("sources", [])
                  if isinstance(s, dict) and isinstance(s.get("source_id"), str)}
    source_links = []
    for row in rows:
        for dimension, value in row["dimensions"].items():
            require(isinstance(value, dict) and isinstance(value.get("source_ids"), list),
                    "invalid_manual_dimension")
            for source_id in value["source_ids"]:
                require(source_id in source_map, "unbound_manual_source")
            source_links.append({"candidate_id": row["model_id"], "dimension": dimension,
                                 "source_ids": list(value["source_ids"]),
                                 "claimed_status_audit_only": value.get("status"),
                                 "admitted_fact_count": 0,
                                 "downgrade_reason": "手写状态和摘录不是具值、具时效的独立事实"})
    bundle = {"schema_version": 1, "request_id": matrix.get("case_id", "manual-audit"),
              "as_of": as_of, "region": region,
              "candidates": [{"id": row["model_id"]} for row in rows],
              "requirements": [{"id": "manual:" + dimension, "dimension": dimension,
                                "unit": "bool", "op": "eq", "value": True,
                                "importance": "hard"} for dimension in dims],
              "sources": [], "facts": []}
    public = publish_checked_comparison(bundle, origin="manual")
    public["manual_source_audit"] = source_links
    public["manual_source_count"] = len(source_map)
    public["manual_claims_downgraded"] = sum(
        item["claimed_status_audit_only"] not in ("unknown", None) for item in source_links)
    return public
