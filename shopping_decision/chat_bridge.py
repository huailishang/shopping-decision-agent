"""Swing 对话式需求的只读适配：显式发送才调用 apply_turn；商品判断复用 web.evaluate_input。

该模块不使用LLM猜测自由文字、不收集账号、不访问商城、不开放购买。
CLI参数依次是 base64(state JSON), base64(field), base64(submitted text)。
返回 DesktopBridgeClient 的 base64 键值文本协议。
"""
from __future__ import annotations

import base64
import json
import re
import sys

from .desktop_bridge import encode
from .dialogue_flow import apply_turn, new_dialogue, next_questions
from .web import evaluate_input
from .claim_gate import publish_checked_comparison
from .evidence_comparison import digest
from .minimal_research import selected_pack

UNKNOWN = {"暂不确定", "不确定", "不知道", "未知", "待确认", "先跳过"}
BOOL = {"是": True, "需要": True, "必须": True, "接受": True,
        "否": False, "不需要": False, "不是必须": False, "不接受": False}
LABELS = {
    "category": "商品品类", "usage": "主要用途", "needs_color": "家中彩印是否必须",
    "accepts_outsourced_color": "能否外包彩印", "wechat_required": "微信是否必须",
    "accepts_initial_setup": "是否接受首次App/扫码设置",
    "wechat_workflow": "微信打印方式", "device_deployment_region": "打印机使用国家/地区",
    "monthly_pages_range": "月打印页数", "budget_max_cny": "预算（元）",
    "budget_scope": "预算范围", "requires_scan": "扫描功能是否必须",
    "requires_auto_duplex": "自动双面是否必须", "delivery_region": "收货地区",
}
QUESTION = {
    "category": "准备买什么商品？请明确品类（不会从含糊原话自动猜测）。",
    "usage": "主要用来做什么？可用自己的话描述。",
    "needs_color": "必须在家打印彩色吗？",
    "accepts_outsourced_color": "偶尔需要彩印时，能去打印店处理吗？",
    "wechat_required": "微信打印是必须条件，还是更喜欢但非必须？",
    "accepts_initial_setup": "第一次连接时，能接受使用厂商App和/或扫码完成设置吗？",
    "wechat_workflow": "需要微信小程序直接打印，还是能接受文件转存厂商App？",
    "device_deployment_region": "打印机实际在哪个国家或地区使用？不是收货地。",
    "monthly_pages_range": "每月大约打印多少页？可以输入区间。",
    "budget_max_cny": "这次购买主机的预算上限是多少元？",
    "budget_scope": "预算是否包括运费和另购耗材？",
    "requires_scan": "扫描或复印是否是必须功能？",
    "requires_auto_duplex": "自动双面打印是否必须？",
    "delivery_region": "商品将收货到哪个地区（无需详细住址）？",
}
REFS = {
    "category": [("打印机", "打印机"), ("手机", "手机"), ("电热水壶", "电热水壶")],
    "usage": [("示例：家用打印学习资料", "家用打印学习资料")],
    "needs_color": [("是", "是"), ("否", "否")],
    "accepts_outsourced_color": [("是", "是"), ("否", "否")],
    "wechat_required": [("必须", "必须"), ("偏好（非必须）", "不是必须")],
    "accepts_initial_setup": [("接受", "接受"), ("不接受", "不接受")],
    "wechat_workflow": [("微信小程序直接打印", "微信小程序直接打印"),
                        ("文件转存厂商App", "文件转存厂商App")],
    "device_deployment_region": [("示例：中国大陆", "中国大陆")],
    "monthly_pages_range": [("示例：0-50", "0-50")],
    "budget_max_cny": [("示例：1000元", "1000")],
    "budget_scope": [("主机含运费及必要支出", "主机含运费及必要支出"),
                     ("含额外耗材", "含额外耗材")],
    "requires_scan": [("是", "是"), ("否", "否")],
    "requires_auto_duplex": [("是", "是"), ("否", "否")],
}
PRINTER_FIELDS = {
    "needs_color", "accepts_outsourced_color", "wechat_required", "accepts_initial_setup",
    "wechat_workflow", "device_deployment_region", "monthly_pages_range", "requires_scan",
    "requires_auto_duplex", "delivery_region", "budget_scope",
}
FIELD_ORDER = (
    "category", "usage", "needs_color", "accepts_outsourced_color",
    "wechat_required", "accepts_initial_setup", "wechat_workflow",
    "device_deployment_region", "monthly_pages_range", "budget_max_cny",
    "requires_scan", "requires_auto_duplex", "budget_scope", "delivery_region",
)


