"""Local worksheet inputs; all conclusions are recomputed by the existing chat engine."""
from copy import deepcopy
from datetime import date
import json
from uuid import uuid4

from .evidence_comparison import digest
from .cognition_comparison import (_scenario_money, MAX_SCENARIO_MONTHS,
                                   MAX_SCENARIO_PAGES)
from .cost_scenario import SCOPE, dependency_fingerprints

MAX_BYTES = 256 * 1024
KEYS = {"schema_version", "action", "state", "worksheet", "payload"}
BASIS = ("pages", "months", "currency", "fee_scope", "scenario_version")
COST = ("hardware", "starter", "toner_yield", "toner_price", "separate_drum",
        "drum_yield", "drum_price", "drum_starter", "maintenance")
FIELDS = {"schema_version", "worksheet_id", "revision", "binding", "confirmed",
          "deferred", "withdrawn", "basis", "models", "sources"}

def _pairs(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError("JSON含重复字段")
        obj[k] = v
    return obj

def parse(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError("工作单超过256KiB")
    obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError("非有限数值")))
    stack = [(obj, 0)]
    while stack:
        x, depth = stack.pop()
        if depth > 16:
            raise ValueError("工作单嵌套过深")
        if isinstance(x, (dict, list)):
            if len(x) > 128:
                raise ValueError("工作单集合过大")
            stack.extend((v, depth + 1) for v in (x.values() if isinstance(x, dict) else x))
    return obj

def _public(view):
    r = json.loads(view["report_json"])
    return r["cognition_comparison"]["public"] if r.get("cognition_comparison") else r["public_decision"]

def _identity(state, public):
    from .chat_bridge import confirmed_values
    values = confirmed_values(state)
    return {"category": values.get("category"), "dialogue_version": state["version"],
            "confirmed_values_sha256": digest(values),
            "session": public["decision_binding"]["session"] if public else None}

def _new(state, public):
    from .chat_bridge import confirmed_values
    models = {} if public is None else {
        a["candidate_id"]: {"values": dict.fromkeys(COST), "kind": "user_scenario_assumption",
                            "dependency_fact_ids": [], "dependency_fingerprints": {}, "withdrawn_fact_ids": []}
        for a in public["assessments"]}
    return {"schema_version": 1, "worksheet_id": uuid4().hex, "revision": 0,
            "binding": _identity(state, public), "confirmed": confirmed_values(state),
            "deferred": sorted(state.get("deferred_fields", [])),
            "withdrawn": sorted(state.get("withdrawn_fields", [])),
            "basis": {"pages": None, "months": None, "currency": "CNY",
                      "fee_scope": SCOPE, "scenario_version": 1},
            "models": models, "sources": []}

def _number(field, value):
    if value is None:
        return value
    if field in ("pages", "starter", "toner_yield", "drum_starter", "drum_yield", "months", "scenario_version"):
        low = 1 if field in ("toner_yield", "drum_yield", "months", "scenario_version") else 0
        high = MAX_SCENARIO_MONTHS if field == "months" else MAX_SCENARIO_PAGES
        if type(value) is not int or not low <= value <= high:
            raise ValueError("页数、期间或版本超出允许范围")
    elif field in ("hardware", "toner_price", "drum_price", "maintenance"):
        if isinstance(value,str) and len(value)>64:
            raise ValueError("费用值过长")
        _scenario_money(value)
    elif field == "separate_drum":
        if type(value) is not bool:
            raise ValueError("是否鼓粉分离必须明确选择")
    elif field == "currency":
        if not isinstance(value, str) or len(value) != 3 or not value.isascii() or not value.isalpha() or not value.isupper():
            raise ValueError("币种无效")
    elif field == "fee_scope" and value != SCOPE:
        raise ValueError("费用范围无效")
    return value

