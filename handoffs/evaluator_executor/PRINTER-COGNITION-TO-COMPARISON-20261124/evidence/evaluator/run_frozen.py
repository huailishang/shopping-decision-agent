"""Independent execution of the frozen commands with raw receipts."""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def main():
    commands = json.loads((HERE / "frozen-commands.json").read_text(encoding="utf-8"))
    results = []
    for check in commands:
        name = check["id"]
        start = datetime.now(timezone.utc).isoformat()
        tick = time.monotonic()
        run = subprocess.run(check["command"], cwd=ROOT, capture_output=True)
        (HERE / (name + ".stdout.txt")).write_bytes(run.stdout)
        (HERE / (name + ".stderr.txt")).write_bytes(run.stderr)
        result = {"id": name, "command": check["command"], "started_at": start,
                  "elapsed_seconds": round(time.monotonic() - tick, 3),
                  "exit_code": run.returncode}
        results.append(result)
        (HERE / "exit-summary.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result), flush=True)
    return int(any(row["exit_code"] for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
