"""2026-11-14 评估者新变体：只读、无真实商品、无密钥或外部调用。
用排他新建的JSON保存独立检查结果，避免覆盖历史执行者/评估者证据。
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from shopping_decision.real_printer_case import compare_case_research, RESEARCH_PATH
from shopping_decision.sale_configuration_evidence import assess_sale_evidence_report
from tests.test_p0_9_b_evidence import MODELS, report, sample

NOW = datetime.now(timezone.utc)
GOOD = sample(NOW)
checks: list[dict] = []

def check(name: str, condition: bool, actual: object, expected: str) -> None:
    checks.append({"id": name, "pass": bool(condition), "actual": actual, "expected": expected})

def run_sale(*rows, models=MODELS):
    return assess_sale_evidence_report(report(*rows), now=NOW, known_models=models)

def altered(**kwargs):
    v = deepcopy(GOOD)
    v.update(kwargs)
    return v

# 新的时区超界变体与行隔离：不复用执行者所测的-00:01。
bad_early = altered(observed_at="0001-01-01T00:00:00+02:00")
a = run_sale(bad_early, GOOD)
check("N01_min_year_utc_underflow", a["accepted_rows"] == 1 and
      a["rejected_count"] == 1 and a["rejected"][0]["reason"] == "source_observation_invalid",
      (a["accepted_rows"], a["rejected_count"], a["rejected"][0]["reason"]), "1 good + 1 bad observation")

bad_max = altered(review_status="withdrawn",
                  review_valid_until="9999-12-31T23:59:59-05:00")
a = run_sale(GOOD, bad_max)
check("N02_max_year_bad_withdrawal", a["accepted_rows"] == 1 and
      a["configurations"][0]["status"] == "synthetic_field_binding_test_only",
      (a["accepted_rows"], a["configurations"][0]["status"]), "bad event cannot revoke good")

a = run_sale(bad_max, GOOD)
check("N03_max_year_swapped_order", a["accepted_rows"] == 1 and
      a["configurations"][0]["status"] == "synthetic_field_binding_test_only",
      (a["accepted_rows"], a["configurations"][0]["status"]), "order independent good row")

bad_lost = altered(permitted_uses=["local_parse"], review_valid_until="9999-12-31T23:59:59-05:00")
a = run_sale(bad_lost, GOOD)
check("N04_max_year_bad_use_loss", a["accepted_rows"] == 1 and
      a["configurations"][0]["status"] == "synthetic_field_binding_test_only",
      (a["accepted_rows"], a["configurations"][0]["status"]), "invalid use loss no revoke")

valid_edge = altered(review_valid_until="9999-12-31T23:59:59+05:00")
a = run_sale(valid_edge)
check("N05_high_year_legal_neighbor", a["accepted_rows"] == 1 and
      a["configurations"][0]["review_valid_until"] == "9999-12-31T18:59:59+00:00",
      (a["accepted_rows"], a["configurations"][0]["review_valid_until"]), "valid extreme UTC neighbor")

different_item = altered(platform_item_id="987654321", review_status="withdrawn")
a = run_sale(GOOD, different_item)
check("N06_other_item_cannot_revoke", a["accepted_rows"] == 1 and
      a["configurations"][0]["status"] == "synthetic_field_binding_test_only",
      (a["accepted_rows"], a["configurations"][0]["status"]), "different item isolated")

# 两个真实品牌的样本接口是否都能表达：探测而不修改代码。
hp = altered(selected_model_id="M232dw", title_models=["M232dw"], spec_models=["M232dw"])
a = run_sale(hp, models=set(MODELS) | {"M232dw"})
check("N07_hp_model_gap_documented", a["accepted_rows"] == 0 and
      a["rejected"][0]["reason"] == "manufacturer_model_not_reviewed",
      (a["accepted_rows"], a["rejected"][0]["reason"]), "current gate does NOT support HP model syntax")

# 研究资料绝不允许靠输入本身改变审查状态或引入虚构来源。
baseline = {
    "category": "printer", "usage": "家用", "budget_max_cny": 1000,
    "monthly_pages_range": [0, 50], "needs_color": False,
    "accepts_outsourced_color": True, "wechat_required": True
}
view = compare_case_research(baseline)
check("N08_original_research_not_purchase", set(r["id"] for r in view["reasons"]) ==
      {"CASE-01", "CASE-02", "CASE-03"} and
      view["purchase_recommendation_approved"] is False and
      view["real_sale_identity_verified_count"] == 0,
      [r["id"] for r in view["reasons"]], "three conditional research reasons, no purchase")

view = compare_case_research({**baseline, "category": "phone"})
check("N09_other_category_no_printer_reason", view["reason_count"] == 0,
      view["reason_count"], "no printer research outside printer")

with TemporaryDirectory() as d:
    path = Path(d) / "mutated.json"
    data = json.loads(RESEARCH_PATH.read_text(encoding="utf-8"))
    data["claims"][1]["support_ids"] = ["R404_UNVERIFIED"]
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    caught = ""
    try:
        compare_case_research(baseline, path=path)
    except ValueError as exc:
        caught = str(exc)
    check("N10_unmapped_source_refused", caught == "unmapped_research_source",
          caught, "unmapped_research_source")

# 真实子进程：补做撤销、恢复、清空和跨品类，均不使用内部catalog_override。
turns = [
    {"text": "已知原案的离线回放，不是本轮真人新确认", "answers": baseline},
    {"text": "模拟同时要求扫描与自动双面", "answers": {
        "requires_scan": True, "requires_auto_duplex": True}},
    {"text": "模拟撤销扫描与双面", "answers": {
        "requires_scan": None, "requires_auto_duplex": None}},
    {"text": "模拟改为在家彩印", "answers": {"needs_color": True}},
    {"text": "模拟恢复黑白且允许外包彩印", "answers": {
        "needs_color": False, "accepts_outsourced_color": True}},
    {"text": "模拟撤销页数和微信条件", "answers": {
        "monthly_pages_range": None, "wechat_required": None}},
    {"text": "模拟更换到手机品类", "answers": {"category": "phone"}},
    {"text": "伪造购买批准必须拒绝", "answers": {"purchase_recommendation_approved": True}},
]
proc = subprocess.run([sys.executable, "-m", "shopping_decision.dialogue_flow", "--real-printer-case"],
    input="".join(json.dumps(x, ensure_ascii=False) + "\n" for x in turns),
    text=True, capture_output=True, encoding="utf-8", timeout=90)
out = [json.loads(x) for x in proc.stdout.splitlines()] if proc.returncode == 0 else []
check("N11_cli_exits_and_row_count", proc.returncode == 0 and len(out) == len(turns)+1,
      {"returncode": proc.returncode, "rows": len(out)}, "zero exit, ready+8 turns")
if len(out) == len(turns)+1:
    ids = lambda i: {x["id"] for x in out[i]["real_printer_case_research"]["reasons"]}
    check("N12_scan_and_duplex_recompute", {"CASE-04","CASE-05"}.issubset(ids(2)),
          sorted(ids(2)), "both conditional reasons added")
    check("N13_clear_scan_and_duplex", "CASE-04" not in ids(3) and "CASE-05" not in ids(3),
          sorted(ids(3)), "cleared reasons removed")
    check("N14_color_change_and_restore", "CASE-01" not in ids(4) and "CASE-01" in ids(5),
          [sorted(ids(4)), sorted(ids(5))], "color change removes and reset restores")
    check("N15_clear_page_range_and_wechat", "CASE-02" not in ids(6) and "CASE-03" not in ids(6),
          sorted(ids(6)), "cleared conditions remove dependent research")
    check("N16_category_change_no_leak", len(ids(7)) == 0,
          sorted(ids(7)), "none for phone")
    check("N17_forged_approval_invalid_turn", out[8].get("status") == "invalid_turn",
          out[8].get("status"), "invalid_turn")
    check("N18_all_valid_turns_safe", all(
          out[i]["real_printer_case_research"]["transactions_enabled"] is False and
          out[i]["real_printer_case_research"]["purchase_recommendation_approved"] is False
          for i in range(1,8)), "all7_checked", "zero purchase or transaction authority")

result = {"role": "independent_evaluator", "run_at_utc": NOW.isoformat(),
          "source": "local_worktree_current_uncommitted",
          "scope": "synthetic_contract_and_research_cli_only_no_business_api",
          "tests": checks, "total": len(checks),
          "passed": sum(c["pass"] for c in checks),
          "failed": [c["id"] for c in checks if not c["pass"]]}
if len(sys.argv) != 3 or sys.argv[1] != "--output":
    raise SystemExit("usage: python3 reports/independent_real_printer_20261114.py --output NEW_FILE.json")
path = Path(sys.argv[2])
with path.open("x", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(json.dumps({"total": result["total"], "passed": result["passed"], "failed": result["failed"],
                  "output": str(path)}, ensure_ascii=False))
raise SystemExit(0 if not result["failed"] else 1)