def _validate(w):
    if not isinstance(w, dict) or not FIELDS <= set(w) <= FIELDS|{"prior_assumption","guide_reference"} or type(w["schema_version"]) is not int or w["schema_version"] != 1:
        raise ValueError("工作单结构或版本无效")
    if not isinstance(w["worksheet_id"], str) or len(w["worksheet_id"]) != 32 or any(c not in "0123456789abcdef" for c in w["worksheet_id"]):
        raise ValueError("工作单编号无效")
    if type(w["revision"]) is not int or w["revision"] < 0:
        raise ValueError("工作单修订号无效")
    if not isinstance(w["binding"], dict) or set(w["binding"]) != {"category","dialogue_version","confirmed_values_sha256","session"}:
        raise ValueError("会话绑定无效")
    if not isinstance(w["confirmed"], dict) or not all(isinstance(w[k], list) for k in ("deferred", "withdrawn", "sources")):
        raise ValueError("工作单确认或来源无效")
    from .dialogue_flow import _check_answer
    from .chat_bridge import LABELS
    for k,v in w["confirmed"].items():
        if k not in LABELS or v is None:
            raise ValueError("无效确认条件")
        _check_answer(k,v)
    for k in ("deferred","withdrawn"):
        if any(not isinstance(f,str) or f not in LABELS for f in w[k]) or len(set(w[k]))!=len(w[k]):
            raise ValueError("无效待确认或撤回条件")
    if set(w["deferred"]) & set(w["withdrawn"]) or set(w["confirmed"]) & (set(w["deferred"]) | set(w["withdrawn"])):
        raise ValueError("工作单条件互相冲突")
    if not isinstance(w["basis"], dict) or set(w["basis"]) != set(BASIS):
        raise ValueError("成本口径无效")
    for k,v in w["basis"].items():
        _number(k,v)
    if not isinstance(w["models"], dict) or len(w["models"]) > 2:
        raise ValueError("候选无效")
    for row in w["models"].values():
        if not isinstance(row,dict) or set(row)!={"values","kind","dependency_fact_ids","dependency_fingerprints","withdrawn_fact_ids"} or row["kind"]!="user_scenario_assumption":
            raise ValueError("成本只能作为用户假设")
        if not isinstance(row["values"], dict) or set(row["values"]) != set(COST):
            raise ValueError("成本字段无效")
        for k,v in row["values"].items():
            _number(k,v)
        ids, fps = row["dependency_fact_ids"],row["dependency_fingerprints"]
        if not isinstance(ids,list) or not all(isinstance(i,str) for i in ids) or len(set(ids))!=len(ids) or not isinstance(fps,dict) or set(ids)!=set(fps):
            raise ValueError("来源依赖无效")
        revoked=row["withdrawn_fact_ids"]
        if not isinstance(revoked,list) or not all(isinstance(i,str) for i in revoked) or len(set(revoked))!=len(revoked) or not set(revoked)<=set(ids):
            raise ValueError("撤回引用无效")
    if "guide_reference" in w:
        ref=w["guide_reference"]
        if (not isinstance(ref,dict) or set(ref)!={"guide_id","guide_version","source_ids"}
                or ref["guide_id"]!="printer-cognition-guide"
                or not isinstance(ref["guide_version"],str) or len(ref["guide_version"])!=64
                or any(c not in "0123456789abcdef" for c in ref["guide_version"])
                or not isinstance(ref["source_ids"],list) or len(ref["source_ids"])>64
                or any(not isinstance(x,str) or not x or len(x)>120 for x in ref["source_ids"])
                or len(set(ref["source_ids"]))!=len(ref["source_ids"])):
            raise ValueError("指南引用无效；存档不能保存推荐结论")
    prior=w.get("prior_assumption")
    if prior is not None:
        if (not isinstance(prior,dict) or set(prior)!={"candidate","field","value"}
                or not isinstance(prior["candidate"],str) or prior["candidate"] not in w["models"]
                or not isinstance(prior["field"],str) or prior["field"] not in COST):
            raise ValueError("单项成本对照输入无效")
        _number(prior["field"],prior["value"])
    for item in w["sources"]:
        if not isinstance(item,dict) or set(item)!={"id","candidate","kind","locator","observed_at","excerpt","status","version"}:
            raise ValueError("来源结构无效")
        if item["status"] not in ("pending_review","withdrawn") or item["kind"] not in ("manufacturer_excerpt","professional_review","user_comment","quote_lead"):
            raise ValueError("外部材料不能自行成为已审事实")
        if not all(isinstance(item[k],str) and len(item[k])<=4000 for k in ("id","candidate","locator","observed_at","excerpt")) or type(item["version"]) is not int or item["version"]<1:
            raise ValueError("来源字段无效")
        date.fromisoformat(item["observed_at"])
    if len({i["id"] for i in w["sources"]}) != len(w["sources"]):
        raise ValueError("来源ID重复")
    return w

