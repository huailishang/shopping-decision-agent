"""Task-owned offline binding checks; source truth still requires independent review."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
ID = TASK.name
MODELS = {"HL-L1238W", "M232dw"}
FLAGS = ("program_integrated", "purchase_recommendation_approved", "transactions_enabled",
         "wechat_reuse_verified", "live_price_verified", "long_term_reliability_verified",
         "real_user_effect_verified")


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def stamp(value):
    result = datetime.fromisoformat(value)
    need(result.tzinfo is not None and result <= datetime.now(timezone.utc), "invalid timestamp")
    return result


def official(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and not parsed.username and any(
        host == domain or host.endswith("." + domain) for domain in ("brother.com", "brother.cn", "hp.com"))


def binding(ref):
    path = (ROOT / ref["path"]).resolve()
    need(path.is_relative_to(TASK / "evidence") and path.is_file(), "out-of-scope evidence path")
    need(sha(path) == ref["sha256"], "evidence hash mismatch: " + str(path))
    return path


def frozen():
    manifest = TASK / "FROZEN_INPUTS.json"
    need(sha(manifest) == (TASK / "FROZEN_INPUTS.sha256").read_text().strip(), "manifest changed")
    need("Frozen inputs SHA-256: " + sha(manifest) in (ROOT / "CURRENT.md").read_text(encoding="utf-8"),
         "CURRENT frozen root anchor mismatch")
    data = read(manifest)
    need(data["task_id"] == ID, "wrong frozen task")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    need(head == data["baseline_head"], "HEAD changed")
    for name, expected in data["files"].items():
        need((ROOT / name).is_file() and sha(ROOT / name) == expected, "protected file changed: " + name)
    current = {p.relative_to(ROOT).as_posix() for folder in data["inventory_roots"]
               for p in (ROOT / folder).rglob("*")
               if p.suffix in data["inventory_suffixes"] and "__pycache__" not in p.parts
               and not p.is_relative_to(TASK) and p.is_file()}
    need(current == set(data["protected_inventory"]), "protected inventory changed")
    return {"protected_files": len(data["files"]), "head": head}


def replay(out=None):
    payload = TASK / "preparation/confirmed_need.input.jsonl"
    command = [sys.executable, "-X", "utf8", "-m", "shopping_decision.dialogue_flow", "--real-printer-case"]
    start = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, cwd=ROOT, input=payload.read_bytes(), capture_output=True, timeout=60)
    end = datetime.now(timezone.utc).isoformat()
    meta = {"command_argv": command, "started_at_utc": start, "finished_at_utc": end,
            "exit_code": result.returncode, "input_sha256": sha(payload),
            "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()}
    if out:
        prefix = (ROOT / out).resolve()
        need(prefix.is_relative_to(TASK / "preparation"), "replay output outside preparation")
        for suffix, raw in ((".stdout.jsonl", result.stdout), (".stderr.log", result.stderr),
                            (".meta.json", json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"))):
            with Path(str(prefix) + suffix).open("xb") as stream:
                stream.write(raw)
    need(result.returncode == 0, "normal CLI replay failed")
    rows = [json.loads(line) for line in result.stdout.decode("utf-8").splitlines()]
    view = rows[-1]["research_case"]
    need({r["model_id"] for r in view["candidate_assessments"]} == MODELS, "baseline models changed")
    need(all(r["research_status"] == "pending_evidence" for r in view["candidate_assessments"]),
         "baseline is no longer pending")
    need(view["input_basis"] == "project_owner_proxy", "proxy input changed")
    for flag in FLAGS[1:]:
        need(view.get(flag) is False, "baseline overclaim: " + flag)
    return {"status": "baseline_replayed", "input_sha256": sha(payload), "models_pending": 2}


def delivery():
    frozen()
    data = read(TASK / "evidence/decision.json")
    work = read(TASK / "evidence/execution.json")
    need(data["task_id"] == work["task_id"] == ID, "wrong delivery task")
    need(data["input_basis"] == "project_owner_proxy" and data["input_sha256"] ==
         sha(TASK / "preparation/confirmed_need.input.jsonl"), "comparison input changed")
    for flag in FLAGS:
        need(data.get(flag) is False, "unverified flag enabled: " + flag)
    need(type(data["actual_feedback_count"]) is int and data["actual_feedback_count"] == 0, "invented feedback")
    need(isinstance(data["questions_prepared_not_sent"], list) and
         len(data["questions_prepared_not_sent"]) <= 3, "feedback question budget")
    scheduled, completed, targets = {}, {}, Counter()
    last_end = None
    events = (TASK / "evidence/attempts.jsonl").read_text(encoding="utf-8").splitlines()
    for raw in events:
        event = json.loads(raw)
        at = stamp(event["at"])
        key = event["id"]
        if event["event"] == "scheduled":
            need(key not in scheduled and len(scheduled) == len(completed), "duplicate or parallel attempt")
            need(event["kind"] in ("search", "open"), "unsupported external attempt")
            need(isinstance(event["target"], str) and event["target"].strip(), "empty target")
            need(last_end is None or at >= last_end, "attempt times out of order")
            if event["kind"] == "open":
                need(official(event["target"]), "non-official open")
            identity = (event["kind"], event["target"])
            targets[identity] += 1
            need(targets[identity] <= 2, "per-target retry budget exceeded")
            if targets[identity] == 2:
                previous = next(k for k, v in scheduled.items() if (v["kind"], v["target"]) == identity)
                need(completed[previous]["outcome"] == "failure" and
                     event.get("retry_reason") in ("timeout", "5xx"), "nonretryable repeat")
            scheduled[key] = event
        else:
            need(event["event"] == "completed" and key in scheduled and key not in completed,
                 "orphan or duplicate completion")
            need(at >= stamp(scheduled[key]["at"]), "negative attempt duration")
            need(event["outcome"] in ("success", "failure"), "unknown attempt outcome")
            binding(event["record"])
            completed[key] = event
            last_end = at
    need(set(scheduled) == set(completed), "unfinished attempts")
    counts = Counter(e["kind"] for e in scheduled.values())
    need(counts["search"] <= 4 and counts["open"] <= 6, "external budget exceeded")
    sources = {s["id"]: s for s in data["sources"]}
    need(len(sources) == len(data["sources"]), "duplicate source id")
    for source in sources.values():
        aid = source["attempt_id"]
        need(aid in completed and scheduled[aid]["kind"] == "open" and
             completed[aid]["outcome"] == "success", "source has no successful official open")
        need(source["record"] == completed[aid]["record"] and official(source["url"]), "source binding invalid")
        binding(source["record"])
        stamp(source["retrieved_at"])
        for field in ("locator", "published_or_updated", "model_binding", "mainland_scope", "limitations"):
            need(isinstance(source.get(field), str) and source[field].strip(), "missing source field: " + field)
    facts = {f["id"]: f for f in data["facts"]}
    need(len(facts) == len(data["facts"]), "duplicate fact id")
    for fact in facts.values():
        need(fact["model_id"] in MODELS and fact["criterion"] in
             ("wechat_entry", "later_print_steps", "current_service"), "invalid fact scope")
        need(fact["finding"] in ("supports", "contradicts") and fact["source_ids"] and
             set(fact["source_ids"]) <= set(sources), "unbound fact")
        for field in ("statement", "counter_evidence", "limitations"):
            need(isinstance(fact.get(field), str) and fact[field].strip(), "missing fact explanation")
    need(len(data["models"]) == 2 and {m["model_id"] for m in data["models"]} == MODELS, "model drift")
    for model in data["models"]:
        need(model["before"] == "pending_evidence" and model["after"] in
             ("pending_evidence", "conditional_document_support", "documented_scope_exclusion"), "invalid state")
        ids = model["changed_fact_ids"]
        need(isinstance(ids, list) and set(ids) <= set(facts) and
             all(facts[i]["model_id"] == model["model_id"] for i in ids), "cross-model fact")
        need(model["after"] == "pending_evidence" or ids, "unsupported state change")
        need(isinstance(model["unknowns"], list) and model["unknowns"], "unknowns erased")
        for text in (model["before_action"], model["next_action"],
                     model["workflow_branches"]["miniprogram"], model["workflow_branches"]["transfer_to_app"]):
            need(isinstance(text, str) and text.strip(), "missing actionable comparison")
    for risk in ("missing_evidence", "adversarial_content", "stale_price", "condition_conflict",
                 "accidental_order", "wrong_model", "setup_vs_reuse", "old_doc_vs_live_service"):
        need(isinstance(data["risk_review"].get(risk), str) and data["risk_review"][risk].strip(), "risk not reviewed")
    need(type(work["correction_rounds"]) is int and 0 <= work["correction_rounds"] <= 2, "correction budget")
    need(work["historical_effective_hours"] == "unknown", "historical time invented")
    total = acquisition = 0
    acquisition_window = None
    previous = None
    need(work["segments"], "no measured work segments")
    for segment in work["segments"]:
        start, end = stamp(segment["started_at"]), stamp(segment["ended_at"])
        need(end >= start and (previous is None or start >= previous), "overlapping work")
        need(segment["phase"] in ("acquisition", "synthesis", "validation") and segment["activity"], "invalid segment")
        seconds = (end - start).total_seconds()
        total += seconds
        previous = end
        if segment["phase"] == "acquisition":
            need(acquisition_window is None, "split acquisition hides elapsed time")
            acquisition_window = (start, end)
            acquisition += seconds
    need(total <= 4 * 3600 and acquisition <= 90 * 60, "work budget exceeded")
    for event in scheduled.values():
        need(acquisition_window is not None and acquisition_window[0] <= stamp(event["at"]) <=
             stamp(completed[event["id"]]["at"]) <= acquisition_window[1], "attempt outside acquisition window")
    for action in ("business_api_calls", "credentials_read", "messages_sent", "device_operations",
                   "transactions", "git_commit", "git_push"):
        need(type(work["forbidden_actions"].get(action)) is int and
             work["forbidden_actions"][action] == 0, "forbidden action: " + action)
    for name in ("COMPARISON.md", "REPORT.md"):
        need((TASK / name).is_file() and (TASK / name).stat().st_size > 100, "missing readable delivery: " + name)
    return {"status": "bindings_checked_not_source_truth", "facts": len(facts),
            "attempts": dict(counts), "recorded_work_seconds": total}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("frozen", "replay", "delivery"), required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        result = replay(args.out) if args.check == "replay" else globals()[args.check]()
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "check_failed", "reason": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
