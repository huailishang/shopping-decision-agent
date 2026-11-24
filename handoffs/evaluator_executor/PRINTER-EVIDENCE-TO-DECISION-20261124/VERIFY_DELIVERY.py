"""Verify audit trail and replay the normal local printer chat."""

import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import runpy
import sys
from unittest.mock import patch
from urllib.parse import urlsplit


TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT))

from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message
from shopping_decision.evidence_comparison import SAFE_FLAGS


ARTIFACTS = TASK / "evidence" / "executor"
MODELS = ("Brother HL-L1238W", "HP M232dw")
SWITCH = "SHOPPING_PRINTER_REVIEWED_EVIDENCE"
PATHS = {
    "miniprogram": ("微信小程序直接打印", "wechat_miniprogram"),
    "transfer_to_app": ("文件转存厂商App", "wechat_transfer_to_app"),
}
STATES = {"documented_supported": "met", "documented_unsupported": "failed",
          "unknown": "unknown", "conflict": "conflict"}
HOSTS = ("brother.cn", "brother.com", "hp.com", "hpcloud.hp.com", "hpstore.cn")


def require(check, reason):
    if not check:
        raise ValueError(reason)


def timestamp(value):
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(moment.utcoffset() is not None, "带时区的观察时间")
    return moment


def official(url):
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and any(
        host == domain or host.endswith("." + domain) for domain in HOSTS)


