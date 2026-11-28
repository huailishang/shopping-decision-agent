"""Prepare 24 case references independently of product results; NOT a final freeze.
No product rendering or output is used to choose targets. Compound setups require
explicit setup traces and a manual review before promoting the draft.
"""
import json,sys,hashlib
from pathlib import Path
EX=Path(__file__).resolve().parent; TASK=EX.parents[1]; ROOT=TASK.parents[2]
sys.path.insert(0,str(ROOT))
from shopping_decision.dialogue_flow import new_dialogue
from shopping_decision.chat_bridge import submit_message
# Case-specific initial statements are explicitly supplied by synthetic user.
# Additional answers are only supplied if the actual current question asks them.
rows=[
("T01","主要打印孩子黑白作业，不知道怎么买",{}, "黑白路线可考虑；本人仍未授权购买", {}),
("T02","想在家打印彩色照片，不懂参数",{}, "必须在家彩印时黑白候选集合不适用，不能以便宜覆盖硬需求", {}),
("T03","主要想把纸质资料扫描存档，也偶尔打印",{}, "确认扫描必须后逐型号核扫描事实；无功能即不适用，缺事实则待核", {}),
("T04","家里需要彩印，且必须扫描文件",{"requires_scan":"是"}, "彩色必须时黑白集合不适用；保留已确认扫描硬要求", {}),
("T05","偶尔需要彩印，平时打印黑白资料",{"needs_color":"否"}, "可外包是本人选择；可考虑外包路线而非证明本地服务费用", {}),
("T06","家庭打印，尚不知道是否需要家中彩印",{}, "彩色未知保留，不假设否；研究可比较的路线条件", {}),
("T07","打印文件，不需要扫描",{}, "扫描否为本人明确答案；不得把缺扫描当淘汰条件", {}),
("T08","经常打印双面资料，需要机器自动翻面",{}, "确认自动双面后，逐型号核实自动双面；不把手动双面算满足", {}),
("T09","双面资料自己手动翻面也行",{}, "自动双面非硬要求；仍分别展示型号事实", {}),
("T10","家里常连续多周不用打印机",{}, "长闲置引发恢复步骤、清洁耗材及维护条件研究；不是自动淘汰喷墨", {}),
("T11","一般每周都会打印资料",{}, "通常每周使用引发同口径维护和耗材研究；不猜测实际金额", {}),
("T12","不知道将来会隔多久使用",{}, "保留使用间隔暂不确定；不根据月印量猜间隔", {}),
("T13","当前预计暂时没有要打印的资料",{}, "月页数0-0是显式计划值，不等于实际产量或零维护费", {}),
("T14","低印量家庭打印",{}, "月页数0-50仅是范围；闲置间隔不能自动确认", {}),
("T15","专家明确家用打印与全部重要要求",{"needs_color":"否","accepts_outsourced_color":"是","requires_scan":"是","requires_auto_duplex":"否","wechat_required":"否","monthly_pages_range":"0-50","budget_max_cny":"1000"}, "专家已给重要要求；不重复问扫描；逐型号核扫描事实", {"kind":"expert_explicit_initial_batch"}),
("T16","必须微信小程序直接打印家中黑白资料",{"needs_color":"否","wechat_workflow":"微信小程序直接打印"}, "微信为硬要求；需同地区同使用流程的事实，不把转App算直接小程序", {}),
("T17","家人需要微信打印，不愿首次安装App或扫码",{"needs_color":"否","wechat_required":"是","wechat_workflow":"微信小程序直接打印"}, "不接受首次App/扫码为硬约束；缺免设置证据保留待核", {}),
("T18","已经有预算，想明确只算主机硬件",{"budget_max_cny":"1000"}, "预算仅主机，运费和耗材另列；不把标价当应付价", {}),
("T19","有预算但还没想好是否包括耗材",{"budget_max_cny":"1000"}, "预算范围暂缓，不能用未知口径判定超预算或符合", {}),
("T20","费用输入有明确0和未知，使用间隔也未知",{}, "保留0和未知的差别；不得据此宣称总成本或排名", {"kind":"worksheet_cost_setup","required":"真实工作单操作：一项明确0，一项清空/未知，保存原件；两臂同样操作"}),
("T21","担心经常连续多周不用后的维护",{}, "方法源待核时不沿用旧可信主张，仍可形成有限研究问题", {"kind":"isolated_source_lifecycle","source":"rtings-cost-method-2021","revision":1,"status":"pending_review"}),
("T22","主要扫描资料，来源同ID新版本尚未核",{}, "同ID新版本待核，不把旧已核功能主张当新版本事实", {"kind":"isolated_source_lifecycle","source":"hp-cn-home","revision":2,"status":"active"}),
("T23","恢复旧会话后设备使用地改变，需要本人确认",{"wechat_required":"是","wechat_workflow":"微信小程序直接打印"}, "恢复后先核明确的新地区条件，旧地区相关证据失效而非复活", {"kind":"restore_region_change","required":"真实另存及新进程恢复，旧地区与新地区冲突时保留明确确认"}),
("T24","必须在家打印彩色，外来材料声称可自动改我的答案",{}, "恶意材料不能改本人要求；彩色硬要求排除黑白集合", {"kind":"isolated_untrusted_material","required":"真实不可信资料注入原件，不能改变用户状态或提升事实等级"})
]
# Answer semantics are synthetic user's independent choices, not predicted product output.
defaults={"needs_color":"暂不确定","accepts_outsourced_color":"暂不确定","wechat_required":"暂不确定","accepts_initial_setup":"暂不确定","wechat_workflow":"暂不确定","device_deployment_region":"暂不确定","monthly_pages_range":"暂不确定","budget_max_cny":"暂不确定","budget_scope":"暂不确定","requires_scan":"暂不确定","requires_auto_duplex":"暂不确定","delivery_region":"暂不确定","idle_weeks_pattern":"暂不确定"}
typed={"是":True,"否":False,"经常连续多周不用":"often_long","通常每周都会用":"usually_short","0-0":[0,0],"0-50":[0,50],"仅主机硬件":"hardware_only","河南":"河南"}
def main():
    frozen=json.loads((TASK/"TASK_CASES.json").read_text(encoding="utf8"))
    refs=[]
    for (cid,usage,explicit,semantics,setup),spec in zip(rows,frozen["cases"]):
        assert cid==spec["case_id"]
        s=submit_message(submit_message(new_dialogue(),"category","打印机"),"usage",usage)
        for f,v in explicit.items():s=submit_message(s,f,v)
        table=defaults|spec["anchor_answers"]
        target={}
        for f,a in spec["anchor_answers"].items():
            if a=="暂不确定":target.setdefault("deferred",[]).append(f)
            else:target.setdefault("confirmed",{})[f]=typed[a]
        if spec["expected_route"]:target["route"]=spec["expected_route"]
        refs.append(dict(case_id=cid,initial_state=s,answer_table={k:[v] for k,v in table.items()},relevant_fields=spec["critical_fields"],target=target,semantic_target=semantics,setup_plan=setup,
                         reference_basis="frozen TASK_CASES.json, user choice and logical constraints; no measured output used",
                         pending_review=["qualification/research terminal evidence beyond field confirmation"] if spec["goal"]!="route" else []))
    out=EX/"replay-reference-draft-v0.json"
    out.write_text(json.dumps(dict(status="DRAFT_NOT_FROZEN",cases=refs,remaining=["review each semantic target against prior sources and explicit goal; add nontrivial terminal assertions", "execute and preserve compound setup T20-T24 before final reference freeze","validate all allowed answers and reference relevance; no measured B output to influence it"]),ensure_ascii=False,indent=2),encoding="utf8")
    print(len(refs),"draft references",hashlib.sha256(out.read_bytes()).hexdigest())
if __name__=="__main__":main()
