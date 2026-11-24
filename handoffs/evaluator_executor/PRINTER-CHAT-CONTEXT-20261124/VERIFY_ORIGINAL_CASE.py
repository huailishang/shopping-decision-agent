"""Replay the historical printer request against the normal local chat backend."""

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message


INPUT = ROOT / ("handoffs/evaluator_executor/PRINTER-WECHAT-DECISION-FACT-20261117"
                "/preparation/confirmed_need.input.jsonl")
FLAGS = ("purchase_recommendation_approved", "transactions_enabled", "live_price_verified")


def answer_text(value):
    if type(value) is bool:
        return "是" if value else "否"
    if isinstance(value, list):
        return "-".join(map(str, value))
    return "暂不确定" if value == "unknown" else str(value)


def main():
    original = json.loads(INPUT.read_text(encoding="utf-8"))
    state = new_dialogue()
    for key, value in original["answers"].items():
        state = submit_message(state, key, answer_text(value))
    state["research_context"] = original["research_context"]
    optional = submit_message(state, "wechat_required", "不是必须")
    revised = submit_message(optional, "budget_max_cny", "800")
    stages = {"original": state, "optional": optional, "revised_budget": revised}

    results = {}
    for name, state in stages.items():
        rendered = render_chat(state)
        audit = json.loads(rendered["report_json"])
        results[name] = {
            "status": rendered["status"],
            "next_question": rendered["prompt_field"],
            "result_text": rendered["result_text"],
            "confirmed_fields": audit["confirmed_fields"],
            "public_decision": audit["public_decision"],
            "flags": {key: audit[key] for key in FLAGS},
        }
    first = results["original"]
    checks = {
        "original_constraints": first["confirmed_fields"] == {
            key: value for key, value in original["answers"].items() if value != "unknown"
        },
        "original_unanswered": all(
            key not in first["confirmed_fields"] for key in ("delivery_region", "budget_scope", "wechat_workflow")
        ),
        "original_research": all(
            text in first["result_text"] for text in ("待核研究", "2条待核研究记录", "1000元", "必须条件")
        ),
        "optional_path": "可选条件" in results["optional"]["result_text"]
            and "必须条件" not in results["optional"]["result_text"],
        "new_budget_only": "800元" in results["revised_budget"]["result_text"]
            and "1000元" not in results["revised_budget"]["result_text"],
        "no_qualified_purchase_claim": all(
            result["status"] == "defer" and result["public_decision"] is None
            and all(value is False for value in result["flags"].values())
            for result in results.values()),
    }
    print(json.dumps({"checks": checks, "results": results}, ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    sys.exit(main())
