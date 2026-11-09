"""文本优先的购物条件状态与动态追问最小链路（受控规则，不是大模型自主研究）。

对话存用户确认为事实的条件；新回答覆盖旧回答，比较每次从最新状态重新计算。
真正商品仍来自现有公开厂商目录快照；本模块不能核实时价或批准购买。
"""
from __future__ import annotations

from copy import deepcopy
import json
import sys

from .contracts import PurchaseRequest
from .printer_conditions import printer_conditions
from .public_catalog import compare_public_snapshot

_FIELDS = {
    "category", "usage", "budget_max_cny", "budget_scope", "monthly_pages_range",
    "needs_color", "accepts_outsourced_color", "requires_wireless", "requires_scan",
    "requires_auto_duplex", "wechat_required", "wechat_workflow",
    "delivery_region", "requirements",
}
_BOOLEAN = {
    "needs_color", "accepts_outsourced_color", "requires_wireless",
    "requires_scan", "requires_auto_duplex", "wechat_required",
}
_MAX_TEXT = 350


def new_dialogue() -> dict:
    return {
        "version": 0, "answers": {}, "history": [], "pending_approval": True,
        "transactions_enabled": False, "purchase_recommendation_approved": False,
    }


def _check_answer(field: str, value: object) -> None:
    if field not in _FIELDS:
        raise ValueError(f"unsupported_slot:{field}")
    if value is None:
        return  # 清除旧答案，不等于回答“否”
    if field in _BOOLEAN:
        if type(value) is not bool:
            raise ValueError(f"invalid_bool:{field}")
    elif field == "budget_max_cny":
        if type(value) is not int or not 0 <= value <= 10_000_000:
            raise ValueError("invalid_budget")
    elif field == "monthly_pages_range":
        if (not isinstance(value, list) or len(value) != 2
                or any(type(x) is not int or x < 0 or x > 100_000 for x in value)
                or value[0] > value[1]):
            raise ValueError("invalid_page_range")
    elif field == "requirements":
        if (not isinstance(value, list) or len(value) > 20
                or any(not isinstance(x, str) or not 1 <= len(x) <= _MAX_TEXT for x in value)):
            raise ValueError("invalid_requirements")
    elif field in ("wechat_workflow", "budget_scope"):
        options = (("unknown", "miniprogram", "transfer_to_app") if field == "wechat_workflow"
                   else ("unknown", "device_delivered", "device_and_extra_consumables"))
        if value not in options:
            raise ValueError(f"invalid_choice:{field}")
    elif not isinstance(value, str) or not 1 <= len(value.strip()) <= _MAX_TEXT:
        raise ValueError(f"invalid_text:{field}")


def apply_turn(state: dict, changes: dict, *, raw_text: str) -> dict:
    """只接受显式字段确认，未解析自由文本由用户下次补充；不把猜测当确认。"""
    if (not isinstance(state, dict) or type(state.get("version")) is not int
            or not isinstance(state.get("answers"), dict)
            or not isinstance(state.get("history"), list)):
        raise ValueError("invalid_dialogue_state")
    if (not isinstance(changes, dict) or not changes or len(changes) > 20
            or not isinstance(raw_text, str) or not 1 <= len(raw_text) <= 1000):
        raise ValueError("invalid_turn")
    for field, value in changes.items():
        _check_answer(field, value)
    next_state = deepcopy(state)
    updated = []
    for field, value in changes.items():
        prev = next_state["answers"].get(field, {})
        if value is None:
            next_state["answers"].pop(field, None)
        else:
            next_state["answers"][field] = {
                "value": value, "origin": "user_explicit", "confirmed": True,
                "raw_text": raw_text,
            }
        if prev.get("value") != value:
            updated.append(field)
    next_state["version"] += 1
    next_state["history"].append({"version": next_state["version"], "raw_text": raw_text,
                                   "changed_fields": updated, "old_conclusions_invalidated": bool(updated)})
    next_state["purchase_recommendation_approved"] = False
    next_state["transactions_enabled"] = False
    return next_state


def _values(state: dict) -> dict:
    return {k: v["value"] for k, v in state["answers"].items()
            if isinstance(v, dict) and v.get("confirmed") is True
            and v.get("origin") == "user_explicit"}