def confirmed_values(state: dict) -> dict:
    return {k: r["value"] for k, r in state["answers"].items()
            if isinstance(r, dict) and r.get("confirmed") is True
            and r.get("origin") == "user_explicit"}


def _valid_state(state: dict) -> dict:
    if not isinstance(state, dict):
        raise ValueError("会话状态必须是对象")
    if type(state.get("version")) is not int or not isinstance(state.get("answers"), dict):
        raise ValueError("会话状态无效")
    if not isinstance(state.get("history"), list) or len(state["history"]) > 30:
        raise ValueError("会话历史无效或过长，请新建会话")
    if len(json.dumps(state, ensure_ascii=False).encode("utf-8")) > 11000:
        raise ValueError("会话状态过长")
    if any(k not in LABELS for k in state["answers"]):
        raise ValueError("存在未允许的条件字段")
    for k, r in state["answers"].items():
        if not isinstance(r, dict) or r.get("origin") != "user_explicit" or r.get("confirmed") is not True:
            raise ValueError("存在未确认的会话字段")
    state["purchase_recommendation_approved"] = False
    state["transactions_enabled"] = False
    skipped = state.get("deferred_fields", [])
    if not isinstance(skipped, list) or any(f not in LABELS for f in skipped):
        raise ValueError("待确认字段无效")
    return state


def _question_fields(state: dict) -> list[str]:
    v = confirmed_values(state)
    skipped = set(state.get("deferred_fields", []))
    # 复用现有问答分流，并在聊天入口按最有信息增量的顺序补字段。
    legacy = {q["field"] for q in next_questions(state, limit=3)}
    if "category" not in v:
        return [] if "category" in skipped else ["category"]
    if "usage" not in v and "usage" not in skipped:
        return ["usage"]
    if v["category"] != "printer":
        return [f for f in ("budget_max_cny",) if f not in v and f not in skipped]
    wants_wechat = v.get("wechat_required") is True or "微信" in v.get("usage", "")
    fields = ["needs_color"]
    if v.get("needs_color") is False:
        fields.append("accepts_outsourced_color")
    fields.append("wechat_required")
    if wants_wechat:
        fields.append("accepts_initial_setup")
    if v.get("wechat_required") is True:
        fields.extend(("wechat_workflow", "device_deployment_region"))
    elif wants_wechat and v.get("wechat_required") is False:
        fields.append("device_deployment_region")
    fields.extend(("monthly_pages_range", "budget_max_cny"))
    # legacy里出现的必要问题仍处在当前问答链，但预算口径仅到核实时再问。
    return [f for f in fields if f not in v and f not in skipped and (f in LABELS or f in legacy)]


def _parse(field: str, submitted: str):
    v = submitted.strip()
    if not v or len(v) > 350:
        raise ValueError("请输入1至350字的明确答复，或填写“暂不确定”")
    if v in UNKNOWN:
        return None
    if field in ("needs_color", "accepts_outsourced_color", "wechat_required",
                 "accepts_initial_setup", "requires_scan", "requires_auto_duplex"):
        if field == "wechat_required" and v == "偏好":
            return False
        if v not in BOOL:
            raise ValueError("本问题请明确回复“是/否”或“暂不确定”，其他原话暂不自动判断")
        return BOOL[v]
    if field == "category":
        names = {"打印机": "printer", "printer": "printer", "手机": "phone", "phone": "phone",
                 "电热水壶": "kettle", "kettle": "kettle"}
        if v in names:
            return names[v]
        # 明确提及唯一品类的一句话，只识别品类；附带用途仍需本人下轮确认。
        lead = re.fullmatch(r"(?:我)?(?:想|希望|打算|需要)?(?:买|购买|选购|找)(?:一台|一部|一款|一个|台|部|个)?\s*(打印机|手机|电热水壶)(?:[，,。\s].*)?", v)
        if lead:
            return names[lead.group(1)]
        if not re.fullmatch(r"[\w\u4e00-\u9fff-]{2,30}", v):
            raise ValueError("请单独发送品类名，如“打印机”；需求用途下一轮再描述")
        return v
    if field == "budget_max_cny":
        m = re.fullmatch(r"([0-9]{1,8})\s*元?", v)
        if not m:
            raise ValueError("预算请填整数，如1000；示例不是自动确认")
        return int(m.group(1))
    if field == "monthly_pages_range":
        m = re.fullmatch(r"([0-9]{1,6})(?:\s*[-–~至]\s*([0-9]{1,6}))?\s*(?:页)?", v)
        if not m:
            raise ValueError("请填月页数，例如0-50或50")
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if lo > hi or hi > 100000:
            raise ValueError("月页数范围无效")
        return [lo, hi]
    if field == "wechat_workflow":
        mapping = {"微信小程序直接打印": "miniprogram", "小程序": "miniprogram",
                   "文件转存厂商App": "transfer_to_app", "厂商App": "transfer_to_app",
                   "转App": "transfer_to_app"}
        if v not in mapping:
            raise ValueError("请选明确的微信方式，或暂不确定")
        return mapping[v]
    if field == "budget_scope":
        mapping = {"主机含运费及必要支出": "device_delivered",
                   "含额外耗材": "device_and_extra_consumables"}
        if v not in mapping:
            raise ValueError("预算口径须选可审选项，或暂不确定")
        return mapping[v]
    return v


