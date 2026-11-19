"""Run bounded real inference once, or independently audit persisted experiment evidence offline."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shopping_decision.evidence_comparison import digest, rule_comparison, validate_model_result
from shopping_decision.minimal_research import build_research_case
from shopping_decision.model_comparison import codex_inference, utc_now, write_json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_scope(task):
    manifest = task / "FROZEN_INPUTS.json"
    expected = (task / "FROZEN_INPUTS.sha256").read_text().strip()
    assert sha(manifest) == expected, "frozen manifest changed"
    assert "Frozen inputs SHA-256: " + expected in (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    data = read(manifest)
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == data["baseline_head"]
    for path, expected in data["files"].items():
        assert sha(ROOT / path) == expected, "protected file changed: " + path
    inventory = {p.relative_to(ROOT).as_posix() for folder in data["inventory_roots"]
                 for p in (ROOT / folder).rglob("*") if p.suffix in data["inventory_suffixes"]
                 and "__pycache__" not in p.parts and not p.is_relative_to(task)
                 and p.relative_to(ROOT).as_posix() not in data["allowed_files"] and p.is_file()}
    assert inventory == set(data["protected_inventory"]), "out-of-scope file added or removed"


def append_event(path, event):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        stream.flush()


def run(task, model=None, resume=False):
    check_scope(task)
    cases = read(task / "cases.json")["cases"]
    evidence = task / "evidence"
    live = evidence / "live"
    if live.exists() and not resume:
        raise ValueError("existing_live_evidence_requires_explicit_resume")
    live.mkdir(parents=True, exist_ok=resume)
    legacy = evidence / "legacy"
    legacy.mkdir(exist_ok=resume)
    rules = evidence / "rules"
    rules.mkdir(exist_ok=resume)
    ledger = live / "attempts.jsonl"
    previous = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines()] if ledger.exists() else []
    counts = Counter(e["case_id"] for e in previous if e["event"] == "scheduled")
    attempts = [e for e in previous if e["event"] == "completed"]
    if len(attempts) != sum(counts.values()):
        raise ValueError("unreconciled_attempts")
    accepted = {e["case_id"]: e["id"] for e in attempts if e["outcome"] == "accepted"}
    for case in cases:
        bundle = case["bundle"]
        rule_path = rules / (case["id"] + ".json")
        if rule_path.exists():
            assert read(rule_path) == rule_comparison(bundle), "changed rule baseline"
        else:
            write_json(rule_path, rule_comparison(bundle))
        if case["legacy_pair_available"]:
            original = case["legacy_input"]
            baseline = build_research_case(original["answers"], original["research_context"])
            legacy_path = legacy / (case["id"] + ".json")
            if legacy_path.exists():
                assert read(legacy_path) == baseline, "changed legacy baseline"
            else:
                write_json(legacy_path, baseline)
    priority = {cid: i for i, cid in enumerate(("C01", "C08", "C05", "C06", "C07", "C04", "C02", "C03"))}
    queue = sorted([c for c in cases if c["id"] not in accepted and counts[c["id"]] < 2],
                   key=lambda c: priority.get(c["id"], 100))
    failed = []
    while queue and len(attempts) < 10:
        case = queue.pop(0)
        cid = case["id"]
        counts[cid] += 1
        aid = cid + "-" + str(counts[cid]).zfill(2)
        directory = live / aid
        scheduled = {"event": "scheduled", "id": aid, "case_id": cid, "at": utc_now(),
                     "input_sha256": digest(case["bundle"])}
        append_event(ledger, scheduled)
        failure = None
        try:
            codex_inference(case["bundle"], directory, timeout=120, model=model)
            accepted[cid] = aid
        except (RuntimeError, OSError, ValueError) as exc:
            failure = str(exc)
            failed.append(case)
        meta_path = directory / "meta.json"
        terminal = {"event": "completed", "id": aid, "case_id": cid, "at": utc_now(),
                    "outcome": "accepted" if failure is None else "rejected", "failure": failure,
                    "meta_sha256": sha(meta_path) if meta_path.is_file() else None}
        append_event(ledger, terminal)
        attempts.append(terminal)
        print(json.dumps({"attempt": aid, "outcome": terminal["outcome"], "failure": failure}), flush=True)
        if failure and any(code in failure for code in ("model_not_found", "invalid_request_error", "unavailable")):
            break
        if not queue and failed and len(attempts) < 10:
            queue = sorted({x["id"]: x for x in failed if counts[x["id"]] < 2 and
                            x["id"] not in accepted}.values(), key=lambda x: (x["id"] not in ("C01", "C08"), x["id"]))
            failed = []
    summary = {"task_id": task.name, "cases_sha256": sha(task / "cases.json"),
               "case_count": len(cases), "legacy_pair_count": sum(c["legacy_pair_available"] for c in cases),
               "attempt_count": len(attempts), "accepted": accepted, "requested_model": model or "cli_default",
               "interrupted_receipts_missing": sum(e["outcome"] == "interrupted" for e in attempts),
               "new_external_product_facts": 0, "real_user_feedback_count": 0,
               "comparison_quality_gain": "not_determined_by_automated_checks",
               "model_requests_only": True, "live_price_verified": False, "transactions_enabled": False}
    summary_path = evidence / "paired.json"
    if summary_path.exists():
        batches = evidence / "batches"
        batches.mkdir(exist_ok=True)
        target = batches / ("paired-before-" + str(len(attempts)).zfill(2) + ".json")
        if target.exists():
            raise ValueError("existing_summary_archive_would_be_overwritten")
        summary_path.rename(target)
    write_json(summary_path, summary)
    return summary


def audit(task):
    check_scope(task)
    cases = read(task / "cases.json")["cases"]
    by_id = {c["id"]: c for c in cases}
    summary = read(task / "evidence/paired.json")
    assert summary["cases_sha256"] == sha(task / "cases.json")
    ledger = task / "evidence/live/attempts.jsonl"
    starts, ends, counts = {}, {}, Counter()
    for raw in ledger.read_text(encoding="utf-8").splitlines():
        event = json.loads(raw)
        aid, cid = event["id"], event["case_id"]
        assert cid in by_id
        if event["event"] == "scheduled":
            assert aid not in starts and len(starts) == len(ends), "parallel or duplicate call"
            starts[aid] = event
            counts[cid] += 1
            assert event["input_sha256"] == digest(by_id[cid]["bundle"])
        else:
            assert event["event"] == "completed" and aid in starts and aid not in ends
            ends[aid] = event
            directory = task / "evidence/live" / aid
            assert sha(directory / "meta.json") == event["meta_sha256"]
            meta = read(directory / "meta.json")
            assert meta["input_sha256"] == starts[aid]["input_sha256"]
            if event["outcome"] == "interrupted":
                assert meta["status"] == "interrupted" and meta["raw_receipt_available"] is False
                continue
            assert meta.get("live_attempt") is True
            raw_events = [json.loads(x) for x in (directory / "stdout.events.jsonl").read_text(encoding="utf-8").splitlines()]
            actual_tools = [e for e in raw_events if isinstance(e.get("item"), dict) and
                            e["item"].get("type") not in ("agent_message", "reasoning", "error", "todo_list")]
            assert not actual_tools, "actual model tool use"
            assert digest(read(directory / "request.json")) == meta["input_sha256"]
            assert meta["stdout_sha256"] == sha(directory / "stdout.events.jsonl")
            assert meta["stderr_sha256"] == sha(directory / "stderr.log")
            if event["outcome"] == "accepted":
                result = validate_model_result(by_id[cid]["bundle"], read(directory / "response.json"))
                assert result == read(directory / "validated.json")
                assert meta["status"] == "accepted" and meta["exit_code"] == 0
                assert summary["accepted"].get(cid) == aid
            else:
                assert meta["status"] == "rejected" and not (directory / "validated.json").exists()
    assert set(starts) == set(ends) and len(starts) <= 10
    assert set(counts) == set(by_id), "model cases not attempted: " + ",".join(sorted(set(by_id) - set(counts)))
    assert max(counts.values()) <= 2, "per-case attempt ceiling exceeded"
    assert len(starts) == summary["attempt_count"]
    assert {"C01", "C08"} <= set(summary["accepted"]), "limited real integration not established"
    for case in cases:
        assert rule_comparison(case["bundle"]) == read(task / "evidence/rules" / (case["id"] + ".json"))
        if case["legacy_pair_available"]:
            original = case["legacy_input"]
            assert build_research_case(original["answers"], original["research_context"]) == read(
                task / "evidence/legacy" / (case["id"] + ".json"))
    return {"status": "offline_audit_passed", "attempts": len(starts), "accepted_cases": len(summary["accepted"]),
            "legacy_pairs": summary["legacy_pair_count"], "semantic_quality_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--live", action="store_true")
    group.add_argument("--audit", action="store_true")
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--model", help="Account-supported Codex model for explicit live inference")
    parser.add_argument("--resume", action="store_true", help="retain all previous attempts and remaining quota")
    args = parser.parse_args()
    task = args.task.resolve()
    try:
        result = run(task, args.model, args.resume) if args.live else audit(task)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (AssertionError, ValueError, KeyError, OSError, RuntimeError) as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
