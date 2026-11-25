"""Replay the Zhoukou case and neighboring inputs through normal chat."""

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


def main():
    frozen = runpy.run_path(str(TASK.parent / "PRINTER-CHAT-CONTEXT-20261124" /
                               "VERIFY_ORIGINAL_CASE.py"))
    original = json.loads(frozen["INPUT"].read_text(encoding="utf-8"))
    owner_path = (TASK.parent / "PRINTER-HOUSEHOLD-NEXT-ACTION-20261124" /
                  "evidence" / "executor" / "owner-input.json")
    owner = json.loads(owner_path.read_text(encoding="utf-8"))
    state = new_dialogue()
    for field, value in original["answers"].items():
        state = submit_message(state, field, frozen["answer_text"](value))
    state["research_context"] = original["research_context"]

    def change(base, field, answer):
        return submit_message(deepcopy(base), field, answer)

    owner_city = change(
        state, "batch", "wechat_workflow：小程序\n"
        f"delivery_region：{owner['delivery_city_for_check']}\n"
        "budget_scope：仅主机硬件",
    )
    example = change(owner_city, "delivery_region", owner["optional_test_district"])
    cases = {
        "owner_city": owner_city,
        "transfer": change(owner_city, "wechat_workflow", "转App"),
        "no_setup": change(owner_city, "accepts_initial_setup", "不接受"),
        "optional_wechat": change(owner_city, "wechat_required", "偏好"),
        "example_only": example,
        "ambiguous_region": change(owner_city, "delivery_region", "河南省周口市，未确认区"),
        "withdraw_region": change(example, "delivery_region", "暂不确定"),
        "withdraw_scope": change(example, "budget_scope", "暂不确定"),
        "phone": change(example, "category", "手机"),
    }
    results = {}
    with patch.dict(os.environ, {"SHOPPING_PRINTER_REVIEWED_EVIDENCE": "1"}):
        for name, case in cases.items():
            view = render_chat(case)
            audit = json.loads(view["report_json"])
            results[name] = {
                "text": view["result_text"],
                "prompt_field": view["prompt_field"],
                "confirmed_fields": audit["confirmed_fields"],
                "preflight": audit["purchase_checks"],
                "public_decision": audit["public_decision"],
                "flags": {key: audit[key] for key in (
                    "purchase_recommendation_approved", "transactions_enabled", "live_price_verified",
                )},
            }

    preflight = {key: row["preflight"] for key, row in results.items()}
    transfer = preflight["transfer"]
    no_setup = preflight["no_setup"]
    checks = {
        "owner_conditions_follow_previous_input": (
            preflight["owner_city"]["quote_missing"] == ["delivery_region"]
            and preflight["owner_city"]["wechat_step"] == "verify_miniprogram"
            and preflight["owner_city"]["budget_max_cny"] == 1000
            and preflight["owner_city"]["budget_scope"] == "hardware_only"
        ),
        "transfer_actions_follow_current_answer": (
            transfer["wechat_step"] == "verify_transfer"
            and len(transfer["candidates"]) == 2
            and all("App" in item["next_step"] and "转" in item["next_step"]
                    and "小程序" not in item["next_step"] and "隔次微信发起" not in item["next_step"]
                    for item in transfer["candidates"])
            and "隔次微信发起" not in results["transfer"]["text"]
        ),
        "rejected_setup_actions_stay_pending": (
            no_setup["wechat_step"] == "verify_no_setup"
            and len(no_setup["candidates"]) == 2
            and all("免" in item["next_step"] and "首次" in item["next_step"]
                    and "隔次微信发起" not in item["next_step"]
                    for item in no_setup["candidates"])
            and "隔次微信发起" not in results["no_setup"]["text"]
        ),
        "wechat_preference_allows_other_checks": (
            preflight["optional_wechat"]["wechat_step"] == "continue_comparison"
            and all("耗材" in item["next_step"] or "墨粉" in item["next_step"]
                    for item in preflight["optional_wechat"]["candidates"])
        ),
        "ambiguous_district_stays_missing": (
            "delivery_region" in preflight["ambiguous_region"]["quote_missing"]
            and preflight["ambiguous_region"]["quote_status"] == "prerequisites_missing"
        ),
        "explicit_district_is_only_ready_to_check": (
            preflight["example_only"]["quote_status"] == "awaiting_authoritative_quote"
            and preflight["example_only"]["payable_cny"] is None
        ),
        "withdrawals_restore_pending_and_category_clears_card": (
            "delivery_region" in preflight["withdraw_region"]["quote_missing"]
            and "budget_scope" in preflight["withdraw_scope"]["quote_missing"]
            and preflight["phone"] is None and "HL-L1238W" not in results["phone"]["text"]
        ),
        "no_legacy_wechat_or_purchase_or_price_upgrade": (
            all(row["public_decision"] is None for row in results.values())
            and all(flag is False for row in results.values() for flag in row["flags"].values())
            and all(row is None or row["payable_cny"] is None for row in preflight.values())
        ),
    }
    print(json.dumps({"checks": checks, "cases": results}, ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
