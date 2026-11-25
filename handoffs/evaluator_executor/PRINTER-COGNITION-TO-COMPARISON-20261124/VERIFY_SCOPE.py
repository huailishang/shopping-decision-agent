"""Freeze the current checkout and verify the permitted changes."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
TASK_PATH = TASK.relative_to(ROOT).as_posix()
HEAD = "3ae3514c482ab1b35335cd2978301efb348a09cd"
BASELINE = TASK / "BASELINE.json"
CHECKSUM = TASK / "BASELINE.sha256"
REQUIRED = (
    'shopping_decision/chat_bridge.py',
    'shopping_decision/printer_reviewed_evidence.py',
    'shopping_decision/printer_purchase_checks.py',
    'shopping_decision/printer_effect_probe.py',
    'shopping_decision/selection_criteria.py',
    'shopping_decision/confirmed_comparison.py',
    'shopping_decision/claim_gate.py',
    'shopping_decision/model_comparison.py',
    'shopping_decision/evidence_comparison.py',
    'tests/test_printer_purchase_checks.py',
    'tests/test_printer_reviewed_evidence.py',
    'tests/test_publication_entry.py',
    'tests/test_minimal_research_flow.py',
    'tests/test_chat_requirement_authority.py',
)
OPTIONAL = (
    'shopping_decision/cognition_comparison.py',
    'knowledge/printer_cognition_comparison_v1.json',
    'tests/test_cognition_comparison.py',
)
PRODUCT = REQUIRED + OPTIONAL
WRITABLE = {
    "CURRENT.md",
    *PRODUCT,
    *(f"{TASK_PATH}/{name}" for name in (
        "BASELINE.json", "BASELINE.sha256", "COMPARISON.md", "REPORT.md", "REVIEW.md",
    )),
}
EVIDENCE = (f"{TASK_PATH}/evidence/executor/", f"{TASK_PATH}/evidence/evaluator/")


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", *args], cwd=ROOT)


def digest(path):
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def snapshot():
    paths = git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    protected = {
        path: digest(ROOT / path)
        for path in sorted(set(paths.decode("utf-8").split("\0")) - WRITABLE)
        if path and not path.startswith(EVIDENCE)
    }
    return {
        "baseline_head": git("rev-parse", "HEAD").decode("ascii").strip(),
        "product_sha256": {path: digest(ROOT / path) for path in PRODUCT},
        "protected_files_sha256": protected,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("freeze", "start", "post"), required=True)
    phase = parser.parse_args().phase
    actual = snapshot()
    empty_index = not git("diff", "--cached", "--name-only", "-z")
    products_present = all(actual["product_sha256"][path] for path in REQUIRED)
    if phase == "freeze":
        if (BASELINE.exists() or CHECKSUM.exists() or not empty_index
                or actual["baseline_head"] != HEAD or not products_present
                or not all(actual["protected_files_sha256"].values())):
            raise SystemExit("无法冻结，先核对 HEAD、索引、基线文件及产品状态")
        BASELINE.write_bytes((json.dumps(actual, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        CHECKSUM.write_bytes((digest(BASELINE) + "\n").encode("ascii"))

    expected = json.loads(BASELINE.read_text(encoding="utf-8"))
    old_protected = expected["protected_files_sha256"]
    new_protected = actual["protected_files_sha256"]
    changed = sorted(path for path in old_protected.keys() | new_protected.keys()
                     if old_protected.get(path) != new_protected.get(path))
    manifest_hash = digest(BASELINE)
    changed_product = [path for path in PRODUCT
                       if actual["product_sha256"][path] != expected["product_sha256"][path]]
    checks = {
        "head_matches_baseline": actual["baseline_head"] == expected["baseline_head"] == HEAD,
        "index_empty": empty_index,
        "manifest_matches_checksum": manifest_hash == CHECKSUM.read_text(encoding="ascii").strip(),
        "protected_files_unchanged": not changed,
        "required_product_files_present": products_present,
    }
    if phase != "post":
        checks["product_matches_preflight"] = not changed_product
    print(json.dumps({
        "phase": phase,
        "head": actual["baseline_head"],
        "manifest_sha256": manifest_hash,
        "protected_files_count": len(old_protected),
        "changed_protected_paths": changed,
        "changed_product_paths": changed_product,
        "checks": checks,
    }, ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