def submit_message(state: dict, field: str, submitted: str) -> dict:
    _valid_state(state)
    v = confirmed_values(state)
    if field == "batch":
        # 明示“字段：答复”的本轮批量提交；不自动拆解随意自然语言。
        if len(submitted) > 1000:
            raise ValueError("本轮批量答复太长")
        lines = [line.strip() for line in submitted.splitlines() if line.strip()]
        if not 1 <= len(lines) <= 8:
            raise ValueError("请每行写一项字段：答复，最多8项")
        labels = {label: name for name, label in LABELS.items()}
        changes = {}
        for line in lines:
            if "：" in line:
                key, value = line.split("：", 1)
            elif ":" in line:
                key, value = line.split(":", 1)
            else:
                raise ValueError("批量答复需要明确字段名和冒号")
            name = labels.get(key.strip(), key.strip())
            if name not in LABELS or name == "category" or name in changes:
                raise ValueError("不支持的/重复的批量字段：" + key.strip())
            if name in PRINTER_FIELDS and v.get("category") != "printer":
                raise ValueError("非打印机不能填打印机条件")
            changes[name] = _parse(name, value)
    else:
        if field not in LABELS:
            raise ValueError("当前没有可确认的条件字段")
        if field in PRINTER_FIELDS and v.get("category") != "printer":
            raise ValueError("此字段仅适用于打印机，不能跨品类使用")
        parsed = _parse(field, submitted)
        changes = {field: parsed}
        if field == "category" and parsed != v.get("category"):
            # 换品类也要清预算等旧需求，不能把原打印机用户条件当成新商品的确认。
            changes.update({k: None for k in list(v) if k != "category"})
    state = apply_turn(state, changes, raw_text=submitted)
    skipped = set(state.get("deferred_fields", []))
    for name, value in changes.items():
        if value is None:
            skipped.add(name)
        else:
            skipped.discard(name)
    if field == "category" and changes.get("category") != v.get("category"):
        skipped = set()
    state["deferred_fields"] = sorted(skipped)
    # 只保留合理有界的本次会话原话；跨会话不自动保存到磁盘。
    return state


def _analysis(state: dict) -> dict | None:
    v = confirmed_values(state)
    if v.get("category") != "printer" or "usage" not in v:
        return None
    data = {"category": "printer", "description": v["usage"], "confirmed": True,
            "needs_color": v.get("needs_color"),
            "accepts_outsourced_color": v.get("accepts_outsourced_color"),
            "wechat_required": v.get("wechat_required"),
            "wechat_workflow": v.get("wechat_workflow", "unknown"),
            "device_deployment_region": v.get("device_deployment_region"),
            "monthly_pages_range": v.get("monthly_pages_range"),
            "budget_max_cny": v.get("budget_max_cny"),
            "budget_scope": v.get("budget_scope", "unknown"),
            "requires_scan": v.get("requires_scan"),
            "requires_auto_duplex": v.get("requires_auto_duplex"),
            "delivery_region": v.get("delivery_region"),
            # 现有PurchaseRequest暂无首次设置专用字段；将明确拒绝作为待核硬条件，
            # 交由原证据/冲突门禁处理，不能因聊天字段没映射而默认设备可用。
            "requirements": (["必须免去厂商App或扫码首次设置"]
                             if v.get("accepts_initial_setup") is False else [])}
    if "research_context" in state:
        data["research_context"] = state["research_context"]
        data["accepts_initial_setup"] = v.get("accepts_initial_setup")
    return evaluate_input(data)