def next_questions(state: dict, *, limit: int = 2) -> list[dict]:
    """按当前缺口提出少量会改变下一步动作的问题，不重复已确认值。"""
    if not 1 <= limit <= 3:
        raise ValueError("invalid_limit")
    v = _values(state)
    questions = []
    def ask(field: str, prompt: str, why: str) -> None:
        if field not in v:
            questions.append({"field": field, "question": prompt, "why": why,
                              "status": "user_confirmation_needed"})
    ask("category", "准备买什么类别的商品？", "决定下一步查询哪些有来源的商品目录")
    if not v.get("category"):
        return questions[:limit]
    ask("usage", "主要用来做什么？", "用途影响硬条件与之后的取舍")
    if v["category"] == "printer":
        ask("needs_color", "必须在家打印彩色吗？", "决定是否排除仅支持黑白打印的机型")
        if v.get("needs_color") is False:
            ask("accepts_outsourced_color", "偶尔要彩印时，可以去打印店解决吗？",
                "决定是否只比较黑白打印机")
        ask("budget_max_cny", "主机预算大约是多少元？", "帮助安排价格核验，不会直接判断到手价")
        if "budget_max_cny" in v and v.get("budget_scope", "unknown") == "unknown":
            ask("budget_scope", "预算包含运费及额外耗材吗？", "不同预算口径影响最终购买资格")
        if v.get("wechat_required") is True and v.get("wechat_workflow", "unknown") == "unknown":
            ask("wechat_workflow", "必须微信小程序直接打印，还是可以通过厂商App？",
                "连接方式不同会改变候选可用性")
        if "monthly_pages_range" not in v:
            ask("monthly_pages_range", "每月大约打印多少页？可以给范围。", "影响打印方案与成本研究")
    else:
        # 新品类仅做表达验证；不把通用品类默认知识冒充领域理解。
        ask("budget_max_cny", "大概预算是多少？", "用于后续价格核验")
    return questions[:limit]


def compare_dialogue(state: dict) -> dict:
    v = _values(state)
    base = {"session_version": state["version"],
            "purchase_recommendation_approved": False, "transactions_enabled": False}
    if v.get("category") != "printer":
        return {**base, "status": "category_facts_not_connected",
                "message": "该品类只支持需求表达；尚未接专业证据与商品比较"}
    if v.get("needs_color") is None:
        return {**base, "status": "needs_color_clarification"}
    req = PurchaseRequest(
        category="printer", budget_max_cny=v.get("budget_max_cny"),
        needs_color=v.get("needs_color"),
        accepts_outsourced_color=v.get("accepts_outsourced_color"),
        monthly_pages_range=tuple(v["monthly_pages_range"]) if "monthly_pages_range" in v else None,
        requirements=tuple(v.get("requirements", [])),
        requires_wireless=v.get("requires_wireless"),
        requires_scan=v.get("requires_scan"),
        requires_auto_duplex=v.get("requires_auto_duplex"),
        wechat_required=v.get("wechat_required"),
        wechat_workflow=v.get("wechat_workflow", "unknown"),
        delivery_region=v.get("delivery_region"),
        budget_scope=v.get("budget_scope", "unknown"),
    )
    conditions = printer_conditions(req)
    if conditions["conflicts"]:
        return {**base, "status": "condition_conflict",
                "conflicts": conditions["conflicts"]}
    result = compare_public_snapshot(required=conditions["required"],
                                     preferred=conditions["preferred"],
                                     budget_max_cny=req.budget_max_cny)
    return {**base, "status": "model_facts_only_not_purchase",
            "questions": conditions["questions"],
            "comparison": result, "unknowns": conditions["unresolved_hard_conditions"]}


def main() -> None:
    """一行JSON为一轮用户显式确认，例如 {"text":"黑白就够","answers":{"needs_color":false}}。"""
    state = new_dialogue()
    print(json.dumps({"status": "ready", "questions": next_questions(state)}, ensure_ascii=False), flush=True)
    for raw in sys.stdin:
        try:
            turn = json.loads(raw)
            state = apply_turn(state, turn["answers"], raw_text=turn["text"])
            out = {"version": state["version"], "questions": next_questions(state),
                   "comparison": compare_dialogue(state), "history": state["history"][-1]}
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            out = {"status": "invalid_turn", "error": str(exc)}
        print(json.dumps(out, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
