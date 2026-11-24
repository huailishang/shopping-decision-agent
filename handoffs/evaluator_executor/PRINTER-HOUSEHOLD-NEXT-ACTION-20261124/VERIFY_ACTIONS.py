"""Replay the case through ordinary local chat and verify next actions."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import runpy
import sys
from unittest.mock import patch


TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))

from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message


def replay():
    prior = runpy.run_path(str(TASK.parent / "PRINTER-CHAT-CONTEXT-20261124" /
                               "VERIFY_ORIGINAL_CASE.py"))
    original = json.loads(prior["INPUT"].read_text(encoding="utf-8"))
    state = new_dialogue()
    for field, value in original["answers"].items():
        state = submit_message(state, field, prior["answer_text"](value))
    state["research_context"] = original["research_context"]

    def change(base, field, answer):
        return submit_message(deepcopy(base), field, answer)

    mini = change(state, "wechat_workflow", "小程序")
    district = change(mini, "delivery_region", "河南省郑州市金水区")
    full = change(district, "budget_scope", "主机含运费及必要支出")
    scenarios = {
        "original": state,
        "mini": mini,
        "transfer": change(mini, "wechat_workflow", "转App"),
        "optional": change(mini, "wechat_required", "不是必须"),
        "setup_rejected": change(mini, "accepts_initial_setup", "不接受"),
        "province_only": change(mini, "delivery_region", "河南省"),
        "district": district,
        "quote_ready": full,
        "withdraw_district": change(full, "delivery_region", "暂不确定"),
        "new_budget": change(full, "budget_max_cny", "800"),
        "switch_category": change(full, "category", "手机"),
    }
    results = {}
    with patch.dict(os.environ, {"SHOPPING_PRINTER_REVIEWED_EVIDENCE": "1"}):
        for name, case in scenarios.items():
            view = render_chat(deepcopy(case))
            report = json.loads(view["report_json"])
            results[name] = {"text": view["result_text"],
                             "preflight": report.get("purchase_checks"),
                             "public": report["public_decision"],
                             "flags": {k: report[k] for k in (
                                 "purchase_recommendation_approved",
                                 "transactions_enabled", "live_price_verified")}}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    runs = replay()
    scenarios = {name: value["preflight"] or {} for name, value in runs.items()}
    if args.baseline:
        checks = {"original_has_no_action_packet": not scenarios["original"],
                  "legacy_mini_has_a_positive_claim": any(
                      c["status"] == "met" and c["dimension"] == "wechat_miniprogram"
                      for c in (runs["mini"]["public"] or {}).get("claims", []))}
    else:
        checks = {
            "clear_original_steps": scenarios["original"].get("wechat_step") == "choose_path"
            and all(model in runs["original"]["text"] for model in ("Brother HL-L1238W", "HP M232dw")),
            "decisions_follow_current_choice":
                scenarios["mini"].get("wechat_step") == "verify_miniprogram"
                and scenarios["transfer"].get("wechat_step") == "verify_transfer"
                and scenarios["optional"].get("wechat_step") == "continue_comparison"
                and scenarios["setup_rejected"].get("wechat_step") == "verify_no_setup",
            "quote_dependencies_follow_answers":
                scenarios["original"].get("quote_missing") == ["delivery_region", "budget_scope"]
                and scenarios["province_only"].get("quote_missing") == ["delivery_region", "budget_scope"]
                and scenarios["district"].get("quote_missing") == ["budget_scope"]
                and scenarios["quote_ready"].get("quote_status") == "awaiting_authoritative_quote"
                and scenarios["withdraw_district"].get("quote_missing") == ["delivery_region"],
            "quoted_total_stays_unverified_and_budget_updates":
                scenarios["quote_ready"].get("payable_cny") is None
                and "800元" in runs["new_budget"]["text"] and "1000元" not in runs["new_budget"]["text"],
            "v1_not_promoted": not any(c["status"] == "met" and
                any(s["source_id"] == "brother-cn-manual" for s in c["source_audit"])
                for view in runs.values() for c in (view["public"] or {}).get("claims", [])),
            "no_card_after_category_switch": not scenarios["switch_category"]
                and "Brother HL-L1238W" not in runs["switch_category"]["text"],
            "all_transaction_flags_false": all(
                flag is False for view in runs.values() for flag in view["flags"].values()),
        }
    print(json.dumps({"checks": checks, "cases": runs}, ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
