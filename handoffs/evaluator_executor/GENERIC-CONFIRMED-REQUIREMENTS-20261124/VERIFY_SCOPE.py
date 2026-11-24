"""Freeze and verify the existing workspace for this local repair."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess


TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
TASK_PATH = TASK.relative_to(ROOT).as_posix()
CHAT = "shopping_decision/chat_bridge.py"
TEST = "tests/test_chat_requirement_authority.py"
SHARED = "shopping_decision/confirmed_comparison.py"
HEAD = "4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf"
MANIFEST = TASK / "BASELINE.json"
MANIFEST_HASH = TASK / "BASELINE.sha256"
MUTABLE = {"CURRENT.md", CHAT, TEST, SHARED, f"{TASK_PATH}/REPORT.md", f"{TASK_PATH}/REVIEW.md"}
EVIDENCE = (f"{TASK_PATH}/evidence/executor/", f"{TASK_PATH}/evidence/evaluator/")


def git(*args):
    return subprocess.check_output(
        ["git", "--no-optional-locks", *args], cwd=ROOT).decode("utf-8")


def file_hash(path):
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def protected_paths():
    paths = set(git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0"))
    ignored = {path.relative_to(ROOT).as_posix() for path in (MANIFEST, MANIFEST_HASH)}
    return sorted(path for path in paths - MUTABLE - ignored
                  if path and not path.startswith(EVIDENCE))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("freeze", "start", "post"), required=True)
    phase = parser.parse_args().phase
    head = git("rev-parse", "HEAD").strip()
    staged = git("diff", "--cached", "--name-only", "-z")
    chat_hash, test_hash = file_hash(ROOT / CHAT), file_hash(ROOT / TEST)
    shared_hash = file_hash(ROOT / SHARED)
    files = {path: file_hash(ROOT / path) for path in protected_paths()}
    if phase == "freeze":
        if (MANIFEST.exists() or MANIFEST_HASH.exists() or head != HEAD or staged
                or not chat_hash or test_hash or shared_hash or None in files.values()):
            raise SystemExit("工作区不符合冻结条件，先核 HEAD、索引与文件状态")
        baseline = {"baseline_head": head, "chat_start_sha256": chat_hash,
                    "protected_files_sha256": files}
        MANIFEST.write_bytes((json.dumps(baseline, ensure_ascii=False, indent=2) + "\n")
                             .encode("utf-8"))
        MANIFEST_HASH.write_bytes((file_hash(MANIFEST) + "\n").encode("ascii"))

    baseline = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = baseline["protected_files_sha256"]
    diff = sorted(path for path in files.keys() | expected.keys()
                  if files.get(path) != expected.get(path))
    manifest_hash = file_hash(MANIFEST)
    checks = {
        "head_unchanged": head == HEAD == baseline["baseline_head"],
        "index_empty": not staged,
        "protected_files_unchanged": not diff,
        "manifest_unchanged": manifest_hash == MANIFEST_HASH.read_text(encoding="ascii").strip(),
        "chat_matches_phase": bool(chat_hash) and
        (chat_hash == baseline["chat_start_sha256"]) == (phase != "post"),
        "new_test_matches_phase": bool(test_hash) == (phase == "post"),
        "shared_module_matches_phase": bool(shared_hash) == (phase == "post"),
    }
    print(json.dumps({"phase": phase, "head": head, "manifest_sha256": manifest_hash,
                      "protected_files_count": len(expected), "changed_paths": diff,
                      "chat_sha256": chat_hash, "test_sha256": test_hash,
                      "shared_sha256": shared_hash, "checks": checks},
                     ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
