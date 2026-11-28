"""Owner-directed compatibility regression: preserve historical verdict and exact bytes."""
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import audit_model_history_readonly as audit

TASK = audit.ROOT / "handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118"


class HistoryAuditVersionTransition(unittest.TestCase):
    def test_current_transition_preserves_historical_failure(self):
        result = audit.audit_history(TASK)
        self.assertEqual(result["scheduled"], 6)
        self.assertEqual(result["completed"], 6)
        self.assertEqual(result["accepted_model_outputs"], 0)
        self.assertEqual(result["not_attempted_cases"], ["C05", "C06", "C07"])
        self.assertEqual(result["parent_vp04_status"], "REJECTED_not_retroactively_repaired")
        self.assertFalse(result["old_evidence_modified"])
        self.assertTrue(set(audit.WORKSHEET_APPROVED_SOURCE_SHA256).issubset(
            result["allowed_current_source_drift"]))

    def test_old_bytes_are_independently_pinned(self):
        manifest = audit.load(TASK / "FROZEN_INPUTS.json")
        for name, expected in audit.WORKSHEET_APPROVED_SOURCE_SHA256.items():
            with self.subTest(name=name):
                old = subprocess.check_output(
                    ["git", "show", audit.WORKSHEET_PRE_TASK_COMMIT + ":" + name],
                    cwd=audit.ROOT)
                self.assertEqual(audit.sha(old), manifest["files"][name])
                self.assertEqual(audit.sha((audit.ROOT / name).read_bytes()), expected)

    def _changed_bytes(self, name, reason):
        read = Path.read_bytes
        target = (audit.ROOT / name).resolve()
        def changed(path):
            data = read(path)
            return data + b"\n# simulated unauthorized change" if path.resolve() == target else data
        with patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(ValueError, reason):
                audit.audit_history(TASK)

    def test_unapproved_current_java_change_rejected(self):
        for name in audit.WORKSHEET_APPROVED_SOURCE_SHA256:
            with self.subTest(name=name):
                self._changed_bytes(name, "worksheet_current_source_sha_mismatch:" + name)

    def test_missing_current_java_rejected(self):
        is_file = Path.is_file
        for name in audit.WORKSHEET_APPROVED_SOURCE_SHA256:
            with self.subTest(name=name):
                target = (audit.ROOT / name).resolve()
                with patch.object(Path, "is_file", lambda p: p.resolve() != target and is_file(p)):
                    with self.assertRaisesRegex(ValueError, "worksheet_current_source_sha_mismatch:" + name):
                        audit.audit_history(TASK)

    def test_wrong_historical_snapshot_rejected(self):
        run = subprocess.check_output
        for name in audit.WORKSHEET_APPROVED_SOURCE_SHA256:
            with self.subTest(name=name):
                def wrong(argv, *args, **kwargs):
                    if argv == ["git", "show", audit.WORKSHEET_PRE_TASK_COMMIT + ":" + name]:
                        return b"wrong historical bytes"
                    return run(argv, *args, **kwargs)
                with patch.object(subprocess, "check_output", wrong):
                    with self.assertRaisesRegex(ValueError, "worksheet_historical_source_sha_mismatch:" + name):
                        audit.audit_history(TASK)

    def test_missing_historical_snapshot_rejected(self):
        run = subprocess.check_output
        name = next(iter(audit.WORKSHEET_APPROVED_SOURCE_SHA256))
        def missing(argv, *args, **kwargs):
            if argv == ["git", "show", audit.WORKSHEET_PRE_TASK_COMMIT + ":" + name]:
                raise subprocess.CalledProcessError(128, argv)
            return run(argv, *args, **kwargs)
        with patch.object(subprocess, "check_output", missing):
            with self.assertRaisesRegex(ValueError, "worksheet_historical_source_unavailable:" + name):
                audit.audit_history(TASK)

    def test_ledger_append_rejected(self):
        ledger = (TASK / "evidence/live/attempts.jsonl").read_bytes()
        with self.assertRaisesRegex(ValueError, "historical_ledger_sha_mismatch"):
            audit.audit_history(TASK, ledger_bytes_override=ledger + b"\n")

    def test_frozen_manifest_change_rejected(self):
        self._changed_bytes((TASK / "FROZEN_INPUTS.json").relative_to(audit.ROOT),
                            "historical_frozen_manifest_sha_mismatch")

    def test_previous_reviewed_test_change_rejected(self):
        name = next(iter(audit.REVIEWED_R1_TEST_SHA256))
        self._changed_bytes(name, "approved_r1_test_sha_mismatch:" + name)

    def test_unrelated_historical_source_change_rejected(self):
        self._changed_bytes("AGENTS.md", "unapproved_historical_file_drift:AGENTS.md")
