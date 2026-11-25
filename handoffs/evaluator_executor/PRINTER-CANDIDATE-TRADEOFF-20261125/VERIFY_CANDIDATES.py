"""Frozen normal-entry hard-constraint probes with explicit synthetic fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))
from shopping_decision import cognition_comparison as cog
from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message

HP = "HP M232dw"
BROTHER = "Brother HL-L1238W"


def main():
    state = new_dialogue()
    for field, answer in (
        ("category", "打印机"), ("usage", "低频家庭打印"),
        ("needs_color", "是"), ("accepts_outsourced_color", "否"),
        ("monthly_pages_range", "0-50"), ("budget_max_cny", "1000"),
        ("device_deployment_region", "中国大陆河南省"),
        ("wechat_required", "偏好"), ("requires_scan", "是"),
    ):
        state = submit_message(state, field, answer)
    pack = cog.load_pack()
    if pack is None:
        raise SystemExit("本机材料包缺失")
    results = {}
    for name, color_values in (
        ("one_excluded", ((HP, False), (BROTHER, True))),
        ("both_excluded", ((HP, False), (BROTHER, False))),
    ):
        fixture = deepcopy(pack)
        for index, (model, value) in enumerate(color_values):
            source = deepcopy(pack["sources"][0])
            sid = "synthetic-color-" + str(index)
            source.update(id=sid, url="https://probe.invalid/color-" + str(index),
                          scope_models=[model])
            fact = deepcopy(pack["facts"][0])
            fact.update(id=sid, candidate_id=model, source_id=sid, dimension="color_print",
                        value=value, kind="synthetic_probe", scope_models=[model],
                        statement="合成控制实验，仅用于硬约束传播")
            fixture["sources"].append(source)
            fixture["facts"].append(fact)
        with patch.object(cog, "load_pack", return_value=fixture):
            view = render_chat(deepcopy(state))
        audit = json.loads(view["report_json"])
        comparison = audit.get("cognition_comparison") or {}
        public = comparison.get("public") or {}
        results[name] = {
            "candidate_states": {row["candidate_id"]: row["research_status"]
                                 for row in public.get("assessments", [])},
            "text": view["result_text"],
            "prompt": view["prompt"],
            "flags": {key: audit[key] for key in (
                "purchase_recommendation_approved", "transactions_enabled", "live_price_verified")},
        }
    checks = {
        "known_hard_failure_excludes_candidate": (
            results["one_excluded"]["candidate_states"].get(HP) == "excluded_for_research"),
        "all_failed_candidates_excluded": all(
            results["both_excluded"]["candidate_states"].get(model) == "excluded_for_research"
            for model in (HP, BROTHER)),
        "no_priority_for_known_failed_candidate": (
            "HP M232dw在该维度有依据，可优先核查" not in results["one_excluded"]["text"]),
        "no_requery_for_already_known_color_failure": (
            "下一项高价值核查：准确型号能否彩印" not in results["both_excluded"]["text"]),
        "no_purchase_or_price_upgrade": all(
            flag is False for case in results.values() for flag in case["flags"].values()),
    }
    print(json.dumps({"basis": "synthetic intervention only", "checks": checks, "cases": results},
                     ensure_ascii=False, indent=2))
    return int(not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
