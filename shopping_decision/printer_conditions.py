"""有限中文短语识别+结构化确认。遇到不理解的硬要求，逐候选保留未知。"""
from __future__ import annotations

import re
from .contracts import PurchaseRequest

WORKFLOWS = {"unknown", "miniprogram", "transfer_to_app"}
BUDGET_SCOPES = {"unknown", "device_delivered", "device_and_extra_consumables"}
HARD = r"(?:必须|务必|一定要|硬要求|要求)"
NEGATED_NEED = r"(?:不是必须|并非必须|不一定要|不需要|不要求|不必|无需)"


def printer_conditions(req: PurchaseRequest) -> dict:
    required = ({"color_print": True} if req.needs_color is True else
                {"monochrome_print": True} if req.needs_color is False else {})
    preferred, unresolved, questions, conflicts = {}, [], [], []
    for name, feature in (("requires_wireless", "wireless"), ("requires_scan", "scan"),
                          ("requires_auto_duplex", "auto_duplex")):
        if getattr(req, name) is True:
            required[feature] = True
    hard_wechat = req.wechat_required is True
    hard_mini, want_wechat = False, False
    for text in dict.fromkeys(req.requirements):
        for clause in re.split(r"[，,；;。\n]|但是|但|不过|而且|同时|并且|且", text):
            # 只屏蔽否定词自身，不能删除其后整个子句，吞掉后续正向硬要求。
            clean = re.sub(NEGATED_NEED, "〔否定〕", clause)
            if not clean.strip():
                continue
            if re.search(r'禁止|不得|不允许|绝不能|不能', clean):
                unresolved.append(clause.strip())
                continue
            if "微信" in clean and '〔否定〕' not in clean:
                want_wechat = True
            hard = re.search(HARD + r"\s*(.*)", clean)
            if not hard:
                continue
            payload = hard.group(1).strip(" ：:")
            # 只消费支持的完整短语；复合或陌生条件不因含已知词而消失。
            patterns = (
                (r"(?:从|用|使用)?微信小程序(?:直接|远程)?(?:打印)?", "wechat_miniprogram"),
                (r"(?:从|用|使用)?微信(?:直接|远程)?打印", "wechat_workflow"),
                (r"自动双面(?:打印)?", "auto_duplex"),
                (r"(?:支持|有)?(?:无线|Wi-Fi|wifi)(?:打印)?", "wireless"),
                (r"(?:支持|有)?扫描", "scan"),
                (r"(?:在家)?(?:打印彩色|彩色打印|彩印|彩色)", "color_print"),
                (r"(?:只打印|只打|打印)?黑白", "monochrome_print"),
            )
            consumed = payload
            for pattern, feature in patterns:
                match = re.match(pattern, consumed, flags=re.IGNORECASE)
                if match is None:
                    continue
                if feature == "wechat_workflow":
                    hard_wechat = True
                else:
                    required[feature] = True
                    hard_mini |= feature == "wechat_miniprogram"
                consumed = consumed[match.end():].strip()
                break
            if consumed:
                unresolved.append(clause.strip())
    if req.needs_color is False and required.get("color_print") is True:
        conflicts.append("用户确认只需黑白，与原文必须彩色打印冲突，请明确最新条件")
    if req.needs_color is True and required.get("monochrome_print") is True:
        conflicts.append("用户确认必须彩色，与原文只需黑白冲突，请明确最新条件")
    if hard_mini:
        hard_wechat = True
    if hard_wechat and req.wechat_required is False:
        conflicts.append("原文微信硬要求与“微信不是必须”确认冲突，请修改原话或确认项")
    if hard_mini and req.wechat_workflow == "transfer_to_app":
        conflicts.append("原文必须微信小程序与确认的转存App方式冲突")
    if hard_wechat and not hard_mini:
        if req.wechat_workflow == "unknown":
            required["wechat_workflow_unconfirmed"] = True
            questions.append("微信打印必须采用哪种方式：微信小程序直接打印，还是文件转存到厂商App后打印？")
        else:
            required["wechat_miniprogram" if req.wechat_workflow == "miniprogram" else "wechat_transfer_to_app"] = True
    elif want_wechat and not hard_wechat and req.wechat_required is not False:
        preferred["wechat_miniprogram"] = True
        preferred["wireless"] = True
    for name, feature in (("requires_wireless", "wireless"), ("requires_scan", "scan"),
                          ("requires_auto_duplex", "auto_duplex")):
        if getattr(req, name) is False and required.get(feature):
            conflicts.append(f"原文{feature}硬要求与“不要求”确认冲突，请修改原话或确认项")
    for index, text in enumerate(dict.fromkeys(unresolved), 1):
        required[f"unresolved_hard_condition_{index}"] = True
        questions.append("请逐项确认未识别硬要求：" + text)
    if req.budget_max_cny is not None and req.budget_scope == "unknown":
        questions.append("预算上限指主机含运费及必要支出，还是还要包括本次额外购买的耗材？")
    if not req.delivery_region:
        questions.append("请确认收货地区（省市区即可，不需要详细地址），用于核对库存和运费")
    return {"required": required, "preferred": preferred,
            "unresolved_hard_conditions": list(dict.fromkeys(unresolved)),
            "questions": list(dict.fromkeys(questions)), "conflicts": list(dict.fromkeys(conflicts))}