def _publish_for_chat(analysis: dict, values: dict, version: int) -> dict | None:
    """Only accept typed backend data bound to this dialogue; never legacy prose.

    The existing backend provides no typed bundle, so ordinary chat correctly
    falls back to unverified research until that contract is populated.
    """
    if not isinstance(analysis, dict):
        return None
    bundle = analysis.get("verified_research_bundle")
    if not isinstance(bundle, dict):
        return None
    if (bundle.get("category") != values.get("category") or
            type(bundle.get("dialogue_version")) is not int or
            bundle["dialogue_version"] != version or
            bundle.get("confirmed_values_sha256") != digest(values)):
        return None
    # User budget and deployment geography must match the rule input exactly.
    if values.get("device_deployment_region") and bundle.get("region") != values["device_deployment_region"]:
        return None
    budget = values.get("budget_max_cny")
    if budget is not None and not any(
            r.get("unit") == "CNY" and r.get("op") == "lte" and
            type(r.get("value")) is int and r["value"] == budget
            for r in bundle.get("requirements", []) if isinstance(r, dict)):
        return None
    try:
        return publish_checked_comparison(bundle, origin="rule")
    except (ValueError, TypeError, KeyError, OverflowError):
        return None


def _safe_research_progress(state: dict, analysis: dict, values: dict) -> str:
    """Only confirmed user fields and SHA-pinned local pack metadata are publishable.

    The record count measures retained research notes, never verified model facts.
    Free-form report_text/decision_plan/next_action are deliberately ignored.
    """
    count = None
    context = state.get("research_context")
    research = analysis.get("research_case") if isinstance(analysis, dict) else None
    if isinstance(context, dict) and isinstance(research, dict):
        try:
            pack_id, pack = selected_pack(context)
            if research.get("evidence_pack_id") == pack_id:
                count = len(pack["claims"])
        except (ValueError, KeyError, TypeError, OSError):
            pass
    if count is None:
        progress = "当前没有可核对的受控研究包记录数；研究材料仍待核。"
    else:
        progress = f"当前受控研究包包含{count}条待核研究记录；记录数量不代表有效商品证据数。"
    wechat = values.get("wechat_required")
    if wechat is True:
        next_step = "微信打印是用户确认的必须条件：优先查证准确型号如何从微信发起、后续复用的具体条件；目前不能认定支持。"
    elif wechat is False:
        next_step = "微信打印是用户确认的可选条件：可继续核实低频印量、耗材和准确销售型号；微信未核不代表其余研究失败。"
    else:
        next_step = "微信是否必须尚未确认：先向用户澄清，再决定优先核查微信复用还是其他型号条件。"
    budget = values.get("budget_max_cny")
    requirement = (f"用户已确认预算上限为{budget}元；这不是商品售价或有效地区报价。"
                   if type(budget) is int else "用户预算尚未确认；不得推断任何商品满足预算。")
    if count == 0:
        next_research = "本次没有留存待核型号记录；先整理允许使用的来源，再核型号事实。"
    elif count is not None:
        next_research = "已有记录仅供研究排查；继续核原始来源、观察时间、适用型号和地区，不把旧文字当结果。"
    else:
        next_research = "先核实本轮研究包与来源记录是否可用，不能凭空生成商品结论。"
    return "\n".join((progress, requirement, next_step, next_research,
                      "研究资料未经过最终商品事实核验，不能据此推荐购买。"))


