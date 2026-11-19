"""固定旧厂家摘要的最小研究通路；仅生成有限研究比较，不批准购物。

用户只能选择冻结的证据包 ID，不能用上下文传入事实、文件路径、来源或批准状态。
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .contracts import PurchaseRequest
from .printer_conditions import printer_conditions

REGISTRY = Path(__file__).resolve().parent.parent / "knowledge/printer_minimal_evidence_packs.json"
REGISTRY_SHA256 = "d6468dfde182dfb86536629f8ae468372b6cb02fe7cd403975bad0b3cf6a7e0a"
CASE_ID = "PRINTER-HENAN-FAMILY-20261116"
MODEL_NAMES = {"HL-L1238W": "Brother HL-L1238W", "M232dw": "HP M232dw"}
UNKNOWN = ("wechat_reuse", "live_price", "long_term_reliability")


def selected_pack(context: dict) -> tuple[str, dict]:
    if (not isinstance(context, dict) or set(context) !=
            {"case_id", "input_basis", "evidence_pack_id"}
            or context.get("case_id") != CASE_ID
            or context.get("input_basis") != "project_owner_proxy"):
        raise ValueError("unapproved_minimal_research_context")
    pack_id = context.get("evidence_pack_id")
    if type(pack_id) is not str or pack_id not in ("setup_two", "setup_one", "setup_empty"):
        raise ValueError("unsupported_minimal_evidence_pack")
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError("minimal_evidence_registry_changed")
    data = json.loads(raw)
    if data.get("scope") != "printer_minimal_evidence_walkthrough":
        raise ValueError("invalid_minimal_evidence_scope")
    pack = data["packs"][pack_id]
    if (pack.get("allowed_use") != "local_source_attributed_model_research_only"
            or pack.get("new_external_fact_count") != 0
            or pack.get("purchase_recommendation_approved") is not False
            or pack.get("transactions_enabled") is not False):
        raise ValueError("unsafe_minimal_evidence_pack")
    for claim in pack["claims"]:
        if (claim.get("model_id") not in MODEL_NAMES
                or claim.get("supports_only") != ["initial_setup"]
                or any(source not in pack["sources"] for source in claim.get("source_ids", []))):
            raise ValueError("invalid_minimal_model_source_binding")
    return pack_id, deepcopy(pack)


def build_research_case(values: dict, context: dict) -> dict:
    """从当前明确需求、*所选*旧事实生成有限比较；无证据也返回未知与下一行动。"""
    if not isinstance(values, dict) or values.get("category") != "printer":
        raise ValueError("minimal_research_printer_only")
    pack_id, pack = selected_pack(context)
    # 复用已有需求冲突识别；没有替用户确认微信硬性程度。
    requirements = values.get("requirements") or []
    if not isinstance(requirements, (list, tuple)):
        requirements = []
    req = PurchaseRequest(
        category="printer",
        budget_max_cny=values.get("budget_max_cny"),
        needs_color=values.get("needs_color"),
        accepts_outsourced_color=values.get("accepts_outsourced_color"),
        wechat_required=values.get("wechat_required"),
        wechat_workflow=values.get("wechat_workflow", "unknown"),
        requires_scan=values.get("requires_scan"),
        requires_auto_duplex=values.get("requires_auto_duplex"),
        requires_wireless=values.get("requires_wireless"),
        delivery_region=values.get("delivery_region"),
        budget_scope=values.get("budget_scope", "unknown"),
        requirements=tuple(x for x in requirements if isinstance(x, str)),
    )
    condition = printer_conditions(req)
    conflict = list(condition["conflicts"])
    if values.get("accepts_initial_setup") is False:
        conflict.append("已明确拒绝首次App/扫码设置；现有资料只描述首次设置流程，不能按已满足处理")
    from .selection_criteria import classify_device_deployment_region
    # 原条件识别器已经同时识别结构化确认、原话硬要求与未解析硬要求。
    # 本次选包只有initial_setup依据；其他必需功能不能用该事实冒充支持。
    required = condition["required"]
    hard_features = [name for name, flag in required.items()
                     if flag is True and name != "monochrome_print"]
    unresolved_hard = condition["unresolved_hard_conditions"]
    extra_hard_unknown = bool(hard_features or unresolved_hard)
    wechat_is_hard = (values.get("wechat_required") is True or
                      any(required.get(name) for name in
                          ("wechat_miniprogram", "wechat_transfer_to_app",
                           "wechat_workflow_unconfirmed")))
    outside_scope = (values.get("device_deployment_region") is not None and
                     classify_device_deployment_region(values.get("device_deployment_region")) != "mainland_china")
    candidates = []
    for model_id, name in MODEL_NAMES.items():
        facts = [row for row in pack["claims"] if row["model_id"] == model_id]
        supported_ids = [row["id"] for row in facts]
        status = ("pending_evidence" if not facts or conflict or extra_hard_unknown or outside_scope
                  else "keep_for_research")
        if facts:
            reason = ("本次所选资料只支持首次设置步骤研究；" +
                      "；".join(f"{x['statement']}（反证/限制：{x['counter']}；"
                               f"观察日期：{x['observed_on']}；范围：{x['scope']}）" for x in facts))
        else:
            reason = "本次所选资料包没有该型号可用的首次设置依据；保持待核，不等于不支持或已支持。"
        if conflict:
            reason = "本次条件存在冲突或明确拒绝首次设置，先解决相应硬条件；" + reason
        if extra_hard_unknown:
            display = {
                "scan": "扫描", "auto_duplex": "自动双面", "wireless": "无线打印",
                "color_print": "彩印", "wechat_miniprogram": "微信小程序直接打印",
                "wechat_transfer_to_app": "微信转App打印",
                "wechat_workflow_unconfirmed": "微信打印方式待核",
            }
            named = [display.get(feature, feature) for feature in hard_features]
            reason = ("本次明确的必须功能仍缺选包证据（" + "、".join(named + unresolved_hard)
                      + "），不能据首次设置说明认定已满足；" + reason)
        if outside_scope:
            reason = "实际使用地区尚未证实处于本包中国大陆适用范围，不能跨地区推断可用；" + reason
        candidates.append({
            "model_id": model_id,
            "supported_claim_ids": supported_ids,
            "research_status": status,
            "reason": reason,
            "positive_evidence": [x["statement"] for x in facts],
            "counter_evidence": [x["counter"] for x in facts] if facts else
                                ["缺少本次选定资料，不能作支持或不支持的断言"],
            "unknown_fields": list(UNKNOWN) + ["required_" + name for name in hard_features]
                              + (["unresolved_hard_condition"] if unresolved_hard else []),
        })

    if not wechat_is_hard and values.get("wechat_required") is None:
        wechat_part = "微信是否必须仍是未答目标：若必须，先核准确型号的后续微信复用；若只是偏好，可继续有限型号研究。两种情况均不能当成本人新确认。"
    elif wechat_is_hard:
        wechat_part = "现有明确条件包含微信打印必须项：优先核准确型号要求的方式与第二次微信打印证据，首次设置说明不能证明复用；无需重复询问微信是否必须。"
    else:
        wechat_part = "微信非必须：可继续已有资料能支持的型号研究，但不能宣称其他App方式已经实测成功。"
    source_part = "；".join(
        f"{sid}：{row['url']}（核查{row['checked_on']}，局限：{row['limit']}）"
        for sid, row in pack["sources"].items()
    ) or "无，本次选包没有可用型号来源"
    model_part = "\n".join(
        f"{MODEL_NAMES[x['model_id']]}：{x['reason']} "
        f"仅有研究状态{('待核' if x['research_status']=='pending_evidence' else '保留研究')}。"
        for x in candidates
    )
    budget = values.get("budget_max_cny")
    budget_text = f"{budget}元" if type(budget) is int else "未知"
    volume = values.get("monthly_pages_range")
    volume_text = (f"{volume[0]}—{volume[1]}页" if isinstance(volume, (tuple, list)) and len(volume) == 2
                   else "未知")
    color_text = ("必须在家彩印" if values.get("needs_color") is True else
                  "黑白为主" if values.get("needs_color") is False else "彩印需求未答")
    setup_text = ("接受" if values.get("accepts_initial_setup") is True else
                  "不接受" if values.get("accepts_initial_setup") is False else "尚未确认")
    header = ("家庭打印机有限研究（负责人代理输入，不是亲戚本人回答或设备试验）："
              f"本轮预算上限{budget_text}，月印量{volume_text}，{color_text}；"
              f"首次App/扫码设置：{setup_text}。")
    warning = ("本次证据包：" + pack_id + "，其中"
               + str(len(pack["claims"])) + "条旧厂家摘要；没有新增外部取证。")
    boundary = ("不能由厂家初次设置指南推断微信二次复用、长期稳定、现货与河南实时到手价，"
                "预算上限不代表成交价符合；不能判断哪款更好，也不批准加购、下单或付款。")
    if conflict:
        caution = "已有冲突或明确拒绝设置，先向需求提出者确认：" + "；".join(conflict) + "。"
    elif extra_hard_unknown:
        caution = ("明确硬要求尚无本次选包依据，先逐型号核证而不判支持："
                   + "；".join(unresolved_hard or hard_features) + "。其他已知研究仍可继续。")
    else:
        caution = "当前可继续作有限研究，不必因为价格、微信二次复用或用户反馈缺席而停下全部研究。"
    report_text = ("\n".join((header, warning, model_part, wechat_part, caution,
                              "本次选定来源：" + source_part, boundary,
                              "实际使用者反馈尚未取得；可以准备问题，但不代填或外发。")))
    next_actions = [
        {"action": "clarify_wechat_requirement" if not wechat_is_hard and values.get("wechat_required") is None else "verify_wechat_reuse_if_needed",
         "owner_role": "需求提出者或自愿参与的设备持有人",
         "exact_item": ("已明确微信为硬条件，核具体微信路径及第二次打印条件（不收集账号密码）"
                        if wechat_is_hard else "确认微信打印是否必须；如必须，向厂家核型号并由设备持有人自愿记录第二次打印条件（不收集账号密码）")},
        {"action": "verify_remaining_product_facts",
         "owner_role": "研究执行者/厂家官方支持",
         "exact_item": "按两款分别补本次没有的型号事实；购买前另向销售方核所售型号、河南实时报价、运费和耗材"},
    ]
    if unresolved_hard:
        next_actions.append({
            "action": "verify_unresolved_hard_capability",
            "owner_role": "研究执行者/厂家官方支持",
            "exact_item": "原话明确但本包尚无可用型号证据：" + "；".join(unresolved_hard)
                          + "；核对两款准确型号及适用范围，不要求重新表态，也不猜支持性",
        })
    return {
        "schema_version": 1,
        "case_id": CASE_ID,
        "input_basis": "project_owner_proxy",
        "flow_status": "research_delivered_with_limits",
        "evidence_pack_id": pack_id,
        "used_facts": deepcopy(pack["claims"]),
        "source_registry": deepcopy(pack["sources"]),
        "new_external_fact_count": 0,
        "processed_stages": ["requirements", "evidence", "comparison", "explanation"],
        "candidate_assessments": candidates,
        "condition_conflicts": conflict,
        "wechat_requirement_status": ("required" if wechat_is_hard else
                                      "optional" if values.get("wechat_required") is False
                                      else "unconfirmed"),
        "report_text": report_text,
        "feedback": {
            "status": "not_collected",
            "actual_response_count": 0,
            "questions_prepared_not_sent": [
                "微信打印是一定需要，还是有就更好？",
                "两款型号中哪些功能对日常打印最重要？",
                "您愿意以后自愿记录一次实际操作体验吗？",
            ],
        },
        "next_actions": next_actions,
        "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "wechat_reuse_verified": False,
        "live_price_verified": False,
        "long_term_reliability_verified": False,
        "real_user_effect_verified": False,
    }
