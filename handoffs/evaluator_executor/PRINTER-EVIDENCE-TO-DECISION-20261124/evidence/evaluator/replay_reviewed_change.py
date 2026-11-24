"""Check a workflow correction followed by loss of locally reviewed evidence."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sys
from unittest.mock import patch


TASK = Path(__file__).resolve().parents[2]
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))

from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message
from shopping_decision.evidence_comparison import SAFE_FLAGS


def capture(state):
    view = render_chat(deepcopy(state))
    report = json.loads(view["report_json"])
    return {"text": view["result_text"], "public": report["public_decision"],
            "fields": report["confirmed_fields"],
            "flags": {key: report[key] for key in SAFE_FLAGS[:3]}}


def main():
    state = new_dialogue()
    for field, answer in (
        ("category", "打印机"), ("usage", "家用学习资料"),
        ("wechat_required", "必须"), ("wechat_workflow", "微信小程序直接打印"),
        ("device_deployment_region", "中国大陆河南省"), ("accepts_initial_setup", "接受"),
        ("budget_max_cny", "1000"),
    ):
        state = submit_message(state, field, answer)
    changed = submit_message(deepcopy(state), "wechat_workflow", "转App")
    with (patch.dict("os.environ", {"SHOPPING_PRINTER_REVIEWED_EVIDENCE": "1"}),
          patch("shopping_decision.chat_bridge.date", wraps=date) as clock):
        clock.today.return_value = date(2026, 11, 24)
        initial, transfer = capture(state), capture(changed)
        clock.today.return_value = date(2026, 12, 25)
        expired = capture(changed)
    initial_claims = initial["public"]["claims"] if initial["public"] else []
    transfer_claims = transfer["public"]["claims"] if transfer["public"] else []
    checks = {
        "miniprogram_document_claim_visible": any(
            c["candidate_id"] == "Brother HL-L1238W" and c["dimension"] == "wechat_miniprogram"
            and c["status"] == "met" and c["claim_id"] in initial["text"] for c in initial_claims),
        "edited_transfer_does_not_inherit_positive": any(
            c["dimension"] == "wechat_transfer_to_app" and c["status"] == "unknown"
            for c in transfer_claims)
        and all(c["dimension"] != "wechat_miniprogram" for c in transfer_claims),
        "expiry_with_edited_condition_returns_to_pending": expired["public"] is None
        and "待核研究" in expired["text"] and expired["fields"]["wechat_workflow"] == "transfer_to_app",
        "no_purchase_or_live_price": all(
            flag is False for result in (initial, transfer, expired)
            for flag in result["flags"].values()),
    }
    print(json.dumps({"checks": checks, "original": initial, "changed": transfer,
                      "expired_after_change": expired}, ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
