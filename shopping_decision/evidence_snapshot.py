"""Validate a minimal locally retained source excerpt and its exact fact binding."""
from .evidence_comparison import digest

def snapshot_valid(source,fact):
    snapshot=source.get("snapshot")
    if not isinstance(snapshot,dict) or source.get("revoked"):
        return False
    try:
        body=snapshot["body"]
        return (snapshot["sha256"]==digest(body)
            and body["excerpt_sha256"]==digest(body["excerpt"])
            and body["source_id"]==source["id"] and body["url"]==source["url"]
            and body["models"]==source["scope_models"]
            and body["fact"]=={k:fact[k] for k in ("id","candidate_id","dimension","unit","value")}
            and body["version"] and body["locator"] and body["review_status"]=="executor_text_rechecked"
            and body["model_visual_checked"] is True)
    except (KeyError,TypeError,ValueError,OverflowError,RecursionError):
        return False
