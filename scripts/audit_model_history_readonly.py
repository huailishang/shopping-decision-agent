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

# Owner-directed worksheet transition: historical bytes must still match the
# original manifest at the pinned pre-task commit; current bytes must match
# the exact candidate tested by the executor (independent review pending).
# No wildcard or caller-supplied exception; no historical file is rewritten.
WORKSHEET_PRE_TASK_COMMIT = "c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f"
WORKSHEET_PREVIOUS_SOURCE_SHA256 = {
    'desktop/DesktopBridgeClient.java': 'ba0a8c8aa5a5d1309721d0b79f09eba472a9cee000e656c00f3d579b9c2f8ff3',
    # Cognition-first typed user input; old bytes remain checked against the same pin.
    'shopping_decision/dialogue_flow.py': '080e2cfbc6ff501e0aa131b5a4ef4691b1c5f63161006e698db36a80588dfaba',
    'desktop/ShoppingDecisionDesktop.java': '873437da98eca260f8d26edd3042daa1e366c6c039f75d98cc3351dcd6659525',
}

# Focus-guidance transition: exact current candidates; original historical
# commit and predecessor candidate bytes above remain independently pinned.
WORKSHEET_APPROVED_SOURCE_SHA256 = {
    **WORKSHEET_PREVIOUS_SOURCE_SHA256,
    'desktop/ShoppingDecisionDesktop.java': '92639e5b600c420936c8b96d3476e101b3e7b4864179e78e9d9e210abe0c87d3',
    'shopping_decision/dialogue_flow.py': 'abeb0355d46f9def24d38ff0f508f49c75875d7aee8d3edf2f6770be834ee815',
}

# Only the exact two R1 test revisions independently reviewed on 2026-11-23
# may drift from the frozen historical inventory. Never blanket-allow test edits.
REVIEWED_R1_TEST_SHA256 = {
    "tests/test_minimal_research_flow.py": "50a2a14b70bb32cea4ffb11fd8e2d51a34697fd49b1a738ad552870e30691c8b",
    "tests/test_printer_decision_plan.py": "00efd08e1ce79f1c958575bb5531c0391f6cbe8a544e182573fa46e39a00ede4",
}


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

    # Reviewed R1 test revisions are allowed only at the exact evaluator SHA.
    for filename, expected in REVIEWED_R1_TEST_SHA256.items():
        p = ROOT / filename
        check(p.is_file(), "approved_r1_test_missing:" + filename)
        check(sha(p.read_bytes()) == expected, "approved_r1_test_sha_mismatch:" + filename)

    historic_drifts = []
    for filename, expected in manifest["files"].items():
        p = ROOT / filename
        if not p.is_file() or sha(p.read_bytes()) != expected:
            historic_drifts.append(filename)
            if filename in WORKSHEET_APPROVED_SOURCE_SHA256:
                check(p.is_file() and sha(p.read_bytes()) == WORKSHEET_APPROVED_SOURCE_SHA256[filename],
                      "worksheet_current_source_sha_mismatch:" + filename)
                try:
                    historical = subprocess.check_output(
                        ["git", "show", WORKSHEET_PRE_TASK_COMMIT + ":" + filename],
                        cwd=ROOT, stderr=subprocess.DEVNULL)
                except (OSError, subprocess.CalledProcessError) as exc:
                    raise ValueError("worksheet_historical_source_unavailable:" + filename) from exc
                check(sha(historical) == expected,
                      "worksheet_historical_source_sha_mismatch:" + filename)
            else:
                check(filename in CURRENT_TASK_ALLOWED_DRIFT or
                      filename in REVIEWED_R1_TEST_SHA256,
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
