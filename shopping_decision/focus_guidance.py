"""One deterministic, user-owned current question; no inferred answers or purchase permission."""

import re

# Topic detection is only for choosing a question. It never writes an answer.
# Keep the old topic order as the deterministic tie-breaker.
_TOPIC_RULES = (
    (r"扫描|存档|复印|(?:转|变|做|弄|扫)成.{0,12}(?:电子|电脑文件|PDF|数字)|(?:纸质|纸本|纸张|照片|证件|手写).{0,22}(?:电子文件|电子版|PDF|电脑文件|数字化)",
     ("requires_scan", "needs_color", "device_deployment_region", "monthly_pages_range")),
    (r"双面|翻面|翻纸|(?:正反|两面|两边).{0,14}(?:印|处理|机器)|(?:机器|自动|自己).{0,8}(?:翻|处理).{0,5}纸",
     ("requires_auto_duplex", "needs_color", "device_deployment_region", "monthly_pages_range")),
    (r"闲置|多周不用|每周|隔多久|使用间隔|(?:几|一两|两三|[一二三四五六七八九十两0-9]+)(?:个)?月.{0,8}(?:不动|不用|才|回来)|(?:放|收|搁).{0,12}(?:到|等).{0,8}(?:才用|再用|再印)|(?:暑假|寒假).{0,22}(?:寒假|暑假).{0,8}(?:才|再)|隔.{0,8}(?:周|月).{0,8}(?:打|用)",
     ("idle_weeks_pattern",)),
    (r"主机|预算范围|包括耗材|算预算|(?:机器|硬件|预算|费用|钱).{0,22}耗材|耗材.{0,15}(?:另算|预算|费用|一起)",
     ("budget_scope",)),
    (r"低印量|页数|暂时没有要打印|(?:没|没有|暂无).{0,8}打印任务|(?:每月|一个月|月均).{0,12}(?:张|页)",
     ("monthly_pages_range",)),
    (r"微信|小程序", ("wechat_required", "accepts_initial_setup", "wechat_workflow", "device_deployment_region")),
    (r"外包|打印店|(?:店里|店外).{0,8}(?:打|印)|彩色.{0,10}(?:外面|店里)", ("needs_color", "accepts_outsourced_color")),
)
# A topic mentioned only in a rejected/uncertain clause is lower priority than
# an affirmative competing purpose. A lone negative still merits confirmation.
_NEG_PREFIX = re.compile(r"(?:不用|不需要|无需|不必|不想|不要|不考虑|不是|并非|不在意|没必要|不打算|不要求)\s*$")
_UNCLEAR_SUFFIX = re.compile(r"^(?:还)?(?:不清楚|不确定|没想好|未知)")
_EMPHASIS = re.compile(r"主要|最在意|重点|更在意|只想|必须|真正想")


def _topic_order(usage):
    scores = {}
    # An interval can span clauses: put away/leave now, resume at a later
    # season or after a stated duration. Keep this separate from page volume.
    if re.search(r"(?:放|收|搁).{0,16}[，,].{0,12}(?:才|再)(?:用|打|印)|(?:出差|离开|外出|放假|旅行).{0,12}(?:周|月)[，,].{0,12}(?:才|再)(?:用|打|印)|(?:暑假|寒假).{0,24}(?:寒假|暑假).{0,8}(?:才|再)(?:用|打|印)", usage):
        scores[2] = 1
    for clause in re.split(r"[，,。；;！？!?]|(?:但是|而是|不过)", usage):
        for i, (pattern, _) in enumerate(_TOPIC_RULES):
            for match in re.finditer(pattern, clause, re.I):
                before, after = clause[:match.start()], clause[match.end():]
                negated = bool(_NEG_PREFIX.search(before) or _UNCLEAR_SUFFIX.match(after))
                # A contrast within a clause may contain a second, affirmed topic.
                score = 0 if negated else 2 if _EMPHASIS.search(before) else 1
                scores[i] = max(scores.get(i, -1), score)
    # Suppress rejected topics only if a competing positive topic exists.
    positive = any(score > 0 for score in scores.values())
    return sorted((i for i in scores if not positive or scores[i] > 0), key=lambda i: (-scores[i], i))


