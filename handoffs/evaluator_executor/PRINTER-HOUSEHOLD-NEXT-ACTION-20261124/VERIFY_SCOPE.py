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
ADAPTER = "shopping_decision/printer_reviewed_evidence.py"
DATA = "knowledge/printer_reviewed_evidence_v2.json"
LEGACY_TEST = "tests/test_printer_reviewed_evidence.py"
TEST = "tests/test_printer_purchase_checks.py"
CHECKS = "shopping_decision/printer_purchase_checks.py"
PRODUCT = (CHAT, ADAPTER, DATA, LEGACY_TEST, TEST, CHECKS)
HEAD = "4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf"
MANIFEST = TASK / "BASELINE.json"
MANIFEST_HASH = TASK / "BASELINE.sha256"
MUTABLE = {*PRODUCT, "CURRENT.md", f"{TASK_PATH}/DECISION_HANDOFF.md", f"{TASK_PATH}/REPORT.md", f"{TASK_PATH}/REVIEW.md"}
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
    product = {name: file_hash(ROOT / name) for name in PRODUCT}
    files = {path: file_hash(ROOT / path) for path in protected_paths()}
    if phase == "freeze":
        if (MANIFEST.exists() or MANIFEST_HASH.exists() or head != HEAD or staged
                or not all(product[key] for key in (CHAT, ADAPTER, LEGACY_TEST))
                or any(product[k] for k in (DATA, TEST, CHECKS))
                or None in files.values()):
            raise SystemExit("工作区不符合冻结条件，先核 HEAD、索引与文件状态")
        baseline = {"baseline_head": head, "original_product": product,
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
        "product_matches_delivery": (
            product == baseline["original_product"] if phase != "post" else
            all(product[key] for key in (CHAT, ADAPTER, LEGACY_TEST, TEST, CHECKS))
            and product[ADAPTER] != baseline["original_product"][ADAPTER]
        ),
    }
    print(json.dumps({"phase": phase, "head": head, "manifest_sha256": manifest_hash,
                      "protected_files_count": len(expected), "changed_paths": diff,
                      "product_sha256": product,
                      "checks": checks},
                     ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
