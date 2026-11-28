"""Two-model research pilot: typed claims, candidate eligibility and cost scenarios."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from .confirmed_comparison import publish_confirmed_comparison
from .evidence_comparison import digest
from .minimal_research import MODEL_NAMES
from .printer_reviewed_evidence import MAINLAND

PACK_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "printer_cognition_comparison_v1.json"
PACK_SHA256 = "8b288d33f55f94323534e00a6b2524fce6b58c04bde97c65c5fd8a51add64385"
DIMS = {"scan": "扫描", "auto_duplex": "自动双面", "manual_duplex": "手动双面",
        "laser_print": "激光打印", "wechat_miniprogram": "微信小程序功能",
        "color_print": "彩色打印"}
STATUS = {"met": "有资料支持", "failed": "有不满足的依据",
          "unknown": "缺少适用证据", "conflict": "证据冲突"}
HARD_FIELDS = {"scan": "requires_scan", "auto_duplex": "requires_auto_duplex",
               "color_print": "needs_color"}
COST_DIMS = {"starter_toner_yield": "随箱墨粉标称页数",
             "replacement_toner_yield": "替换墨粉标称页数",
             "drum_yield": "硒鼓标称页数"}
EXTRA_LABELS = {"wechat_reuse": "微信稳定复用", "wechat_transfer_to_app": "微信转App",
                "initial_setup_without_app_or_scan": "免首次App/扫码", "cost": "预算",
                "separate_drum": "鼓粉分离", "starter_included": "随箱附黑色硒鼓",
                "replacement_137a_x": "137A/137X替换硒鼓",
                 "replace_on_unacceptable_quality": "按打印质量更换耗材", **COST_DIMS}
LABELS = {**DIMS, **EXTRA_LABELS}


def load_pack():
    try:
        raw = PACK_PATH.read_bytes()
        if sha256(raw).hexdigest() != PACK_SHA256:
            return None
        pack = json.loads(raw)
        return pack if pack.get("schema_version") == 1 else None
    except (OSError, ValueError, TypeError):
        return None


MAX_SCENARIO_PAGES = 10_000_000
MAX_SCENARIO_MONTHS = 1200
MAX_SCENARIO_PRICE = 1_000_000_000

def _scenario_money(value):
    from .evidence_comparison import number
    amount = number(value)
    if amount < 0:
        raise ValueError("negative_cost")
    # Bound magnitude and significant fractional precision before arithmetic.
    if amount > MAX_SCENARIO_PRICE or amount.as_tuple().exponent < -6:
        raise ValueError("cost_input_out_of_range")
    return amount


def replacement_count(pages, starter, yield_pages):
    """Scenario arithmetic only, not a forecast or a price."""
    if any(type(x) is not int for x in (pages, starter, yield_pages)):
        raise ValueError("scenario integers required")
    if min(pages, starter) < 0 or yield_pages <= 0 or max(pages, starter, yield_pages) > MAX_SCENARIO_PAGES:
        raise ValueError("invalid scenario")
    return (max(0, pages - starter) + yield_pages - 1) // yield_pages


def lifecycle_cost(*, pages, hardware, starter, toner_yield, toner_price,
                   separate_drum, drum_yield=None, drum_price=None, maintenance=None,
                   months=None, currency=None, fee_scope=None, scenario_version=1,
                   drum_starter=None):
    """Calculate an explicit scenario, never turn missing inputs into zero."""
    from .evidence_comparison import number
    if type(pages) is not int or not 0 <= pages <= MAX_SCENARIO_PAGES:
        raise ValueError("invalid_pages")
    if months is not None and (type(months) is not int or not 1 <= months <= MAX_SCENARIO_MONTHS):
        raise ValueError("invalid_months")
    if currency is not None and (not isinstance(currency,str) or len(currency)!=3 or not currency.isupper()):
        raise ValueError("invalid_currency")
    if fee_scope is not None and fee_scope!="hardware_consumables_maintenance":
        raise ValueError("invalid_fee_scope")
    if type(scenario_version) is not int or scenario_version<=0:
        raise ValueError("invalid_scenario_version")
    if separate_drum is not None and type(separate_drum) is not bool:
        raise ValueError("invalid_drum_type")
    if any(x is None for x in (hardware, starter, toner_yield, toner_price,
                               separate_drum, maintenance)):
        return None
    values = [_scenario_money(v) for v in (hardware, toner_price, maintenance)]
    if min(values) < 0:
        raise ValueError("negative_cost")
    count = replacement_count(pages, starter, toner_yield)
    drum_count = 0
    drum_cost = number(0)
    if separate_drum:
        if drum_yield is None or drum_price is None:
            return None
        if type(drum_yield) is not int or drum_yield <= 0:
            raise ValueError("invalid_drum_yield")
        drum_cost = _scenario_money(drum_price)
        if drum_cost < 0:
            raise ValueError("negative_cost")
        # Scenario assumes a new included drum at the start.
        drum_count = replacement_count(pages, drum_yield if drum_starter is None else drum_starter, drum_yield)
    return {"toner_replacements":count,"drum_replacements":drum_count,
            "total":format(values[0]+count*values[1]+drum_count*drum_cost+values[2],"f"),
            "assumption_only":True,
            "comparison_basis":{"pages":pages,"months":months,"currency":currency,
                                "fee_scope":fee_scope,"scenario_version":scenario_version},
            "basis_status":"explicit" if None not in (months,currency,fee_scope) else "legacy_unscoped_fixture",
            "input_lineage":{"kind":"scenario_assumption","hardware":str(hardware),"starter":starter,
                             "toner_yield":toner_yield,"toner_price":str(toner_price),
                             "separate_drum":separate_drum,"drum_yield":drum_yield,
                             "drum_price":str(drum_price) if drum_price is not None else None,
                             "drum_starter":(drum_yield if drum_starter is None else drum_starter) if separate_drum else None,
                             "maintenance":str(maintenance)}}


def compare_lifecycle_costs(a,b):
    """No winner if a scenario has unresolved inputs; compare only like scenarios."""
    from .evidence_comparison import number
    if a is None or b is None:
        return "unknown"
    if not a.get("comparison_basis") or a["comparison_basis"] != b.get("comparison_basis"):
        return "incomparable"
    x,y=number(a["total"]),number(b["total"])
    return "a" if x<y else "b" if x>y else "tie"


def requirements(values):
    reqs = [{"id": "cognition:" + dim, "dimension": dim, "unit": "bool",
             "op": "eq", "value": True,
             "importance": "hard" if (values.get(HARD_FIELDS.get(dim, "")) is True or
                    (dim == "wechat_miniprogram" and values.get("wechat_required") is True
                     and values.get("wechat_workflow") == "miniprogram")) else "soft"}
            for dim in DIMS]
    for r in reqs:
        field = HARD_FIELDS.get(r["dimension"])
        if field and values.get(field) is False:
            r["research_relevant"] = False
        if r["dimension"] == "manual_duplex" and values.get("requires_auto_duplex") is False:
            r["research_relevant"] = False
    def add(dim, unit="bool", op="eq", value=True, hard=False):
        reqs.append({"id": "cognition:" + dim, "dimension": dim, "unit": unit,
                     "op": op, "value": value, "importance": "hard" if hard else "soft"})
    if values.get("wechat_required") is True:
        add("wechat_reuse", hard=True)
        if values.get("wechat_workflow") == "transfer_to_app":
            add("wechat_transfer_to_app", hard=True)
        if values.get("accepts_initial_setup") is False:
            add("initial_setup_without_app_or_scan", hard=True)
    if type(values.get("budget_max_cny")) is int:
        add("cost", "CNY", "lte", values["budget_max_cny"], True)
    for dim in ("separate_drum", "starter_included", "replacement_137a_x", "replace_on_unacceptable_quality"):
        add(dim)
    for dim in COST_DIMS:
        add(dim, "pages", "gte", 1)
    return reqs


def _cost_scenario(values, claims, facts):
    monthly = values["monthly_pages_range"]
    if not isinstance(monthly, list) or len(monthly) != 2 or any(type(n) is not int or n < 0 for n in monthly) or monthly[0] > monthly[1]:
        raise ValueError("invalid page range")
    pages = [n * 36 for n in monthly]
    result = {"months": 36, "assumption_only": True, "pages": pages, "models": {}}
    for model in MODEL_NAMES.values():
        row = {"starter": None, "replacement_yield": None, "drum_yield": None,
               "separate_drum": None, "starter_included": None, "replacement_137a_x": None,
               "replace_on_unacceptable_quality": None,
               "fact_ids": [], "example_replacements": None}
        for dim, name in (("starter_toner_yield", "starter"), ("replacement_toner_yield", "replacement_yield"),
                          ("drum_yield", "drum_yield"), ("separate_drum", "separate_drum"),
                          ("starter_included", "starter_included"), ("replacement_137a_x", "replacement_137a_x"),
                          ("replace_on_unacceptable_quality", "replace_on_unacceptable_quality")):
            c = claims[(model, dim)]
            if c["status"] != "met" or not c["supporting_fact_ids"]:
                continue
            f = facts[c["supporting_fact_ids"][0]]
            val = f["value"]
            if (dim not in COST_DIMS and val is True) or (dim in COST_DIMS and type(val) is int and val > 0):
                row[name] = val
                row["fact_ids"].extend(c["supporting_fact_ids"])
        y = row["replacement_yield"]
        if y:
            # Explicit starter assumptions isolate the effect of a missing box yield.
            row["example_replacements"] = [{"assumed_starter": s, "assumed_effective_yield": y,
                                             "at_max_pages": replacement_count(pages[1], s, y)}
                                            for s in (0, y)]
        result["models"][model] = row
    return result


def _decision(values, reqs, public, facts, deferred=()):
    claims = {(c["candidate_id"], c["dimension"]): c for c in public["claims"]}
    hard = [r["dimension"] for r in reqs if r["importance"] == "hard"]
    rows = []
    for a in public["assessments"]:
        model = a["candidate_id"]
        failed = [d for d in hard if claims[(model,d)]["status"] == "failed"]
        pending = [d for d in hard if claims[(model,d)]["status"] in ("unknown","conflict")]
        supported = [d for d in hard if claims[(model,d)]["status"] == "met"]
        rows.append({"model": model, "state": a["research_status"], "failed": failed,
                     "pending": pending, "supported": supported,
                     "claim_ids": [claims[(model,d)]["claim_id"] for d in hard]})
    survivors = [r for r in rows if not r["failed"]]
    names = [r["model"] for r in survivors]
    action = {"kind": "stop", "field": None, "candidates": [], "dimension": None,
              "text": "原两款均有硬性反证，结束本轮两款比较；调整需求或另找候选。"}
    if survivors:
        for dim in ("color_print","scan","auto_duplex","initial_setup_without_app_or_scan","wechat_transfer_to_app","wechat_miniprogram","wechat_reuse"):
            targets = [r["model"] for r in survivors if dim in r["pending"]]
            if targets:
                text = "核" + "、".join(targets) + "的" + LABELS[dim] + "；若证实满足则继续研究，若证实不满足则排除相应候选，缺证仍待核。"
                action = {"kind": "research", "field": None, "candidates": targets, "dimension": dim, "text": text}
                break
        else:
            action = {"kind": "research", "field": None, "candidates": names, "dimension": "cost",
                      "text": "核" + "、".join(names) + "的实际随箱耗材量及同配置耗材价格；若成本优势足以抵消主机差价则优先该款，否则继续比较另一款。"}
    # Both consumers receive the same policy before ranking.
    if public["next_actions"] and public["next_actions"][0]["kind"] == "clarify":
        first = public["next_actions"][0]
        dim = next(r["dimension"] for r in reqs if r["id"] == first["requirement_id"])
        action = {"kind":"clarify","field":HARD_FIELDS[dim],"candidates":names,
                  "dimension":dim,"text":first["description"]}
    elif public["next_actions"] and public["next_actions"][0]["kind"]=="confirm_cost_assumption":
        first=public["next_actions"][0]
        action={"kind":"confirm_cost_assumption","field":None,"candidates":[first["candidate_id"]],
                "dimension":"cost","text":first["description"], **({"scenario_field":first["scenario_field"]} if "scenario_field" in first else {})}
    elif public["next_actions"]:
        first = public["next_actions"][0]
        dim = next(r["dimension"] for r in reqs if r["id"] == first["requirement_id"])
        targets = list(dict.fromkeys(a["candidate_id"] for a in public["next_actions"]
                                     if a["requirement_id"] == first["requirement_id"]))
        if dim == "cost":
            text = "核" + "、".join(targets) + "的实际硬件报价及同配置耗材成本；若硬件超预算则排除，否则继续比较。"
        else:
            text = "核" + "、".join(targets) + "的" + LABELS.get(dim, dim) + "；若证实满足则继续研究，若证实不满足则按当前硬要求筛选，缺证仍待核。"
        action = {"kind": "research", "field": None, "candidates": targets,
                  "dimension": dim, "text": text}
    elif survivors:
        action = {"kind": "wait", "field": None, "candidates": names, "dimension": None,
                  "text": "现有条件已核至当前资料边界；等待新的有效证据，不自动批准购买。"}
    return {"candidates": rows, "next_action": action, "cost_scenario": _cost_scenario(values, claims, facts)}


def compare(values, version, today, *, deferred=(), withdrawn=(), ranking_route=None,
            ranking_transport=None, ranking_budget=None, cost_scenario=None):
    if (values.get("category") != "printer" or "usage" not in values
            or "monthly_pages_range" not in values or "needs_color" not in values
            or values.get("device_deployment_region") not in MAINLAND):
        return None
    pack = load_pack()
    if pack is None:
        return None
    region = values["device_deployment_region"]
    reqs = requirements(values)
    try:
        sources, facts = deepcopy(pack["sources"]), deepcopy(pack["facts"])
        for row in sources + facts:
            if row.get("scope_region") == "中国大陆":
                row["scope_region"] = region
        # No sale quote is part of this local pack. Price remains unknown.
        facts = [f for f in facts if f["dimension"] != "cost"]
        bundle = {"schema_version": 1, "request_id": "printer-cognition-pilot",
                  "category": "printer", "dialogue_version": version,
                  "confirmed_values_sha256": digest(values), "as_of": today.isoformat(),
                  "region": region, "candidates": [{"id": m} for m in MODEL_NAMES.values()],
                  "requirements": reqs, "sources": sources, "facts": facts}
        public = publish_confirmed_comparison(bundle, reqs, as_of=today.isoformat(),
                                               deployment_region=region, session_values=values, deferred=deferred, withdrawn=withdrawn)
        if not public:
            return None
        from .cost_scenario import bind_cost
        bind_cost(public, cost_scenario)
        fact_map = {f["id"]: f for f in facts}
        decision = _decision(values, reqs, public, fact_map, deferred)
        from .action_ranking import rank_actions
        from .cognition_guide import project
        cognition_context = json.loads(project(values, {"public_decision":public}, as_of=today, deferred=deferred, withdrawn=withdrawn, state_version=version)["cognition_context_json"])
        ranked, audit = rank_actions(public, ranking_route, ranking_transport,
                                     cognition_context=cognition_context,
                                     **(ranking_budget or {}))
        if audit["business_accepted"]:
            public["next_actions"] = ranked
            decision = _decision(values, reqs, public, fact_map, deferred)
        return {"public": public, "sources": sources, "facts": facts, "decision": decision,
                "bundle": bundle, "ranking_audit": audit}
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return None


def render(result, values):
    if not result:
        return ""
    public = result["public"]
    decision = result["decision"]
    sources = {s["id"]: s for s in result["sources"]}
    facts = {f["id"]: f for f in result["facts"]}
    claims = {(c["candidate_id"], c["dimension"]): c for c in public["claims"]}
    survivors = [r["model"] for r in decision["candidates"] if not r["failed"]]
    lines = ["品类认知与条件化比较（部分厂家资料已独立复证，其余仍待复核）："]
    if not survivors:
        lines.append("整体取舍：原两款均有硬性反证，均不适用；不在两款间挑胜者。")
    elif len(survivors) == 1:
        lines.append("整体取舍：仅" + survivors[0] + "保留研究资格；其余硬条件仍须按证据核对，不等于可购买。")
    else:
        lines.append("整体取舍：暂不选冠军；先满足硬条件，再以低频耗材、维护成本与主机差价比较。")
    if values.get("needs_color") is True:
        lines.append("当前要求在家彩印：硬性反证不能由扫描或其他功能抵消。")
    elif values.get("accepts_outsourced_color") is True:
        lines.append("彩印可外包：额外彩印功能不是当前必要条件。")
    else:
        lines.append("彩印替代方式仍需按实际需求判断。")
    for row in decision["candidates"]:
        model = row["model"]
        label = {"excluded_for_research": "硬条件不满足，退出优先研究",
                 "pending_evidence": "待核，保留研究资格",
                 "eligible_for_research": "现有硬条件研究层面满足"}[row["state"]]
        lines.append(model + "：" + label + "。")
        for name, key in (("反证", "failed"), ("待核", "pending"), ("有据硬条件", "supported")):
            if row[key]:
                lines.append("  " + name + "：" + "、".join(LABELS[d] for d in row[key]) + "。")
        for dim, label in DIMS.items():
            c = claims[(model, dim)]
            lines.append(f"  {label}：{STATUS[c['status']]}。")
            for fid in c["supporting_fact_ids"]:
                source = sources[facts[fid]["source_id"]]
                lines.append(f"    来源 {source['url']}；获取 {source['captured_on']}；本地复核期限 {source['valid_until']}。")
    for field, dim in (("requires_scan", "scan"), ("requires_auto_duplex", "auto_duplex")):
        label = DIMS[dim]
        required = values.get(field)
        supported = [m for m in survivors if claims[(m, dim)]["status"] == "met"]
        prefix = ("当前" + label + "是硬要求" if required is True else
                  "当前不要求" + label if required is False else "若需要" + label)
        if supported and required is not False:
            lines.append(prefix + "：" + "、".join(supported) + "在该维度有依据，可优先核查；不代表另一款不支持或整体可买。")
        elif required is False:
            lines.append(prefix + "：该额外功能不构成当前选型必要性。")
        else:
            lines.append(prefix + "：缺足够证据，暂不能据此选择。")
    cost = decision["cost_scenario"]
    lines.append("低频维护与总成本（3年情景，非本人确认年限或设备寿命）："
                 + str(cost["pages"][0]) + "–" + str(cost["pages"][1]) + "页。")
    lines.append("成本=主机H+替换耗材数量×耗材单价P+仅鼓粉分离时另换硒鼓数量×鼓价D+维护M；"
                 "替换墨粉数量=向上取整(max(0,打印页数−随箱可用页数)/实际替换产量)。"
                 "各项实际售价、实际产量、闲置维护与故障成本未知，不能比较耐用排名。")
    for model in survivors:
        row = cost["models"][model]
        known = [LABELS[d] + " " + str(row[k]) for d,k in (
            ("starter_toner_yield","starter"), ("replacement_toner_yield","replacement_yield"),
            ("drum_yield","drum_yield")) if row[k] is not None]
        if row["separate_drum"]:
            known.insert(0,"鼓粉分离，墨粉用完不等同更换硒鼓")
        if row["starter_included"]:
            known.append("随箱附黑色硒鼓（页数未知）")
        if row["replacement_137a_x"]:
            known.append("137A/137X替换硒鼓（具体产量及价格待核）")
        if row["replace_on_unacceptable_quality"]:
            known.append("厂商指南允许耗材低告警后按打印质量决定更换；严重不足后耗材高级保护保修终止")
            lines.append(model + "维护条件：不能仅因低告警就计入一次更换成本；"
                         "若质量不可接受则计入实际替换件，剩余产量、频率和费用仍待核。")
        lines.append(model + "耗材：" + ("；".join(known) if known else "所售套装与标称产量待核") + "；随箱量和实际维护/价格仍需按配置核对。")
        for fid in row["fact_ids"]:
            source = sources[facts[fid]["source_id"]]
            lines.append("  耗材依据 " + fid + "：" + source["url"] + "；获取 " + source["captured_on"] + "。")
        if row["example_replacements"]:
            a,b = row["example_replacements"]
            lines.append(f"  仅作情景：按{cost['pages'][1]}页、假设实际替换产量{a['assumed_effective_yield']}页；"
                         f"若随箱为0页则需{a['at_max_pages']}盒，若随箱为{b['assumed_starter']}页则需{b['at_max_pages']}盒。"
                         "标称量不等于家庭实际量；此处未假定实际随箱量。")
    if len(survivors) > 1:
        lines.append("翻转条件：若兄弟的主机差价节省大于其相对多出的耗材及维护成本，且硬要求均满足，则优先兄弟；反向则优先惠普；相等或缺值则暂平局。")
    if type(values.get("budget_max_cny")) is int:
        lines.append(f"预算上限为{values['budget_max_cny']}元；两款应付价未知，不能据历史建议价淘汰。收货区县只限制适用报价。")
    from .cost_scenario import render_cost
    lines.append(render_cost(public.get("cost_comparison")))
    lines.append("下一项高价值核查：" + decision["next_action"]["text"])
    lines.append("没有证明低频耐用排名、真实价格或真人收益；未批准购买，交易关闭。")
    return "\n".join(lines)