def choose_field(values, deferred, withdrawn, active, *, comparison_ready=False):
    """Prioritize stated purpose; never confirm a preference from free text."""
    blocked=set(values)|set(deferred)|set(withdrawn)
    if values.get("category")!="printer" or "usage" not in values or comparison_ready:
        return active
    if values.get("needs_color") is True:
        return ""
    for i in _topic_order(values["usage"]):
        for f in _TOPIC_RULES[i][1]:
            if f in blocked:continue
            if f=="accepts_outsourced_color" and values.get("needs_color") is not False:continue
            if f=="wechat_workflow" and values.get("wechat_required") is not True:continue
            if f=="accepts_initial_setup" and values.get("wechat_required") is False:continue
            return f
    return active if active not in blocked else ""

def build_focus(values, state, guide, field, prompt):
    if not guide:
        return dict(schema_version=1,guide_id=None,guide_version=None,state_version=state["version"],
                    status="unsupported",field=None,question="当前品类暂无认知指南。",
                    explanation="仍可使用普通需求整理入口。",basis_kind="unknown",claim_ids=[],source_ids=[],
                    if_unknown="暂不形成专业判断。",effect_if_yes="",effect_if_no="",next_step="先确认品类。",
                    purchase_recommendation_approved=False,transactions_enabled=False)
    usage=values.get("usage","")
    rows={
        "usage":("先了解实际使用目的，之后再判断哪些参数有必要。","说明生活中的任务。","保留用途未知，不代填。",""),
        "needs_color":("是否必须在家打印彩色，直接决定黑白机器是否适用。","必须彩印：排除黑白路线，继续核彩色方案。","黑白可考虑，偶尔彩印是否外包仍由你决定。",""),
        "requires_scan":("你是否需要把纸质资料变成电子文件？打印与扫描是两个不同功能。","扫描成为硬要求，逐型号核功能。","不将扫描列为淘汰条件。","guide-functions"),
        "requires_auto_duplex":("先确认是否必须由机器自动翻面；手动翻面不能当自动双面。","自动双面列为硬要求，按型号核实。","可手动翻面，不以自动双面作为淘汰条件。","guide-functions"),
        "idle_weeks_pattern":("使用间隔是本人场景，决定下一步应核哪种恢复和维护条件；不由印量推断。","多周不用：核恢复步骤、清洁耗材及维护条件。","通常每周使用：核同条件维护和耗材更换口径。","guide-cost-method"),
        "accepts_outsourced_color":("如果家中不必须彩印，可以把偶尔彩印和日常黑白分开考虑。","外包可列为选项，费用及可达性仍待核。","不把外包视为可接受替代。",""),
        "wechat_required":("微信打印是否必须，决定能否用其他打印方式替代。","作为硬要求，继续核具体微信流程。","作为偏好，不因此直接淘汰。",""),
        "accepts_initial_setup":("先确认能否接受首次安装或扫码；这与以后能否微信打印是两件事。","继续核实际首次设置及后续复用流程。","免首次设置是硬条件，必须单独核实。",""),
        "wechat_workflow":("微信小程序直打与文件转存厂商App不是同一要求。","按本人明确方式核型号和实际流程。","未知时不把两种方式混同。",""),
        "device_deployment_region":("使用地决定哪些地区的型号和流程材料可以适用。","按明确使用地核查资料适用性。","未知时保留地区相关事实待核。",""),
        "monthly_pages_range":("月页数只描述预期工作量；不能据此猜闲置时间或实际耗材产量。","按明确范围研究耗材情景，保留实际产量未知。","未知时不代填数字。",""),
        "budget_max_cny":("预算限制可缩小范围，但未取得有效报价不能判断是否买得起。","按上限核相同口径的报价。","暂不按价格淘汰。",""),
        "budget_scope":("主机费用与耗材、运费的口径不同；先确认你希望预算覆盖什么。","仅主机预算只核硬件价，其他支出另列。","含其他费用时按完整配置与相同口径核价。",""),
        "delivery_region":("收货地与设备使用地可能不同；核价前需要分别确认。","按收货地核报价适用范围。","未知则不声称报价有效。",""),
    }
    if field:
        explanation,yes,no,cid=rows.get(field,("先明确这个会影响当前比较的条件。","按明确条件继续。","按否定或其他明确选项重算。",""))
        if field=="needs_color":
            if "彩色" in usage or "照片" in usage:
                explanation="你提到彩色照片，先确认是否必须在家彩印；黑白机器不能完成彩印。"
            elif "黑白" in usage or "作业" in usage:
                explanation="你提到黑白作业，先确认彩色是否也是硬需求；不能仅凭用途替你决定。"
        claims=[c for c in guide["claims"] if c["id"]==cid and c["evidence_status"]=="supported" and c["source_ids"]]
        kind="supported_claim" if claims else "logical_constraint" if field in ("needs_color","budget_scope","accepts_outsourced_color","wechat_workflow") else "user_choice"
        if claims:
            explanation += " 依据："+claims[0]["text"]+" 限制："+claims[0]["exceptions"][0]+"。"
        elif cid:
            explanation+=" 当前专业依据待核，不据此推荐技术路线。"
            kind="unknown" if field=="idle_weeks_pattern" else "user_choice"
        unknown="可以暂不确定；保留这一条件为未知，不替你作答或据此淘汰候选。"
        step="本人提交、暂缓或展开完整指南；按明确答复重算。"
        status="ask"
    else:
        claims=[];kind="logical_constraint" if values.get("needs_color") is True else "unknown"
        explanation=("已确认必须在家彩印；现有两款黑白研究样本不适用。具体彩色方案仍需证据。"
                     if values.get("needs_color") is True else "当前应按已确认条件和实际证据缺口继续，不要求先填写未知数据。")
        yes=no="";unknown="缺失证据仍待核，不替用户确认，也不批准购买。";step=prompt;status="research" if values.get("needs_color") is True or "核" in prompt else "wait"
    return dict(schema_version=1,guide_id=guide["guide_id"],guide_version=guide["version"],state_version=state["version"],
                status=status,field=field or None,question=prompt,explanation=explanation,
                claim_ids=[c["id"] for c in claims],source_ids=sorted({x for c in claims for x in c["source_ids"]}),
                basis_kind=kind,if_unknown=unknown,effect_if_yes=yes,effect_if_no=no,next_step=step,
                purchase_recommendation_approved=False,transactions_enabled=False)