def _scenario(w):
    return {"schema_version":1,"binding":w["binding"],
            **({"prior_assumption":w["prior_assumption"]} if w.get("prior_assumption") is not None else {}),
            "models":{k:{"kind":"synthetic_scenario","inputs":dict(w["basis"],**v["values"]),
                         "dependency_fact_ids":v["dependency_fact_ids"],
                         "dependency_fingerprints":{fid:("withdrawn" if fid in v["withdrawn_fact_ids"] else fp) for fid,fp in v["dependency_fingerprints"].items()}}
                      for k,v in w["models"].items()}}

def _concise_result(view, w):
    # A short projection of the same authoritative decision, not a new ranking.
    from .cognition_comparison import LABELS
    from .cost_scenario import render_cost
    public = _public(view)
    if public is None:
        return view["result_text"] + "\n" + _summary(w, public)
    binding = public["decision_binding"]
    hard = {r["id"] for r in binding["requirements"] if r["importance"]=="hard"}
    lines = ["当前取舍（研究判断，不是购买许可）"]
    for a in public["assessments"]:
        cid=a["candidate_id"]
        label={"excluded_for_research":"硬条件不满足，排除","pending_evidence":"硬条件待核","eligible_for_research":"现有硬条件研究层面满足"}[a["research_status"]]
        claims=[c for c in public["claims"] if c["candidate_id"]==cid and c["requirement_id"] in hard]
        lines.append(cid+"："+label)
        for status, title in (("failed","反证"),("unknown","缺证"),("conflict","冲突"),("met","有据")):
            dims=[LABELS.get(c["dimension"],c["dimension"]) for c in claims if c["status"]==status]
            if dims:lines.append("  "+title+"："+ "、".join(dims))
    lines.append(render_cost(public.get("cost_comparison")))
    lines.append("下一步："+view["prompt"])
    guidance=json.loads(view["report_json"]).get("cognition_guidance",{}).get("usage_research",{})
    if guidance.get("status")=="research_required":
        lines.append("使用场景补证："+guidance["question"])
    lines.append(_summary(w,public))
    lines.append("完整来源、日期及核查限制见资料审计；原结果见完整审计。未批准购买，交易关闭，未核实实时价格。")
    return "\n".join(lines)

def _summary(w, public):
    lines = ["本机决策工作单：成本输入均为个人情景假设，不是实时价格。"]
    if w["sources"]:
        lines.append(f"本机新导入资料{len(w['sources'])}条，均不作为已验事实；请查看工作单资料审计。")
    else:
        lines.append("暂无新导入资料；原有事实仍以原证据门禁为准。")
    return "\n".join(lines)

