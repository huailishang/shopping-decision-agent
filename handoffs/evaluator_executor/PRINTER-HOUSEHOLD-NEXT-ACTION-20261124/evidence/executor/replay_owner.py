"""Replay the owner's newly supplied conditions and a separate county example."""

from copy import deepcopy
import json
from pathlib import Path
import runpy
import sys


EVIDENCE = Path(__file__).resolve().parent
TASK = EVIDENCE.parents[1]
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))

from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message


def main():
    baseline = runpy.run_path(str(TASK.parent / "PRINTER-CHAT-CONTEXT-20261124" /
                                  "VERIFY_ORIGINAL_CASE.py"))
    original = json.loads(baseline["INPUT"].read_text(encoding="utf-8"))
    owner = json.loads((EVIDENCE / "owner-input.json").read_text(encoding="utf-8"))
    state = new_dialogue()
    for field, value in original["answers"].items():
        state = submit_message(state, field, baseline["answer_text"](value))
    state["research_context"] = original["research_context"]
    state = submit_message(state, "batch", "wechat_workflow：小程序\n"
                           f"delivery_region：{owner['delivery_city_for_check']}\n"
                           "budget_scope：仅主机硬件")
    sample = submit_message(deepcopy(state), "delivery_region", owner["optional_test_district"])
    results = {}
    for label, current in (("owner_city", state), ("example_county_only", sample)):
        view = render_chat(current)
        audit = json.loads(view["report_json"])
        results[label] = {"text": view["result_text"], "fields": audit["confirmed_fields"],
                          "next_prompt": view["prompt_field"], "checks": audit["purchase_checks"],
                          "price_verified": audit["live_price_verified"]}
    assert results["owner_city"]["checks"]["quote_missing"] == ["delivery_region"]
    assert results["example_county_only"]["checks"]["quote_status"] == "awaiting_authoritative_quote"
    assert all(row["price_verified"] is False for row in results.values())
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
