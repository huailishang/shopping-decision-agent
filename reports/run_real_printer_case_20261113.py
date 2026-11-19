"""H08原案+4个明确标模拟的关键改答：正常CLI子进程回放，结果路径必须新建。"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (ROOT / "reports").resolve()

# H08真人原案及既有真人补答；无扫描、地区、微信具体流程、费用范围的假定。
BASE = {
    "category": "printer", "usage": "家用",
    "budget_max_cny": 1000, "monthly_pages_range": [0, 50],
    "needs_color": False, "accepts_outsourced_color": True,
    "wechat_required": True
}
TURNS = [
    {"text": "H08原案与既有补答结构化回放（非本轮真人再确认）", "answers": BASE},
    {"text": "技术变体验证：假设要求自动双面（非用户新确认）",
     "answers": {"requires_auto_duplex": True}},
    {"text": "技术变体验证：假设家中要彩色（非用户新确认）",
     "answers": {"needs_color": True}},
    {"text": "技术变体验证：假设不强求微信打印（非用户新确认）",
     "answers": {"wechat_required": False}},
    {"text": "技术变体验证：假设必须扫描（非用户新确认）",
     "answers": {"requires_scan": True}},
]
EXPECTED = [
    {"CASE-01", "CASE-02", "CASE-03"},
    {"CASE-01", "CASE-02", "CASE-03", "CASE-05"},
    {"CASE-02", "CASE-03", "CASE-05"},
    {"CASE-03", "CASE-05"},
    {"CASE-03", "CASE-04", "CASE-05"},
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path,
                        help="必须是reports下尚不存在的JSON文件，禁止覆盖历史证据")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.parent != REPORT_DIR or output.suffix != ".json" or output.exists():
        parser.error("output must be a new .json directly under reports/")
    command = [sys.executable, "-m", "shopping_decision.dialogue_flow", "--real-printer-case"]
    proc = subprocess.run(command, cwd=ROOT,
                          input="".join(json.dumps(x, ensure_ascii=False) + "\n" for x in TURNS),
                          text=True, capture_output=True, encoding="utf-8", timeout=90)
    if proc.returncode:
        print(proc.stderr, file=sys.stderr)
        return proc.returncode
    outputs = [json.loads(x) for x in proc.stdout.splitlines()]
    if len(outputs) != len(TURNS) + 1:
        print("unexpected number of CLI outputs", file=sys.stderr)
        return 1
    checks = []
    for i, out in enumerate(outputs[1:]):
        research = out.get("real_printer_case_research", {})
        actual = {x["id"] for x in research.get("reasons", [])}
        safe = (research.get("real_sale_identity_verified_count") == 0
                and research.get("regional_live_quote_count") == 0
                and research.get("purchase_recommendation_approved") is False
                and research.get("transactions_enabled") is False
                and out.get("comparison", {}).get("purchase_recommendation_approved") is False)
        correct = actual == EXPECTED[i] and safe and out["version"] == i + 1
        checks.append({"round": i + 1, "expected_reason_ids": sorted(EXPECTED[i]),
                       "actual_reason_ids": sorted(actual), "safe": safe, "pass": correct,
                       "kind": "recorded_original_replay" if i == 0 else "synthetic_change_only"})
    result = {
        "case_id": "REAL-PRINTER-H08B-20261113",
        "role": "executor", "test_kind": "real_CLI_subprocess_with_offline_research_not_live_SKU",
        "original_provenance": "H08 recorded real user requirements, no new actual confirmation",
        "scenario_change_provenance": "synthetic only; no real user confirmation",
        "command": command,
        "turns": TURNS, "checks": checks,
        "passed": sum(x["pass"] for x in checks), "total": len(checks),
        "outputs": outputs[1:],
        "real_sale_identity_verified": 0, "regional_quotes_verified": 0,
        "purchase_recommendation_approved": False, "transactions_enabled": False,
    }
    with output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"passed": result["passed"], "total": result["total"],
                      "file": str(args.output), "failures": [
                          x["round"] for x in checks if not x["pass"]]}, ensure_ascii=False))
    return 0 if all(x["pass"] for x in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