def public_focus(values, version, guide, public):
    """Bind the pre/post-ranking focus to a stable equal-priority action group.

    Ranking may reorder candidates inside this group, but cannot change the
    user's current question or the research dimension. The specific next action
    remains the authoritative candidate gate output.
    """
    if not public or not guide:
        return None
    actions=public.get("next_actions", [])
    reqs={r["id"]:r for r in public["decision_binding"]["requirements"]}
    state={"version":version}
    if actions:
        first=actions[0]
        dim=reqs[first["requirement_id"]]["dimension"]
        if first["kind"]=="clarify":
            field={"scan":"requires_scan","auto_duplex":"requires_auto_duplex","color_print":"needs_color"}.get(dim)
            if field and field not in values:
                from .chat_bridge import QUESTION
                return build_focus(values,state,guide,field,QUESTION[field])
        # Sorted candidate identities make the focus invariant under legal ranking.
        targets=sorted({a["candidate_id"] for a in actions if a["requirement_id"]==first["requirement_id"] and a["kind"]==first["kind"]})
        from .cognition_comparison import LABELS
        question="核"+"、".join(targets)+"的"+LABELS.get(dim,dim)+"；按当前证据确定下一步。"
        focus=build_focus(values,state,guide,"",question)
        focus.update(status="research",basis_kind="unknown",
                     explanation="先核当前同优先级的候选证据；满足则继续研究，反证则按已确认硬条件筛选，缺证保持待核。")
        return focus
    excluded=bool(public.get("assessments")) and all(x["research_status"]=="excluded_for_research" for x in public["assessments"])
    question="原候选均有硬性反证，结束本轮候选比较；调整需求或另找候选。" if excluded else "现有资料到达研究边界；等待新的有效证据。"
    focus=build_focus(values,state,guide,"",question)
    if excluded:
        focus.update(status="research",explanation="现有候选均有已准入的硬条件反证；不以软成本复活候选。")
    else:
        focus.update(status="wait",basis_kind="unknown",explanation="当前没有可继续的已准入行动；等待有效证据，不批准购买。")
    return focus
