"""结构化约束检查。只对明确支持的中文短语做安全冲突检查，不假装完成语义理解。"""
from __future__ import annotations
from .contracts import PurchaseRequest, Recommendation

def validate_request(req: PurchaseRequest) -> Recommendation | None:
    for name in ("monthly_pages", "budget_max_cny", "idle_weeks"):
        n = getattr(req, name)
        if n is not None and (type(n) is not int or n < 0):
            return Recommendation("invalid", None, (f"{name} 必须是非负整数",))
    for name in ("needs_color", "accepts_outsourced_color", "requires_wireless", "requires_scan"):
        v = getattr(req, name)
        if v is not None and type(v) is not bool:
            return Recommendation("invalid", None, (f"{name} 必须是布尔值",))
    if not isinstance(req.requirements, tuple) or any(not isinstance(s,str) for s in req.requirements):
        return Recommendation("invalid", None, ("requirements 必须是文本元组",))
    terms = "；".join(req.requirements)
    must_home_color = any(s in terms for s in ("必须在家彩印", "必须在家打印彩色", "必须家用彩印", "必须彩色"))
    no_color = any(s in terms for s in ("不需要彩色", "不能彩印", "只打黑白"))
    if (req.needs_color is False and must_home_color) or (req.needs_color is True and no_color):
        return Recommendation("clarify", None, ("颜色要求与明确的文字硬约束冲突，先澄清，不能推荐黑白机。",),questions=("是否必须在家彩印？还是只打印黑白？",))
    if req.accepts_outsourced_color is True and must_home_color:
        return Recommendation("clarify", None, ("同时声明必须在家彩印、可以外包彩印，需明确是否接受全部彩印外包。",),questions=("彩印必须在家完成吗？",))
    if req.category != "printer":
        return Recommendation("unsupported", None, ("本阶段只支持家用打印机。",))
    return None
