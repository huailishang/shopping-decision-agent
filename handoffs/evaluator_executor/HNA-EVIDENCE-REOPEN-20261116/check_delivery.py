"""Read-only structural checks for a bounded evidence-collection task.
No network, source admission, legal approval, product restore, or original-file writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

class CheckError(ValueError):
    pass

def need(condition, message):
    if not condition:
        raise CheckError(message)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inside(root, name):
    need(isinstance(name, str) and name, "missing relative path")
    path = (root / name).resolve()
    need(path.is_relative_to(root.resolve()), "path escapes workspace")
    return path

def bound(root, task_dir, ref):
    need(isinstance(ref, dict), "missing evidence binding")
    path = inside(root, ref.get("path"))
    prefix = (root / task_dir / "evidence/collected").resolve()
    need(path.is_relative_to(prefix), "evidence must be in this task collected directory")
    need(path.is_file() and digest(path) == ref.get("sha256"), "evidence missing or hash mismatch")
    return path

def safe_url(value, plan):
    need(isinstance(value, str), "missing document URL")
    uri = urlsplit(value)
    need(uri.scheme == "https" and uri.hostname in plan["approved_hosts"], "unapproved source host")
    need(not uri.username and not uri.password, "URL must not contain credentials")
    need(not any(k.lower() in {"token","access_token","api_key","key","session","authorization"}
                 for k,_ in parse_qsl(uri.query)), "URL contains credential-like query")
    clean = uri._replace(fragment="").geturl()
    need(clean not in plan["blocked_urls"], "known restricted or empty entry cannot be retried")
    return clean

def validate_receipt(root, plan, receipt):
    need(receipt.get("schema") == "evidence-acquisition-receipt/v2", "receipt schema mismatch")
    need(receipt.get("task_id") == plan["task_id"], "receipt task mismatch")
    need(receipt.get("outcome") in {"candidate_found","no_actionable_evidence"}, "unknown collection outcome")
    for name in ("purchase_recommendation_approved","transactions_enabled","parent_restoration_authorized"):
        need(receipt.get(name) is False, "collection cannot authorize product or transaction")
    counts = receipt.get("prohibited_actions")
    need(isinstance(counts, dict) and set(counts) == set(plan["prohibited_actions"]), "missing prohibited-action ledger")
    need(all(type(x) is int and x == 0 for x in counts.values()), "prohibited action was reported")
    prior = inside(root, plan["prior_ledger"]["path"])
    need(prior.is_file() and digest(prior) == plan["prior_ledger"]["sha256"], "parent action ledger changed")
    ledger = json.loads(prior.read_text(encoding="utf-8-sig"))
    need(ledger["budget"]["search_used"] == ledger["budget"]["search_limit"], "parent search budget differs")
    prior_reads = ledger["budget"]["document_reads_used"]
    need(ledger["budget"]["document_read_limit"]-prior_reads == plan["document_read_limit"], "remaining read budget differs")
    routes = {row["id"]:row for row in plan["routes"]}
    actions = receipt.get("actions")
    need(isinstance(actions, list) and actions, "must perform and record collection work")
    by_id, reads, seen_urls = {}, {k:0 for k in routes}, set()
    for action in actions:
        need(isinstance(action, dict), "action must be an object")
        aid, rid = action.get("id"), action.get("route_id")
        need(isinstance(aid,str) and aid and aid not in by_id and rid in routes, "duplicate action or wrong route")
        need(action.get("recorded_at"), "action observation time missing")
        need(action.get("outcome") in {"readable","no_relevant_fact","new_fact","restricted","empty","owner_only","timeout"}, "action terminal outcome missing")
        proof = bound(root, plan["task_dir"], action.get("evidence"))
        kind = action.get("kind")
        if kind == "local":
            need(action.get("input_path") in routes[rid]["local_inputs"], "local input not in frozen route")
        else:
            need(kind in {"document","render"}, "search/API or unknown action is forbidden")
            url = safe_url(action.get("url"), plan)
            origin = action.get("discovered_from")
            if url not in routes[rid]["seed_urls"]:
                need(origin in by_id and by_id[origin]["route_id"] == rid, "new URL needs an earlier source link")
                source_proof = bound(root, plan["task_dir"], by_id[origin]["evidence"])
                need(url in source_proof.read_text(encoding="utf-8"), "link absent from captured source")
            if kind == "document":
                need(url not in seen_urls, "repeat document request is forbidden")
                seen_urls.add(url)
            else:
                need(origin in by_id and by_id[origin].get("url") == action["url"], "render must bind a prior document")
                need(by_id[origin]["outcome"] not in {"restricted","empty","owner_only","timeout"}, "cannot render or retry a restricted or failed document")
            reads[rid] += 1
        by_id[aid] = action
    need(sum(reads.values()) <= plan["document_read_limit"], "total document budget exceeded")
    for rid,used in reads.items():
        need(used <= routes[rid]["document_read_limit"], "route document budget exceeded")
    materials = receipt.get("materials")
    need(isinstance(materials,list), "missing material result list")
    for row in materials:
        need(row.get("action_id") in by_id, "material must bind an actual action")
        need(row.get("review_status") == "pending_evaluator", "executor cannot approve sources")
        for field in ("model_or_subject_scope","supported_claim","limitations","action_relevance","observed_on"):
            need(isinstance(row.get(field),str) and row[field].strip(), "material meaning or limit missing")
        need(row.get("novelty") == "new_relevant_fact", "candidate must identify relevant fact increment")
        bound(root,plan["task_dir"],row.get("evidence"))
    results = receipt.get("route_results")
    need(isinstance(results,list) and len(results)==len(routes), "both route results required")
    need({r.get("route_id") for r in results} == set(routes), "route coverage missing")
    for result in results:
        rid = result["route_id"]
        need(result.get("owner") == routes[rid]["owner"] and result.get("reason"), "route owner or reason missing")
        ids = result.get("action_ids")
        need(isinstance(ids,list) and all(i in by_id and by_id[i]["route_id"]==rid for i in ids), "route action binding missing")
        need(result.get("state") in {"candidate","no_relevant_fact","restricted","owner_only","budget_stop","skipped_sufficient"}, "route terminal state missing")
        if result["state"] == "skipped_sufficient":
            need(receipt["outcome"] == "candidate_found" and materials, "cannot skip work without sufficient candidate")
        else:
            need(ids, "route must be investigated, not left waiting")
    if receipt["outcome"] == "candidate_found":
        need(materials and any(x["state"]=="candidate" for x in results), "candidate outcome lacks candidate evidence")
    else:
        need(not materials and all(x["state"] not in {"candidate","skipped_sufficient"} for x in results), "empty result contradicts route evidence")
        request = receipt.get("owner_request")
        need(isinstance(request,dict) and request.get("recipient_role") and request.get("exact_item"), "no-result needs a specific owner request")
        need(request.get("sent") is False, "owner request must remain unsent")
        bound(root,plan["task_dir"],request.get("evidence"))
    need(isinstance(receipt.get("next_step"),str) and receipt["next_step"].strip(), "next step missing")
    return {"status":"submission_structure_checked_not_source_approval",
            "outcome":receipt["outcome"],"document_reads":sum(reads.values()),
            "parent_reads_total":prior_reads+sum(reads.values()),"candidate_count":len(materials)}

def verify_frozen(root, manifest_path, expected_sha):
    need(manifest_path.is_file() and digest(manifest_path)==expected_sha, "frozen manifest changed")
    data=json.loads(manifest_path.read_text(encoding="utf-8"))
    need(data.get("files"), "missing frozen inputs")
    for name,sha in data["files"].items():
        path=inside(root,name)
        need(path.is_file() and digest(path)==sha, "frozen input changed: "+name)
    snapshot=json.loads(inside(root,data["source_snapshot"]).read_text(encoding="utf-8"))
    for name,sha in snapshot["source_hashes"].items():
        need(digest(inside(root,name))==sha, "product source changed during collection")
    return {"status":"frozen_inputs_match","product_sources_checked":len(snapshot["source_hashes"])}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,default=Path.cwd())
    parser.add_argument("--check",choices=("frozen","receipt"),required=True)
    parser.add_argument("--frozen",type=Path,required=True)
    parser.add_argument("--frozen-sha",required=True)
    args=parser.parse_args()
    root=args.repo.resolve()
    task=Path(__file__).resolve().parent
    try:
        frozen=args.frozen if args.frozen.is_absolute() else root/args.frozen
        result=verify_frozen(root,frozen,args.frozen_sha)
        if args.check=="receipt":
            plan=json.loads((task/"acquisition_plan.json").read_text(encoding="utf-8"))
            receipt=json.loads((task/"evidence/acquisition_receipt.json").read_text(encoding="utf-8"))
            result=validate_receipt(root,plan,receipt)
    except (CheckError,OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({"status":"check_failed","reason":str(exc)},ensure_ascii=True))
        return 1
    print(json.dumps(result,ensure_ascii=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