def _source_rows(w, view):
    public=_public(view)
    report=json.loads(view["report_json"])
    cognition=report.get("cognition_comparison") or {}
    bundle=cognition.get("bundle") or (report.get("research_result") or {}).get("verified_research_bundle") or {}
    sources={s["id"]:s for s in bundle.get("sources",[]) if isinstance(s,dict) and "id" in s}
    rows=[]
    seen=set()
    def clean(x):return str(x).replace("\t"," ").replace("\n"," ").replace("\r"," ")
    if public:
        for claim in public["claims"]:
            cid=claim["candidate_id"]
            for a in claim["source_audit"]:
                fid=a["fact_id"]
                if (cid,fid) in seen:continue
                seen.add((cid,fid))
                src=sources.get(a["source_id"],{})
                revoked=fid in w["models"].get(cid,{}).get("withdrawn_fact_ids",[])
                label="本工作单引用已撤回" if revoked else "结构准入（真实性限于原复核）" if a["admitted"] else "未准入/失效"
                if not revoked and claim["status"]=="conflict":label+="；证据冲突"
                if not revoked and isinstance(src.get("valid_until"),str) and src["valid_until"]<date.today().isoformat():label+="；已过期"
                rows.append({"candidate":cid,"id":fid,"status":label,"grade":a["source_grade"],
                             "locator":src.get("locator"),"url":src.get("url"),"observed_at":src.get("observed_at",src.get("captured_on")),
                             "valid_until":src.get("valid_until"),"fingerprint":a["evidence_sha256"],"limit":a["limit"]})
    pending=[i for i in w["sources"] if i["status"]=="pending_review"]
    for i in w["sources"]:
        label="已撤回" if i["status"]=="withdrawn" else "型号不适用" if i["candidate"] not in w["models"] else "未审；不参与事实"
        if i["kind"]=="quote_lead" and i["observed_at"]!=date.today().isoformat() and label.startswith("未审"):
            label="历史报价线索，现价待核；未审"
        if i in pending and i["candidate"] in w["models"] and any(j["id"]!=i["id"] and j["candidate"]==i["candidate"] and j["kind"]==i["kind"] and j["excerpt"]!=i["excerpt"] for j in pending):
            label+="；同类摘录有差异，待核冲突"
        rows.append({"candidate":i["candidate"],"id":i["id"],"status":label,"grade":i["kind"],
                     "locator":i["locator"],"observed_at":i["observed_at"],"version":i["version"],
                     "limit":"用户导入摘录，未经认证；不会自动访问地址"})
    return "\n".join("\t".join(clean(r.get(k,"")) for k in ("candidate","id","status","grade","observed_at","valid_until","locator","url","limit")) for r in rows)

def _fields(w):
    labels = {"pages":"期间总打印页数","months":"期间（月）","currency":"币种",
              "hardware":"主机价","starter":"随箱实际可用页数","toner_yield":"替换墨粉实际页数",
              "toner_price":"替换墨粉单价","separate_drum":"鼓粉分离（是/否）",
              "drum_yield":"替换鼓实际页数","drum_price":"替换鼓单价","drum_starter":"随箱鼓实际页数","maintenance":"维护总费用"}
    rows = []
    for cid, values in [("", w["basis"]), *((k,v["values"]) for k,v in w["models"].items())]:
        for k,v in values.items():
            if k in labels:
                display = "" if v is None else "是" if v is True else "否" if v is False else str(v)
                rows.append("\t".join((cid,k,labels[k],display)))
    return "\n".join(rows)

def _conditions(w):
    from .chat_bridge import LABELS
    return "\n".join([f"{LABELS.get(k,k)}：{v}" for k,v in w["confirmed"].items()] +
                       ["暂缓："+ "、".join(LABELS.get(k,k) for k in w["deferred"]),
                        "撤回："+ "、".join(LABELS.get(k,k) for k in w["withdrawn"])])

