"""Build a local purchase-preparation checklist from confirmed household inputs."""

from .minimal_research import MODEL_NAMES


HARDWARE_ONLY = "hardware_only"
SCOPE_LABELS = {
    HARDWARE_ONLY: "仅主机硬件，运费及另购耗材单列",
    "device_delivered": "主机、运费及必要支出",
    "device_and_extra_consumables": "主机及额外耗材",
}

_WECHAT_STEPS = {
    "clarify_wechat": "先明确微信打印是硬条件还是偏好。",
    "continue_comparison": "微信是偏好，优先核低频耗材和所售配置，保留微信路径的未知。",
    "verify_no_setup": "先核是否能免厂商App或扫码完成首次设置；未取得适用证据前保留待核。",
    "choose_path": "先确认是在微信小程序内发起，还是可以把文件转到厂商App。",
    "verify_miniprogram": "核首次配置完成后，是否能直接在微信小程序发起；隔一段时间再从微信打印一份普通文件。",
    "verify_transfer": "核能否从微信把普通文件转到厂商App发起打印，并记录转存步骤。",
}


def _wechat_step(values):
    required = values.get("wechat_required")
    if required is False:
        return "continue_comparison"
    if required is not True:
        return "clarify_wechat"
    if values.get("accepts_initial_setup") is False:
        return "verify_no_setup"
    return {"miniprogram": "verify_miniprogram", "transfer_to_app": "verify_transfer"}.get(
        values.get("wechat_workflow"), "choose_path")


def _county_level(region):
    if not isinstance(region, str):
        return False
    region = region.strip()
    if any(marker in region for marker in ("未确认", "不确定", "未知", "待定", "待确认", "未定", "暂不", "示例")):
        return False
    return region.endswith(("县", "区", "旗")) and not region.endswith("自治区")


def build_purchase_checks(values):
    """Build actionable questions. This pilot has no authoritative price reader."""
    budget = values.get("budget_max_cny")
    scope = values.get("budget_scope")
    missing = []
    if not _county_level(values.get("delivery_region")):
        missing.append("delivery_region")
    if scope not in SCOPE_LABELS:
        missing.append("budget_scope")
    if type(budget) is not int:
        missing.append("budget_max_cny")
    step = _wechat_step(values)
    if step == "continue_comparison":
        actions = (
            "核同型号低频使用所需的初始墨粉、替换墨粉与硒鼓。",
            "按历史配置线索 9YF97A 核所售套装与耗材，保留在售状态待核。",
        )
    elif step in ("verify_transfer", "verify_no_setup", "choose_path", "clarify_wechat"):
        # The exact model action must follow the same confirmed workflow as
        # the aggregate action, without inferring support from an old path.
        actions = tuple(_WECHAT_STEPS[step] for _ in MODEL_NAMES)
    else:
        actions = (
            "按畅享印小程序线索核准确型号、首次配置及隔次微信发起。",
            "按历史配置线索 9YF97A 核型号，有条件时核惠普云打印首次绑定和隔次微信发起。",
        )
    return {
        "wechat_step": step,
        "wechat_action": _WECHAT_STEPS[step],
        "quote_missing": missing,
        "quote_status": "prerequisites_missing" if missing else "awaiting_authoritative_quote",
        "budget_max_cny": budget,
        "budget_scope": scope,
        "payable_cny": None,
        "candidates": [{"model": model, "next_step": action}
                       for model, action in zip(MODEL_NAMES.values(), actions)],
    }


def render_purchase_checks(checks):
    missing = checks["quote_missing"]
    labels = {"delivery_region": "实际收货区县", "budget_scope": "预算费用范围",
              "budget_max_cny": "预算金额"}
    budget = checks["budget_max_cny"]
    scope = SCOPE_LABELS.get(checks["budget_scope"], "费用范围待确认")
    lines = ["购买前核对", checks["wechat_action"]]
    lines.extend(f"{item['model']}：{item['next_step']}" for item in checks["candidates"])
    if type(budget) is int:
        lines.append(f"预算 {budget}元（{scope}）。")
    if missing:
        lines.append("核价前待确认：" + "、".join(labels[field] for field in missing) + "。")
    elif checks["budget_scope"] == HARDWARE_ONLY:
        lines.append("核同一收货区县的主机成交额，运费及另购耗材单列。")
    else:
        lines.append("核同一收货区县及费用范围下的完整应付价。")
    lines.append("核价回传：准确型号与配置、商家、区县、价格分项、观察时间及有效期。实际价格待核。")
    return "\n".join(lines)
