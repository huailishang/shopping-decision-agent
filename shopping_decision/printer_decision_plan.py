"""在已审厂家研究快照上给出条件化行动，不增加商品事实或购买权限。"""
from __future__ import annotations

from copy import deepcopy

_MODEL_IDS = ("HL-L1238W", "M232dw")
_SOURCE_IDS = ("R7", "R10")


def build_printer_decision_plan(values: dict, snapshot: dict, *, conflicts: list | None = None) -> dict | None:
    """仅对本案两款且来源仍可映射的型号产生研究路径；不推断实机复用。"""
    if values.get("category") != "printer":
        return None
    models = snapshot.get("all_candidates", [])
    sources = snapshot.get("source_registry", {})
    if not all(any(row.get("model_id") == mid for row in models) for mid in _MODEL_IDS):
        return None
    if not all(isinstance(sources.get(sid), dict) and
               all(sources[sid].get(k) for k in ("url", "checked_on", "limit"))
               for sid in _SOURCE_IDS):
        # 来源缺失时拒绝伪造来源绑定；其他研究字段及安全门禁不变。
        return None

    requirement = values.get("wechat_required")
    conflicting = bool(conflicts)
    if conflicting:
        current_path = "resolve_user_condition_conflict"
    elif requirement is True:
        current_path = "verify_wechat_reuse"
    elif requirement is False:
        current_path = "continue_model_research"
    else:
        current_path = "clarify_wechat_requirement"

    def item(needed: bool) -> dict:
        if needed:
            return {
                "when": {"wechat_required": True},
                "basis": "hypothetical_not_user_confirmation",
                "candidate_model_ids": list(_MODEL_IDS),
                "source_ids": list(_SOURCE_IDS),
                "state": "pending_reuse_evidence",
                "explanation": "微信为硬条件时，现有中国区厂家初次配置资料只能支持核实路径，不能证明两款准确型号在亲戚设备上隔次微信复用成功；两款均暂留研究。",
                "limitations": "Brother的旧配置流程不等于实机复用；HP为系列安装指南，未绑定所售配置；一次成功也不能证明长期稳定。",
                "next_step": {
                    "action": "verify_wechat_reuse",
                    "owner_role": "厂家官方支持或自愿提供记录的设备持有者",
                    "exact_item": "逐型号确认中国大陆河南实际使用环境、首次配置后断开再连接的微信小程序第二次打印路径；如有自愿实测，记准确型号/配置、时间、网络、步骤、成功与失败，不收集账户凭证",
                    "blocks": "wechat_reuse_claim",
                },
            }
        return {
            "when": {"wechat_required": False},
            "basis": "hypothetical_not_user_confirmation",
            "candidate_model_ids": list(_MODEL_IDS),
            "source_ids": list(_SOURCE_IDS),
            "state": "research_can_continue",
            "explanation": "微信只是偏好时，可继续比较两款的已有规格、低频使用、耗材、售后与待核型号事实；缺微信复用证据只限制复用保证，不阻断全部型号研究。",
            "limitations": "不能因偏好下降便宣称厂商App已实测可用，也不能按建议价、未知可靠性或未核的平台商品配置排名与推荐购买。",
            "next_step": {
                "action": "continue_model_research",
                "owner_role": "研究执行者；涉及机型规格由厂家公开资料核对",
                "exact_item": "分别核对两款准确型号的低频使用/耗材与功能证据及其适用日期；逐条标出缺证据断言，不扩大到未经验证的App使用成功或到手价",
                "blocks": "specific_unverified_claim_only",
            },
        }

    branches = [item(True), item(False)]
    source_brief = "；".join(
        f"{sid}（核于{sources[sid]['checked_on']}，限制：{sources[sid]['limit']}）"
        for sid in _SOURCE_IDS)
    if conflicting:
        lead = "本轮存在互相冲突的明确条件，先请用户处理冲突，不能套用某一研究路径。"
    elif requirement is True:
        lead = "本轮输入把微信列为必须：先查准确型号后续微信复用证据；不重复追问微信是否必须。"
    elif requirement is False:
        lead = "本轮输入把微信列为可选：继续研究两款，微信未证不等于全部研究失败；不重复追问微信是否必须。"
    else:
        lead = "原代理样本尚未回答微信是否必须，必须先澄清此目标；以下两条只是条件假设，不代表亲戚的新答复。"
    text = (
        lead +
        "\n现有研究锚点：Brother HL-L1238W、HP M232dw，两款暂保留，不按未知功能、可靠性或价格选冠军。"
        "\n正面依据：已有中国区厂商微信/初次配置流程线索；来源：" + source_brief +
        "。反面限制：Brother流程和HP系列指南不证明实际在售型号后续微信复用、其他App可用、长期耐用或实时报价。"
        "\n若微信必须：由厂商官方支持或自愿测试的设备持有者逐型号提供首次设置后隔次打印的具体条件/最小记录；"
        "在核实前只暂停“后续微信复用已成功”的断言，不武断淘汰两款。"
        "\n若微信可选：研究执行者继续有据比较两款准确型号的低频印量、耗材和功能，"
        "把未核微信/其他App的说法保持未知，不让单条缺证据阻断其余研究。"
        "\n买前另核：预算是否含运费与另购耗材、实际收货地、销售方及所售配置身份、河南实时到手价；"
        "这是购买阶段事项，不代表已经符合1000元预算，更不批准加购、下单或付款。"
    )
    return {
        "schema_version": 1,
        "scope": "conditional_model_research",
        "current_path": current_path,
        "primary_question": ({
            "field": "wechat_required",
            "status": "unconfirmed",
            "question": "微信打印是必须条件，还是可选偏好？",
            "why": "答案决定应优先核实后续微信复用，还是可继续现有型号研究",
        } if requirement is None and not conflicting else None),
        "branches": deepcopy(branches),
        "purchase_checks": [
            {"field": "budget_scope", "stage": "purchase", "verified": False,
             "action": "核预算含运费/本次另购耗材的口径"},
            {"field": "delivery_region", "stage": "purchase", "verified": False,
             "action": "核实际收货地区，不以设备部署地代替"},
            {"field": "sale_identity", "stage": "purchase", "verified": False,
             "action": "核销售方及真实在售配置与准确型号绑定"},
            {"field": "live_price", "stage": "purchase", "verified": False,
             "action": "核河南有效地区实时到手价、运费和库存"},
        ],
        "reuse_verified": False,
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "text": text,
    }
