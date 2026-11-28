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
from .product_compare import compare_products
from .p0_7_official_details import load_reviewed_local_replay

_FIELDS = {
    "category", "usage", "budget_max_cny", "budget_scope", "monthly_pages_range",
    "needs_color", "accepts_outsourced_color", "requires_wireless", "requires_scan",
    "requires_auto_duplex", "wechat_required", "wechat_workflow",
    "delivery_region", "device_deployment_region", "accepts_initial_setup", "requirements", "idle_weeks_pattern",
}
_BOOLEAN = {
    "needs_color", "accepts_outsourced_color", "requires_wireless",
    "requires_scan", "requires_auto_duplex", "wechat_required", "accepts_initial_setup",
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
    elif field == "idle_weeks_pattern":
        if type(value) is not str or value not in ("often_long", "usually_short"):
            raise ValueError("invalid_idle_weeks_pattern")
    elif field == "requirements":
        if (not isinstance(value, list) or len(value) > 20
                or any(not isinstance(x, str) or not 1 <= len(x) <= _MAX_TEXT for x in value)):
            raise ValueError("invalid_requirements")
    elif field in ("wechat_workflow", "budget_scope"):
        options = (("unknown", "miniprogram", "transfer_to_app") if field == "wechat_workflow"
                   else ("unknown", "hardware_only", "device_delivered", "device_and_extra_consumables"))
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


def compare_dialogue(state: dict, *, catalog_override: dict | None = None) -> dict:
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
    source_mode = "caller_injected_manufacturer_facts"
    source_warning = None
    if catalog_override is None:
        try:
            catalog_override = load_reviewed_local_replay()
            source_mode = "recorded_manufacturer_detail_replay_no_network"
        except (FileNotFoundError, OSError, ValueError):
            # 原文缺失或完整性检查失败时，只能降级为旧目录快照；绝不回退到旧详情摘要。
            source_mode = "older_manufacturer_directory_snapshot_only"
            source_warning = "本机型号详情原文缺失或完整性校验失败，已降级为旧目录快照；未使用旧详情摘要。"
    if catalog_override is None:
        result = compare_public_snapshot(required=conditions["required"],
                                         preferred=conditions["preferred"],
                                         budget_max_cny=req.budget_max_cny)
    else:
        # 仅供内部已核对厂商事实实验调用；不能接受用户输入任意商品事实。
        fact_result = compare_products(
            catalog_override, category="printer", required=conditions["required"],
            preferred=conditions["preferred"], budget_max_cny=req.budget_max_cny,
            target_region="CN")
        result = {"operation": "injected_manufacturer_facts_only",
                  "comparison": fact_result, "approved_purchase_count": 0,
                  "purchase_recommendation_approved": False, "transactions_enabled": False}
    return {**base, "status": "model_facts_only_not_purchase",
            "source_mode": source_mode,
            **({"source_warning": source_warning} if source_warning else {}),
            "questions": conditions["questions"],
            "unresolved_actions": [{"issue": q, "state": "optional_confirmation_or_defer"}
                                    for q in conditions["questions"]],
            "comparison": result, "unknowns": conditions["unresolved_hard_conditions"]}


def main() -> None:
    """一行JSON为一轮用户显式确认，例如 {"text":"黑白就够","answers":{"needs_color":false}}。"""
    import argparse
    from pathlib import Path
    from .discovery_pool import build_discovery_pool

    parser = argparse.ArgumentParser()
    parser.add_argument("--haina-report", type=Path,
                        help="仅用于接入测试的海纳离线导入报告；真实响应须先获用途许可")
    parser.add_argument("--haina-mcp-report", type=Path,
                        help="显式加载本机MCP合成测试包；真实响应在用途许可核准前阻断")
    parser.add_argument("--sale-evidence-report", type=Path,
                        help="P0.9-B销售配置离线合同测试；仅synthetic_test，非真实身份核验")
    parser.add_argument("--real-printer-case", action="store_true",
                        help="H08真实需求公开来源研究比较（仅待审理由，不接真实销售SKU/报价）")
    args = parser.parse_args()
    discovery_context = None
    haina_mcp_context = None
    sale_context = None
    sale_report = None
    if args.haina_mcp_report is not None:
        from .haina_mcp_ingest import load_haina_mcp_report
        haina_mcp_context = load_haina_mcp_report(args.haina_mcp_report)
    if args.sale_evidence_report is not None:
        try:
            if (not args.sale_evidence_report.is_file()
                    or args.sale_evidence_report.stat().st_size > 200_000):
                raise ValueError("sale_evidence_missing_or_too_large")
            sale_report = json.loads(args.sale_evidence_report.read_text(encoding="utf-8"))
            sale_context = build_discovery_pool(
                [], sale_configuration_report=sale_report)["sale_configuration_evidence"]
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            sale_context = {
                "status": "sale_evidence_unavailable",
                "error": type(exc).__name__,
                "configuration_count": 0, "configurations": [],
                "real_identity_verified_count": 0,
                "purchase_recommendation_approved": False,
                "transactions_enabled": False,
            }
    if args.haina_report is not None:
        try:
            if not args.haina_report.is_file() or args.haina_report.stat().st_size > 200_000:
                raise ValueError("haina_report_missing_or_too_large")
            report = json.loads(args.haina_report.read_text(encoding="utf-8"))
            discovery_context = build_discovery_pool([report])
            leads = discovery_context.get("unverified_source_leads", [])
            discovery_context["total_unverified_source_lead_count"] = len(leads)
            discovery_context["displayed_source_lead_count"] = min(3, len(leads))
            discovery_context["unverified_source_leads"] = leads[:3]
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            discovery_context = {
                "status": "discovery_report_unavailable",
                "error": type(exc).__name__,
                "candidate_count": 0,
                "unverified_source_lead_count": 0,
                "unverified_source_leads": [],
                "purchase_recommendation_approved": False,
                "transactions_enabled": False,
            }

    # Windows 管道默认可能使用 GBK；文本 JSONL 契约固定 UTF-8，避免父子进程误解码。
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    state = new_dialogue()
    print(json.dumps({"status": "ready", "questions": next_questions(state)}, ensure_ascii=False), flush=True)
    for raw in sys.stdin:
        try:
            turn = json.loads(raw)
            state = apply_turn(state, turn["answers"], raw_text=turn["text"])
            comparison = compare_dialogue(state)
            fact_result = comparison.get("comparison", {}).get("comparison", {})
            candidates = fact_result.get("candidates") if isinstance(fact_result, dict) else None
            if isinstance(candidates, list):
                fact_result["total_candidate_count"] = len(candidates)
                displayed = candidates[:3]
                excluded = next((x for x in candidates
                                 if x.get("status") == "excluded_by_verified_spec"), None)
                if excluded and all(x.get("model_id") != excluded.get("model_id") for x in displayed):
                    displayed = candidates[:2] + [excluded]
                fact_result["displayed_candidate_count"] = len(displayed)
                fact_result["candidates"] = displayed
            out = {"version": state["version"], "questions": next_questions(state),
                   "comparison": comparison, "history": state["history"][-1]}
            if haina_mcp_context is not None:
                out["haina_mcp_research"] = haina_mcp_context
            if args.real_printer_case:
                from .real_printer_case import compare_case_research
                # 此处仅按本轮已显式确认条件筛研究理由，绝不代替平台SKU证据。
                out["real_printer_case_research"] = compare_case_research(_values(state))
            if "research_context" in turn:
                from .minimal_research import build_research_case
                # 只准选择本机固定旧摘要，不读取输入中的任意事实或路径。
                out["research_case"] = build_research_case(_values(state), turn["research_context"])
            if discovery_context is not None:
                out["discovery_pool"] = discovery_context
            if sale_report is not None:
                # 每轮按当前时刻重新核验原观察事件，绝不刷新原来源时间。
                # 兼容受控模拟钟：时间来自门禁模块，而不是CLI启动缓存。
                from . import sale_configuration_evidence as sale_gate
                current = sale_gate.datetime.now(sale_gate.timezone.utc)
                try:
                    sale_context = build_discovery_pool(
                        [], now=current, sale_configuration_report=sale_report
                    )["sale_configuration_evidence"]
                except (ValueError, TypeError, OSError) as exc:
                    sale_context = {
                        "status": "sale_evidence_unavailable",
                        "error": type(exc).__name__, "configuration_count": 0,
                        "configurations": [], "real_identity_verified_count": 0,
                        "purchase_recommendation_approved": False,
                        "transactions_enabled": False,
                    }
            if sale_context is not None:
                # 按用户本轮最新条件，仅关联已核的厂商型号规格；平台所售配置
                # 仍是合成合同测试，绝不提升真实身份、预算或购买批准。
                view = deepcopy(sale_context)
                matched = {x.get("model_id"): x for x in candidates or []
                           if isinstance(x, dict)}
                details = []
                for config in view.get("configurations", [])[:3]:
                    detail = dict(config)
                    matched_row = (matched.get(detail["selected_model_id"])
                                   if detail.get("status") == "synthetic_field_binding_test_only"
                                   else None)
                    detail["manufacturer_model_fact_status"] = (
                        "manufacturer_facts_comparison_available"
                        if matched_row else "manufacturer_facts_not_compared")
                    detail["required_met"] = matched_row.get("required_met", []) if matched_row else []
                    detail["required_unknown"] = matched_row.get("required_unknown", []) if matched_row else []
                    detail["required_failed"] = matched_row.get("required_failed", []) if matched_row else []
                    detail["next_verification"] = (
                        "核平台真实所售配置及授权用途，再核地区价格、库存与预算；本行仅合成合同测试"
                    )
                    details.append(detail)
                view["displayed_configuration_count"] = len(details)
                view["configurations"] = details
                out["sale_configuration_evidence"] = view
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            out = {"status": "invalid_turn", "error": str(exc)}
        print(json.dumps(out, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
