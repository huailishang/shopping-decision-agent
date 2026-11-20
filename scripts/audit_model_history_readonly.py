"""Strict read-only audit of historical model attempts despite legitimate later HEAD drift.

Never repairs or reinterprets the frozen parent's VP-04. Exit 0 means the
historical receipts are intact AND the experiment remains incomplete.
"""
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
from shopping_decision.evidence_comparison import digest

PIN = (ROOT / "handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118"
       / "post_review/PRINTER-TRUSTED-DECISION-20261119/post_review"
       / "GENERIC-EVIDENCE-CLAIM-GATE-20261119")
CURRENT_TASK_ALLOWED_DRIFT = {"shopping_decision/chat_bridge.py"}


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit_history(task: Path, *, ledger_bytes_override: bytes | None = None):
    task = task.resolve()
    check(task.is_relative_to(ROOT), "historical_task_outside_repository")
    manifest_path = task / "FROZEN_INPUTS.json"
    frozen_sha = (task / "FROZEN_INPUTS.sha256").read_text(encoding="utf-8").strip()
    check(sha(manifest_path.read_bytes()) == frozen_sha, "historical_frozen_manifest_sha_mismatch")
    manifest = load(manifest_path)

    pin_path = PIN / "BASELINE.json"
    pin_sha = (PIN / "BASELINE.sha256").read_text(encoding="utf-8").strip()
    check(sha(pin_path.read_bytes()) == pin_sha, "pinned_baseline_sha_mismatch")
    baseline = load(pin_path)
    protected = baseline["immutable_files_sha256"]
    for filename, expected in protected.items():
        p = ROOT / filename
        check(p.is_file() and sha(p.read_bytes()) == expected,
              "protected_file_sha_mismatch:" + filename)

    # The original frozen inventory is read, but current task's chat module is
    # explicitly allowed to evolve. All OTHER original files stay byte-identical.
    historic_drifts = []
    for filename, expected in manifest["files"].items():
        p = ROOT / filename
        if not p.is_file() or sha(p.read_bytes()) != expected:
            historic_drifts.append(filename)
            check(filename in CURRENT_TASK_ALLOWED_DRIFT,
                  "unapproved_historical_file_drift:" + filename)
    actual_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    frozen_head = manifest["baseline_head"]

    cases_path = task / "cases.json"
    cases = load(cases_path)["cases"]
    by_id = {item["id"]: item for item in cases}
    check(len(cases) == len(by_id), "duplicate_case_id")
    summary = load(task / "evidence/paired.json")
    check(summary["cases_sha256"] == sha(cases_path.read_bytes()), "cases_sha_mismatch")

    ledger = task / "evidence/live/attempts.jsonl"
    real_ledger = ledger.read_bytes()
    ledger_relative = ledger.relative_to(ROOT).as_posix()
    check(ledger_relative in protected, "historical_ledger_not_pinned")
    check(sha(real_ledger) == protected[ledger_relative], "historical_ledger_sha_mismatch")
    candidate_bytes = real_ledger if ledger_bytes_override is None else ledger_bytes_override
    check(sha(candidate_bytes) == protected[ledger_relative], "historical_ledger_sha_mismatch")
    events = [json.loads(line) for line in candidate_bytes.decode("utf-8").splitlines() if line.strip()]
    starts, ends = {}, {}
    counts = Counter()
    for event in events:
        aid, case_id = event["id"], event["case_id"]
        check(case_id in by_id and isinstance(aid, str), "invalid_historical_case_or_attempt_id")
        if event.get("event") == "scheduled":
            check(aid not in starts and len(starts) == len(ends),
                  "duplicate_or_parallel_historical_attempt")
            check(event["input_sha256"] == digest(by_id[case_id]["bundle"]),
                  "historical_scheduled_input_mismatch")
            starts[aid] = event
            counts[case_id] += 1
            check(counts[case_id] <= 2, "per_case_attempt_limit_exceeded")
        else:
            check(event.get("event") == "completed" and aid in starts and aid not in ends
                  and starts[aid]["case_id"] == case_id, "unpaired_historical_event")
            ends[aid] = event
            directory = task / "evidence/live" / aid
            meta_path = directory / "meta.json"
            check(meta_path.is_file() and sha(meta_path.read_bytes()) == event["meta_sha256"],
                  "historical_receipt_meta_sha_mismatch:" + aid)
            meta = load(meta_path)
            check(meta["input_sha256"] == starts[aid]["input_sha256"],
                  "historical_meta_input_mismatch:" + aid)
            if event.get("outcome") == "interrupted":
                check(meta["status"] == "interrupted"
                      and meta.get("raw_receipt_available") is False,
                      "invalid_interrupted_attempt:" + aid)
                continue
            check(meta.get("live_attempt") is True and event.get("outcome") in ("rejected", "accepted"),
                  "invalid_attempt_outcome:" + aid)
            check(sha((directory / "stdout.events.jsonl").read_bytes()) == meta["stdout_sha256"],
                  "historical_stdout_sha_mismatch:" + aid)
            check(sha((directory / "stderr.log").read_bytes()) == meta["stderr_sha256"],
                  "historical_stderr_sha_mismatch:" + aid)
            check(digest(load(directory / "request.json")) == meta["input_sha256"],
                  "historical_request_sha_mismatch:" + aid)
            check((event["outcome"] == "rejected" and meta["status"] == "rejected") or
                  (event["outcome"] == "accepted" and meta["status"] == "accepted"),
                  "historical_status_mismatch:" + aid)
    check(set(starts) == set(ends), "unpaired_historical_attempt")
    check(len(starts) == len(ends) == summary["attempt_count"] == 6,
          "historical_attempt_count_mismatch")
    check(len(starts) <= 10, "historical_max_attempts_exceeded")
    missing = sorted(set(by_id) - set(counts))
    check(missing == ["C05", "C06", "C07"], "historical_missing_cases_changed")
    check(not summary.get("accepted"), "unexpected_historical_accepted_model_case")
    return {"audit_status": "historical_receipts_intact_experiment_incomplete",
            "parent_vp04_status": "REJECTED_not_retroactively_repaired",
            "frozen_manifest_sha_valid": True, "protected_files_valid": len(protected),
            "original_manifest_file_count": len(manifest["files"]),
            "allowed_current_source_drift": sorted(historic_drifts),
            "frozen_head": frozen_head, "current_head": actual_head,
            "head_drift": actual_head != frozen_head,
            "scheduled": len(starts), "completed": len(ends),
            "attempt_limit": 10, "not_attempted_cases": missing,
            "accepted_model_outputs": 0, "old_evidence_modified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit_history(args.task)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "rejected", "reason": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
