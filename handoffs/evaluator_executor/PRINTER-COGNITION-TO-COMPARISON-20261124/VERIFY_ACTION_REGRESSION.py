"""Retain prior action checks while allowing newly reviewed facts to be public."""

import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]


def main():
    old = TASK.parent / "PRINTER-HOUSEHOLD-DECISION-CHECK-20261124" / "VERIFY_ENTRY.py"
    replay = subprocess.run([sys.executable, "-X", "utf8", str(old)],
                            cwd=ROOT, capture_output=True)
    if not replay.stdout:
        sys.stderr.buffer.write(replay.stderr)
        return 1
    data = json.loads(replay.stdout)
    checks = dict(data["checks"])
    # The old aggregate requires every public_decision to be None. The new
    # contract permits supported research claims. Preserve its safety part.
    del checks["no_legacy_wechat_or_purchase_or_price_upgrade"]
    checks["no_price_or_transaction_upgrade"] = all(
        flag is False for case in data["cases"].values() for flag in case["flags"].values())
    print(json.dumps({"checks": checks, "cases": data["cases"],
                      "legacy_replay_exit": replay.returncode},
                     ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
