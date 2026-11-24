"""Verify the admitted local snapshot without modifying the index or worktree."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
TASK_PATH = TASK.relative_to(ROOT).as_posix()
CHAT = "shopping_decision/chat_bridge.py"
TEST = "tests/test_chat_context_admission.py"
CHANGEABLE = {"CURRENT.md", CHAT, TEST, f"{TASK_PATH}/REPORT.md",
              f"{TASK_PATH}/DECISION_HANDOFF.md", f"{TASK_PATH}/REVIEW.md"}
EVIDENCE_OUTPUT = (f"{TASK_PATH}/evidence/executor/", f"{TASK_PATH}/evidence/evaluator/")


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", *args], cwd=ROOT).decode("utf-8")


def file_sha(path):
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def working_files():
    return {name for name in git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
            if name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("start", "post"), required=True)
    phase = parser.parse_args().phase
    baseline_file = TASK / "BASELINE.json"
    manifest_hash = file_sha(baseline_file)
    expected_hash = (TASK / "BASELINE.sha256").read_text(encoding="utf-8").strip()
    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    frozen = baseline["protected_files_sha256"]
    head = git("rev-parse", "HEAD").strip()
    staged = [name for name in git("diff", "--cached", "--name-only", "-z").split("\0") if name]
    mismatch = [name for name, expected in frozen.items() if file_sha(ROOT / name) != expected]
    unlisted = working_files() - set(frozen) - CHANGEABLE - {
        f"{TASK_PATH}/BASELINE.json", f"{TASK_PATH}/BASELINE.sha256"
    }
    extra = sorted(name for name in unlisted if not name.startswith(EVIDENCE_OUTPUT))
    chat_sha = file_sha(ROOT / CHAT)
    test_sha = file_sha(ROOT / TEST)
    checks = {
        "head_unchanged": head == baseline["baseline_head"],
        "index_empty": not staged,
        "manifest_unchanged": manifest_hash == expected_hash,
        "protected_files_unchanged": not mismatch,
        "no_extra_paths": not extra,
        "chat_snapshot_matches_phase": chat_sha is not None and
            (chat_sha == baseline["chat_start_sha256"]) == (phase == "start"),
        "new_test_matches_phase": (test_sha is None) == (phase == "start"),
    }
    print(json.dumps({"phase": phase, "head": head, "manifest_sha256": manifest_hash,
                      "protected_files_count": len(frozen), "mismatch": mismatch,
                      "unlisted_paths": extra, "staged": staged, "chat_sha256": chat_sha,
                      "new_test_sha256": test_sha, "checks": checks},
                     ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    sys.exit(main())
