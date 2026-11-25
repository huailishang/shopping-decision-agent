"""Capture normal chat output for the frozen business cases, for human review."""

from copy import deepcopy
import json
from pathlib import Path
import runpy
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))

from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message


def main():
    prior = runpy.run_path(str(TASK.parent / "PRINTER-CHAT-CONTEXT-20261124" /
                               "VERIFY_ORIGINAL_CASE.py"))
    original = json.loads(prior["INPUT"].read_text(encoding="utf-8"))
    base = new_dialogue()
    for field, value in original["answers"].items():
        base = submit_message(base, field, prior["answer_text"](value))
    base = submit_message(base, "batch", "wechat_workflow：小程序\n"
                          "delivery_region：河南省周口市\nbudget_scope：仅主机硬件")
    cases = json.loads((TASK / "CASES.json").read_text(encoding="utf-8"))["cases"]
    output = []
    for case in cases:
        state = deepcopy(base)
        if case["research_context"]:
            state["research_context"] = deepcopy(original["research_context"])
        for field, answer in case["changes"].items():
            state = submit_message(state, field, answer)
        view = render_chat(state)
        report = json.loads(view["report_json"])
        assert all(report[key] is False for key in (
            "purchase_recommendation_approved", "transactions_enabled", "live_price_verified"))
        output.append({
            "case_id": case["id"], "expected_human_review": case["expected"],
            "confirmed_fields": report["confirmed_fields"],
            "prompt_field": view["prompt_field"], "result_text": view["result_text"],
            "report": report,
        })
    print(json.dumps({"purpose": "原始入口记录，退出0仅代表重放和安全断言通过；业务效果逐案人审",
                      "cases": output}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
