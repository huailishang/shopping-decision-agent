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
PACK_SHA256 = "6e303e1cd0a85bfd1aca4302da2a0a88821f880c1e62ef098c2aa48ee873e7a6"
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
                "replacement_137a_x": "137A/137X替换硒鼓", **COST_DIMS}
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


def replacement_count(pages, starter, yield_pages):
    """Scenario arithmetic only, not a forecast or a price."""
    if any(type(x) is not int for x in (pages, starter, yield_pages)):
        raise ValueError("scenario integers required")
    if min(pages, starter) < 0 or yield_pages <= 0:
        raise ValueError("invalid scenario")
    return (max(0, pages - starter) + yield_pages - 1) // yield_pages


def requirements(values):
    reqs = [{"id": "cognition:" + dim, "dimension": dim, "unit": "bool",
             "op": "eq", "value": True,
             "importance": "hard" if (values.get(HARD_FIELDS.get(dim, "")) is True or
                    (dim == "wechat_miniprogram" and values.get("wechat_required") is True
                     and values.get("wechat_workflow") == "miniprogram")) else "soft"}
            for dim in DIMS]
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
    for dim in ("separate_drum", "starter_included", "replacement_137a_x"):
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
               "fact_ids": [], "example_replacements": None}
        for dim, name in (("starter_toner_yield", "starter"), ("replacement_toner_yield", "replacement_yield"),
                          ("drum_yield", "drum_yield"), ("separate_drum", "separate_drum"),
                          ("starter_included", "starter_included"), ("replacement_137a_x", "replacement_137a_x")):
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
        # An unanswered scan/duplex preference changes the decision before quoting.
        # A known hard-feature contradiction takes precedence over this question.
        if action["dimension"] in ("wechat_miniprogram", "wechat_reuse", "cost") and len(survivors) > 1:
            for field, dim in (("requires_scan","scan"), ("requires_auto_duplex","auto_duplex")):
                if field not in values and field not in deferred:
                    action = {"kind": "clarify", "field": field, "candidates": names, "dimension": dim,
                              "text": "确认是否必须" + DIMS[dim] + "；若必须则按有据能力筛选，若无需则不为该功能额外付费。"}
                    break
    # Remove actions that refer to excluded candidates, preserving the gate's claims.
    public["next_actions"] = [a for a in public["next_actions"] if a["candidate_id"] in names]
    return {"candidates": rows, "next_action": action, "cost_scenario": _cost_scenario(values, claims, facts)}


def compare(values, version, today, *, deferred=()):
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
                                               deployment_region=region)
        if not public:
            return None
        decision = _decision(values, reqs, public, {f["id"]: f for f in facts}, deferred)
        return {"public": public, "sources": sources, "facts": facts, "decision": decision, "bundle": bundle}
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
            lines.append(f"  {label}：{STATUS[c['status']]}；命题 {c['claim_id']}。")
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
    lines.append("成本=主机H+替换墨粉数量×墨粉单价P+另换硒鼓数量×鼓价D+维护M；"
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
    lines.append("下一项高价值核查：" + decision["next_action"]["text"])
    lines.append("没有证明低频耐用排名、真实价格或真人收益；未批准购买，交易关闭。")
    return "\n".join(lines)