def read_attempts():
    starts, finished = {}, {}
    for line in (ARTIFACTS / "attempts.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        key = row["id"]
        at = timestamp(row["at"])
        if row["event"] == "scheduled":
            require(key not in starts, "重复安排")
            kind = row["kind"]
            require((kind == "query" and row["target"])
                    or (kind == "open" and official(row["target"])), "未允许的取证对象")
            starts[key] = row
        else:
            require(row["event"] == "completed" and key in starts and key not in finished,
                    "未配对的结束回执")
            require(at >= timestamp(starts[key]["at"]), "取证时间顺序")
            require(row["status"] in {"ok", "failed", "blocked"}, "无效的回执状态")
            receipt = (ARTIFACTS / row["receipt"]).resolve()
            require(receipt.is_relative_to(ARTIFACTS) and receipt.is_file()
                    and receipt.stat().st_size > 0, "回执缺失")
            finished[key] = row | {"sha256": sha256(receipt.read_bytes()).hexdigest()}
    require(starts.keys() == finished.keys(), "未完成的取证记录")
    for kind, maximum in (("query", 8), ("open", 14)):
        require(sum(row["kind"] == kind for row in starts.values()) <= maximum, "取证超额")
    return starts, finished


def replay():
    prior = runpy.run_path(str(TASK.parent / "PRINTER-CHAT-CONTEXT-20261124" /
                               "VERIFY_ORIGINAL_CASE.py"))
    original = json.loads(prior["INPUT"].read_text(encoding="utf-8"))
    state = new_dialogue()
    for key, value in original["answers"].items():
        state = submit_message(state, key, prior["answer_text"](value))
    state["research_context"] = original["research_context"]
    states = {"original": state}
    for name, (user_answer, _) in PATHS.items():
        states[name] = submit_message(deepcopy(state), "wechat_workflow", user_answer)
    states["optional"] = submit_message(deepcopy(state), "wechat_required", "不是必须")
    states["revised_budget"] = submit_message(deepcopy(state), "budget_max_cny", "800")
    results = {}
    for mode in ("0", "1"):
        results[mode] = {}
        with patch.dict(os.environ, {SWITCH: mode}):
            for name, case in states.items():
                rendered = render_chat(deepcopy(case))
                report = json.loads(rendered["report_json"])
                public = report["public_decision"]
                require(all(report.get(key) is False for key in SAFE_FLAGS[:3]), "安全标志开")
                require(not public or all(public[key] is False for key in SAFE_FLAGS),
                        "比较安全标志开")
                results[mode][name] = {
                    "text": rendered["result_text"], "confirmed": report["confirmed_fields"],
                    "public_decision": public,
                }
    require(all(not row["public_decision"] for row in results["0"].values()),
            "关闭开关未恢复原路径")
    require(all(results["0"][k]["confirmed"] == results["1"][k]["confirmed"] for k in states),
            "前后会话条件变化")
    return results


def check_delivery(runs):
    decision = json.loads((ARTIFACTS / "decision.json").read_text(encoding="utf-8"))
    starts, finished = read_attempts()
    require(starts or decision.get("source_access_blocker"), "零尝试缺少具体原因")
    sources = decision["sources"]
    for entry in sources.values():
        attempt = entry["attempt_id"]
        require(starts[attempt]["kind"] == "open" and finished[attempt]["status"] == "ok",
                "证据没有可回查的成功打开")
        require(finished[attempt]["sha256"] == entry["receipt_sha256"], "证据回执哈希不符")
        require(official(entry["url"]) and entry["locator"] and entry["limitations"],
                "证据定位或限制缺失")
        observed = timestamp(entry["observed_at"])
        require(timestamp(starts[attempt]["at"]) <= observed <= timestamp(finished[attempt]["at"]),
                "观察时间超出回执窗口")
        require(isinstance(entry["models"], list) and entry["models"]
                and all(model in MODELS for model in entry["models"])
                and entry["region"] == "中国大陆", "来源适用范围不符")
    require(set(decision["models"]) == set(MODELS), "两款决策行缺失")
    require(all(decision[flag] is False for flag in SAFE_FLAGS), "决策安全标志")
    published = 0
    for model, record in decision["models"].items():
        require(record["before_action"] and record["after_action"]
                and type(record["action_changed"]) is bool, "前后行动缺失")
        action_ids = record["action_source_ids"]
        require(all(model in sources[key]["models"] for key in action_ids)
                and (not record["action_changed"] or bool(action_ids)), "行动无准确出处")
        for kind in (*PATHS, "reuse_conditions", "sales_identity", "henan_payable"):
            row = record[kind]
            status = STATES[row["status"]]
            ids = row["source_ids"]
            require(all(model in sources[key]["models"] for key in ids)
                    and (status == "unknown" or bool(ids)) and row["reason"], "判读无法回查")
            if kind == "henan_payable":
                require(status == "unknown", "原案无法核验河南应付价")
            if kind in PATHS and row.get("publish"):
                require(status != "unknown", "不可发布未知为已核事实")
                output = runs["1"][kind]
                public = output["public_decision"] or {}
                claims = [c for c in public.get("claims", []) if c["candidate_id"] == model
                          and c["dimension"] == PATHS[kind][1] and c["status"] == status
                          and c["claim_id"] in output["text"]]
                require(any(set(ids) <= {s["source_id"] for s in c["source_audit"]} for c in claims),
                        "真实入口缺少对应命题或来源")
                published += 1
    expected = "integrated" if published else "blocked_no_admissible_fact"
    require(decision["mode"] == expected, "执行分支与可发布资料不符")
    if published:
        require((ROOT / "knowledge/printer_reviewed_evidence_v1.json").is_file()
                and (ROOT / "tests/test_printer_reviewed_evidence.py").is_file(), "接线或专项缺失")
        require(any(line in runs["1"]["revised_budget"]["text"] for line in ("800", "800元")),
                "改答预算未显示")
    else:
        require(all(not row["public_decision"] for row in runs["1"].values()), "无据产生比较")
    require((TASK / "DECISION_HANDOFF.md").stat().st_size > 0, "行动单缺失")
    return {"mode": expected, "published_paths": published, "attempts": len(starts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    runs = replay()
    if args.baseline:
        require(all(not row["public_decision"] for row in runs["1"].values()),
                "前测已发布结构化商品结论")
        summary = {"mode": "old_backend_no_admitted_facts"}
    else:
        summary = check_delivery(runs)
    print(json.dumps({"summary": summary, "chat": runs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