def handle(request):
    from .chat_bridge import _valid_state, render_chat, confirmed_values
    from .dialogue_flow import _check_answer, new_dialogue
    if not isinstance(request,dict) or set(request)!=KEYS or type(request["schema_version"]) is not int or request["schema_version"]!=1:
        raise ValueError("工作单请求结构或版本无效")
    state = _valid_state(deepcopy(request["state"]))
    for k,v in confirmed_values(state).items():
        _check_answer(k,v)
    action, payload = request["action"],request["payload"]
    if not isinstance(payload,dict) or action not in ("create","preview","edit","clear","import_source","withdraw_source","restore","rebind","edit_many","inspect","bind_reference","withdraw_reference","guide"):
        raise ValueError("工作单操作无效")
    if action == "guide":
        if payload or request["worksheet"] is not None or "category" not in confirmed_values(state):
            raise ValueError("指南只接受已确认品类和空参数")
        return render_chat(state)
    initial = render_chat(state)
    public = _public(initial)
    if action == "create":
        if request["worksheet"] is not None or payload:
            raise ValueError("创建工作单不接收旧内容")
        w = _new(state,public)
    else:
        w = _validate(deepcopy(request["worksheet"]))
        if action == "inspect":
            if payload:
                raise ValueError("预览不得改变输入")
            return {"status":"preview","worksheet_conditions":_conditions(w),
                    "worksheet_json":json.dumps(w,ensure_ascii=False)}
        if action == "restore" and payload == {"confirm_saved_conditions":True} and not state["answers"] and not state["history"]:
            # Explicit confirmation on an empty session only; no silent overwrite.
            if set(w["confirmed"]) & (set(w["deferred"]) | set(w["withdrawn"])):
                raise ValueError("保存的条件冲突")
            for k,v in w["confirmed"].items():
                _check_answer(k,v)
            state = new_dialogue()
            state["answers"] = {k:{"value":v,"confirmed":True,"origin":"user_explicit","raw_text":"已确认恢复的条件"} for k,v in w["confirmed"].items()}
            state["deferred_fields"] = w["deferred"]
            state["withdrawn_fields"] = w["withdrawn"]
            state["version"] = 1
            _valid_state(state)
            initial=render_chat(state);public=_public(initial)
            # Same conditions may rebind; prior source fingerprints are rechecked by current gate.
            if set(w["models"]) != set(_new(state,public)["models"]):
                raise ValueError("恢复候选已变化，请重新创建")
            w["binding"]=_identity(state,public)
        elif w["binding"] != _identity(state,public):
            if action != "rebind" or payload:
                raise ValueError("工作单与当前需求不一致；请预览原条件并重新创建")
            # Explicit rebind clears obsolete costs and references.
            w = _new(state,public)
        if w["confirmed"] != confirmed_values(state) or w["deferred"] != sorted(state.get("deferred_fields",[])) or w["withdrawn"] != sorted(state.get("withdrawn_fields",[])):
            raise ValueError("工作单需求快照与当前条件不一致")
        if set(w["models"]) != set(_new(state,public)["models"]):
            raise ValueError("工作单候选与当前比较不一致")
        if action in ("edit","clear","edit_many"):
            changes = payload.get("changes") if action=="edit_many" else [payload]
            if action=="edit_many" and set(payload)!={"changes"}:
                raise ValueError("批量编辑无效")
            if not isinstance(changes,list) or not 1<=len(changes)<=32:
                raise ValueError("编辑数量无效")
            seen=set()
            actual_changes=[]
            for change in changes:
                if not isinstance(change,dict) or set(change)!={"candidate","field","value"}:
                    raise ValueError("编辑字段无效")
                cid, field = change["candidate"],change["field"]
                if (cid,field) in seen:
                    raise ValueError("同一字段重复编辑")
                seen.add((cid,field))
                val = None if action=="clear" else change["value"]
                if cid is None and field in BASIS:
                    if w["basis"][field]!=val:actual_changes.append((None,field,w["basis"][field]))
                    w["basis"][field]=_number(field,val)
                elif cid in w["models"] and field in COST:
                    if w["models"][cid]["values"][field]!=val:actual_changes.append((cid,field,w["models"][cid]["values"][field]))
                    w["models"][cid]["values"][field]=_number(field,val)
                else:
                    raise ValueError("未知成本字段或候选")
            if actual_changes:
                w.pop("prior_assumption",None)
                if len(actual_changes)==1:
                    cid,field,old=actual_changes[0]
                    if cid is not None and old is not None and w["models"][cid]["values"][field] is not None:
                        w["prior_assumption"]={"candidate":cid,"field":field,"value":old}
            w["revision"]+=1
        elif action in ("bind_reference","withdraw_reference"):
            if set(payload)!={"candidate","fact_id"} or payload["candidate"] not in w["models"] or not isinstance(payload["fact_id"],str):
                raise ValueError("来源引用无效")
            cid, fid=payload["candidate"],payload["fact_id"]
            row=w["models"][cid]
            if action=="bind_reference":
                admitted=dependency_fingerprints(public,cid) if public else {}
                if fid not in admitted:
                    raise ValueError("只能引用当前已准入事实")
                if fid not in row["dependency_fact_ids"]:
                    row["dependency_fact_ids"].append(fid)
                row["dependency_fingerprints"][fid]=admitted[fid]
                row["withdrawn_fact_ids"]=[i for i in row["withdrawn_fact_ids"] if i!=fid]
            else:
                if fid not in row["dependency_fact_ids"]:
                    raise ValueError("不存在此工作单引用")
                if fid not in row["withdrawn_fact_ids"]:
                    row["withdrawn_fact_ids"].append(fid)
            w["revision"]+=1
        elif action=="import_source":
            if set(payload)!={"id","candidate","kind","locator","observed_at","excerpt"}:
                raise ValueError("只接受待审摘录，不接受自称已审或执行内容")
            previous=next((i for i in w["sources"] if i["id"]==payload["id"]),None)
            w["sources"]=[i for i in w["sources"] if i["id"]!=payload["id"]]+[dict(payload,status="pending_review",version=1 if previous is None else previous["version"]+1)]
            w["revision"]+=1
        elif action=="withdraw_source":
            if set(payload)!={"id"} or not any(i["id"]==payload["id"] for i in w["sources"]):
                raise ValueError("未知来源")
            for item in w["sources"]:
                if item["id"]==payload["id"]:
                    item["status"]="withdrawn"
            w["revision"]+=1
        elif action in ("preview","rebind") and payload:
            raise ValueError("预览不修改输入")
        elif action=="restore" and payload not in ({},{"confirm_saved_conditions":True}):
            raise ValueError("恢复操作无效")
    previous_reference=w.get("guide_reference")
    _validate(w)
    final = render_chat(state,cost_scenario=_scenario(w) if public and len(w["models"])==2 else None)
    # Store only identifiers, never trust saved guide content or a saved winner.
    g=json.loads(final["cognition_guide_json"]) if "cognition_guide_json" in final else None
    current_reference={"guide_id":g["guide_id"],"guide_version":g["version"],
                       "source_ids":sorted(x["id"] for x in g["sources"])} if g else None
    if current_reference:
        w["guide_reference"]=current_reference
    else:
        w.pop("guide_reference",None)
    _validate(w)
    guide_changed=previous_reference!=current_reference and action!="create"
    if guide_changed:
        message=("已按当前来源重算认知；旧指南引用已迁移，用户明确答案及独立成本假设保留。"
                 if previous_reference is None else "指南版本或来源已变化；旧认知引用失效，按当前材料重算，不复活旧判断。用户明确答案保留。")
        final["guide_change_notice"]=message
        report=json.loads(final["report_json"])
        report["guide_reference_change"]={"previous":previous_reference,"current":current_reference,"notice":message}
        final["report_json"]=json.dumps(report,ensure_ascii=False,indent=2)
    final["worksheet_json"] = json.dumps(w,ensure_ascii=False)
    final["worksheet_fields"] = _fields(w)
    final["worksheet_conditions"] = _conditions(w)
    final["worksheet_sources"] = _source_rows(w,final)
    final["worksheet_detail_text"] = final["result_text"]
    final["result_text"] = _concise_result(final,w)
    if "guide_change_notice" in final:
        final["result_text"] += "\n"+final["guide_change_notice"]
    if "cognition_guide_json" in final:
        from .decision_note import render_note
        final["decision_note_json"]=render_note(json.loads(final["report_json"]),final,final["prompt"])
    return final
