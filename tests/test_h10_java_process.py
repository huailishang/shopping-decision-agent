"""H10: real Java ProcessBuilder subprocess regressions, not Python capture_output alone."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "JDK required")
class H10JavaProcessTests(unittest.TestCase):
    def test_java_bridge_and_stale_result(self):
        with tempfile.TemporaryDirectory(prefix="h10_javac_") as classes:
            compile_command = ["javac", "-encoding", "UTF-8", "-d", classes,
                str(ROOT / "desktop" / "DesktopBridgeClient.java"),
                str(ROOT / "desktop" / "H10JavaRegression.java")]
            result = subprocess.run(compile_command, cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(["java", "-cp", classes, "H10JavaRegression", sys.executable],
                cwd=ROOT, capture_output=True, text=True, timeout=35)
            self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
            self.assertIn("H10 Java subprocess regression: 6/6 PASS", result.stdout)
