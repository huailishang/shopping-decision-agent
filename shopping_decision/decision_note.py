"""Read-only local decision explanation from the same current product result."""
import json
from datetime import date

def render_note(report, guide, prompt):
    public=(report.get("cognition_comparison") or {}).get("public") or report.get("public_decision") or {}
    g=json.loads(guide["cognition_guide_json"])
    context=report["cognition_guidance"]
    binding=public.get("decision_binding",{})
    comparison=report.get("cognition_comparison") or {}
    bundle=comparison.get("bundle") or (report.get("research_result") or {}).get("verified_research_bundle") or {}
    note={
        "schema_version":1,"document_type":"local_research_decision_note",
        "as_of":date.today().isoformat(),"purpose":"本机研究说明，不是订单、购买许可或实时报价",
        "original_turns":report["dialogue"]["history"],
        "confirmed_requirements":report["confirmed_fields"],
        "deferred":report["deferred_fields"],"withdrawn":report["withdrawn_fields"],
        "guide_id":g["guide_id"],"guide_version":g["version"],"guide_status":g["status"],
        "parameter_reference":g["dimensions"],"cognition_claims":g["claims"],"cognition_sources":g["sources"],
        "routes":g["routes"],"usage_research":context["usage_research"],
        "candidate_assessments":public.get("assessments",[]),"candidate_claims":public.get("claims",[]),
        "candidate_source_records":bundle.get("sources",[]),"requirements":binding.get("requirements",[]),
        "personal_assumptions":public.get("cost_comparison",{}),"unknowns":g["unknowns"],
        "next_step":prompt,"guidance_focus":context.get("guidance_focus"),"guide_reference_change":report.get("guide_reference_change"),
        "invalidation":"需求、认知来源版本、时点、地区、商品证据或假设变化均应重新计算。",
        "purchase_recommendation_approved":False,"transactions_enabled":False,"live_price_verified":False,
    }
    return json.dumps(note,ensure_ascii=False,indent=2)
