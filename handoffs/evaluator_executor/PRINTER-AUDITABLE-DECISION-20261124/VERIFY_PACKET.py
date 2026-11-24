"""Check auditable sources and replay the regular chat in both settings."""

import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import runpy


TASK = Path(__file__).resolve().parent
EXEC = TASK / "evidence" / "executor"
PRIOR = TASK.parent / "PRINTER-EVIDENCE-TO-DECISION-20261124"
LEGACY = runpy.run_path(str(PRIOR / "VERIFY_DELIVERY.py"))
MODELS = set(LEGACY["MODELS"])
PATHS = LEGACY["PATHS"]


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def timestamp(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(stamp.utcoffset() is not None, "缺取证时区")
    return stamp


def probe(packet, runs):
    require(set(packet["models"]) == MODELS and len(packet["open_questions"]) <= 3,
            "交付型号或待答问题不符")
    sources = packet["sources"]
    for row in sources.values():
        item = (EXEC / row["fragment_path"]).resolve()
        require(item.is_relative_to(EXEC) and item.is_file(), "缺少留存片段")
        body = item.read_bytes()
        require(sha256(body).hexdigest() == row["fragment_sha256"], "来源片段哈希不符")
        require(row["anchor"].strip() and row["anchor"] in body.decode("utf-8"),
                "原文定位不在留存片段中")
        require(row["kind"] in ("manufacturer", "owner_supplied_manufacturer")
                and LEGACY["official"](row["url"]) and row["locator"] and row["permitted_use"]
                and isinstance(row["models"], list) and set(row["models"]) <= MODELS
                and row["models"] and row["region"] == "中国大陆", "来源范围不符")
        timestamp(row["obtained_at"])
    for model, row in packet["models"].items():
        require(row["next_action"].strip() and all(source in sources and model in sources[source]["models"]
                                                   for source in row["action_source_ids"]),
                "下一行动缺失或引用的型号不符")
        for field in (*PATHS, "reuse", "sales_identity", "henan_payable"):
            item = row[field]
            require(item["note"] and item["status"] in (
                "documented_supported", "documented_unsupported", "conflict", "historical_lead", "unknown"),
                "缺判断状态")
            if field in PATHS and item["status"] in (
                    "documented_supported", "documented_unsupported", "conflict"):
                require(item["source_ids"], "可发布路径没有可核出处")
            require(all(key in sources and model in sources[key]["models"] for key in item["source_ids"]),
                    "引用型号不符")
    expected = {"met": "documented_supported", "failed": "documented_unsupported", "conflict": "conflict"}
    published = set()
    for variant, output in runs["1"].items():
        result = output["public_decision"] or {}
        for claim in result.get("claims", []):
            dimension = claim["dimension"]
            if dimension not in ("wechat_print", "wechat_miniprogram", "wechat_transfer_to_app"):
                continue
            if claim["status"] not in expected:
                continue
            model = claim["candidate_id"]
            ids = {row["source_id"] for row in claim["source_audit"] if row["admitted"]}
            path = next((name for name, (_, key) in PATHS.items() if key == dimension), None)
            require(ids and all(key in sources and model in sources[key]["models"] for key in ids),
                    "可见命题缺独立原文")
            if path:
                item = packet["models"][model][path]
                require(item["status"] == expected[claim["status"]] and ids <= set(item["source_ids"]),
                        "可见路径和行动单不一致")
            require(claim["claim_id"] in output["text"], "命题未进入真实用户文本")
            published.add((model, dimension))
    require(packet["mode"] == ("auditable_evidence" if published else "pending_source"),
            "模式与发布结果不一致")
    require((TASK / "DECISION_HANDOFF.md").stat().st_size > 0, "缺家庭行动单")
    return sorted(published)


def audit_attempts():
    scheduled, completed = {}, {}
    prior_lines = (PRIOR / "evidence" / "executor" / "attempts.jsonl").read_text(
        encoding="utf-8").splitlines()
    old_addresses = {json.loads(line)["target"] for line in prior_lines
                     if json.loads(line)["event"] == "scheduled" and json.loads(line)["kind"] == "open"}
    for text in (EXEC / "attempts.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(text)
        key, event = row["id"], row["event"]
        if event == "scheduled":
            require(key not in scheduled and row["kind"] in ("query", "open"), "重复或无效调度")
            if row["kind"] == "open":
                require(LEGACY["official"](row["target"]) and row["target"] not in old_addresses,
                        "重开历史地址或越过官方范围")
            timestamp(row["at"])
            scheduled[key] = row
        else:
            require(event == "completed" and key in scheduled and key not in completed
                    and timestamp(row["at"]) >= timestamp(scheduled[key]["at"]), "回执未配对")
            receipt = (EXEC / row["receipt"]).resolve()
            require(receipt.is_relative_to(EXEC) and receipt.is_file() and receipt.stat().st_size > 0,
                    "缺取证原始回执")
            completed[key] = row
    require(scheduled.keys() == completed.keys(), "存在未结束取证")
    for kind, limit in (("query", 4), ("open", 6)):
        require(sum(item["kind"] == kind for item in scheduled.values()) <= limit, "超取证额度")
    return len(scheduled)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    runs = LEGACY["replay"]()
    if args.baseline:
        initial = runs["1"]["miniprogram"]["public_decision"] or {}
        require(any(c["candidate_id"] == "Brother HL-L1238W" and c["status"] == "met"
                    for c in initial.get("claims", [])), "前测未见原 V1 小程序命题")
        summary = {"mode": "legacy_v1_positive_without_auditable_fragment"}
    else:
        packet = json.loads((EXEC / "packet.json").read_text(encoding="utf-8"))
        count = audit_attempts()
        publish = probe(packet, runs)
        summary = {"mode": packet["mode"], "published_confirmed_paths": publish, "attempts": count}
    print(json.dumps({"summary": summary, "chat": runs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