def _public_chat_text(public: dict | None, setup_guard: str, progress: str = "") -> str:
    """User-facing text is exclusively authored by this module and the gate."""
    if public is None:
        return (setup_guard + "商品判断：待核研究；本轮没有可对应当前用户需求的有效结构化商品事实。"
                + ("\n" + progress if progress else "")
                + "\n仍需查证：候选型号、匹配条件、原始来源、观察时间、适用地区和有效报价。"
                + "\n下一行动：补齐上述可追溯事实，再重新计算；现有旧研究文字仅留内部审计。"
                + "\n未批准购买，交易关闭，未核实实时价格。")
    lines = [setup_guard + "结构化条件比较（仅对准入事实和规则可核，不是购买许可）："]
    for i, assessment in enumerate(public["assessments"], 1):
        for j, item in enumerate(assessment["comparisons"], 1):
            lines.append(f"候选{i} 条件{j}：{item['text']} "
                         f"核验命题ID：{item['claim_id']}。适用边界：{item['limit']}")
    for action in public["next_actions"]:
        lines.append("下一行动：" + action["description"])
    lines.append("未批准购买，交易关闭，未核实实时价格。")
    return "\n".join(lines)


def render_chat(state: dict) -> dict:
    _valid_state(state)
    v = confirmed_values(state)
    fields = _question_fields(state)
    active = fields[0] if fields else ""
    prompt = QUESTION[active] if active else "已记录当前明确条件；可点击下方条件修改，或主动预览审计。"
    choices = [*(REFS.get(active, [])), ("暂不确定", "暂不确定")] if active else []
    confirmed = [f"{LABELS.get(k, k)}：{json.dumps(val, ensure_ascii=False)}"
                 for k, val in v.items()]
    missing = [LABELS.get(k, k) for k in fields]
    deferred = [LABELS.get(k, k) for k in state.get("deferred_fields", [])]
    understanding = ("已明确：\n" + ("\n".join(confirmed) if confirmed else "暂无")
                     + "\n\n尚需确认：" + ("、".join(missing) if missing else "当前无必须追问")
                     + ("\n暂不确定：" + "、".join(deferred) if deferred else "")
                     + "\n参考答案点击只填草稿，发送后才会被确认为用户原话。")
    analysis = _analysis(state)
    public_decision = None
    if analysis is None:
        outcome = ("尚未选择受审品类或缺用途，先收集需求；未给出商品推荐。"
                   if v.get("category") in (None, "printer")
                   else "该品类目前只能整理需求，尚无可用的专业商品材料；不会返回打印机候选。")
        status = "clarify" if v.get("category") in (None, "printer") else "unsupported"
    else:
        r = analysis["recommendation"]
        setup_guard = ("已确认不接受App/扫码首次设置；现有型号流程材料不足以证明免设置可用，"
                       "此条件先按未核硬要求处理。\n"
                       if v.get("accepts_initial_setup") is False else "")
        public_decision = _publish_for_chat(analysis, v, state["version"])
        research_progress = _safe_research_progress(state, analysis, v)
        outcome = _public_chat_text(public_decision, setup_guard, research_progress)
        # The status remains a dialogue workflow signal, never a verified
        # product claim. Only the gate-generated text can be published as such.
        status = r["status"]
    editable = "\n".join(f"{k}\t{LABELS[k]}\t{json.dumps(v[k], ensure_ascii=False) if k in v else '待确认'}"
                          for k in FIELD_ORDER
                          if (v.get("category") == "printer" or k not in PRINTER_FIELDS))
    report = {"dialogue": state, "confirmed_fields": v,
              "unconfirmed_fields": fields, "deferred_fields": state.get("deferred_fields", []),
              "research_result": analysis,
              "legacy_unverified_research": analysis is not None,
              "public_decision": public_decision,
              "public_claim_source": "publish_checked_comparison" if public_decision else "unverified_research_only",
              "purchase_recommendation_approved": False, "transactions_enabled": False,
              "live_price_verified": False}
    return {"status": status, "state_json": json.dumps(state, ensure_ascii=False),
            "prompt_field": active, "prompt": prompt,
            "choices": "\n".join(label + "\t" + draft for label, draft in choices),
            "understanding": understanding, "result_text": outcome,
            "editable": editable, "session_version": str(state["version"]),
            "report_json": json.dumps(report, ensure_ascii=False, indent=2)}


def main() -> None:
    try:
        args = sys.argv[1:]
        if len(args) != 3:
            raise ValueError("需要状态、条件字段和本轮发送原话")
        raw = [base64.b64decode(x, validate=True).decode("utf-8") for x in args]
        state = new_dialogue() if not raw[0] else json.loads(raw[0])
        if raw[1] or raw[2]:
            state = submit_message(state, raw[1], raw[2])
        out = render_chat(state)
    except (ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        out = {"error": str(exc)}
    for key, value in out.items():
        print(key + "\t" + encode(value))


if __name__ == "__main__":
    main()
