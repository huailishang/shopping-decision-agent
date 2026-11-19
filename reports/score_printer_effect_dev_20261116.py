"""保存评估者逐包判读及位置；不调用被测比较器，不自动根据E编号打分。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
PACKETS=ROOT/"reports/printer_effect_executor_recheck_20261116_run01_dev_review_packets.json"
DELIVERY=ROOT/"reports/printer_effect_executor_recheck_20261116_run01_dev.json"
RUBRIC=ROOT/"evaluation/printer_cognition_dev_independent_rubric_20261116.json"
PREFIX="printer_effect_e1_independent_20261116_run01"

# 在逐包审读后明确记录的判定；此表不是由被测函数或它的参考生成器算出的成绩。
# 公开开发、单一评估者、内容可辨组，不声称严格盲评。
PARTIALS={
    ("4e11654a5ce07ee6","D01-original:T4"):
        "地区报价/成本未核已说明；没有明确形成两型号长期耐用对比不足的判断。R6反证仅说耗材页数不是可靠性数据，不能替本组补出整体长期比较结论。",
    ("176a60646c0c9aab","D06-higher-volume:T1"):
        "报告within且信息性，无可靠/最低成本强断言；未明确说明建议区间内不证明耐用/成本最低。按事前完整回答口径记部分，不当作错误选型。",
    ("6ed1a80c8fe360d6","D06-higher-volume:T1"):
        "报告within且信息性，无可靠/最低成本强断言；未明确说明建议区间内不证明耐用/成本最低。与另一包同尺度记部分，不按组别加分。",
}
REASONS={
    "D01-original:T1":"两款路线仍为厂家规格研究，地区实价/预算未核且禁止购买，未承诺千元可买。",
    "D01-original:T2":"两款models.wechat_setup已有Mobile Connect首次配置与Wi-Fi/二维码绑定说明；基线已有内容同等认可。",
    "D01-original:T3":"HP建议印量为informational，低于区间未造成硬淘汰，HP仍可规格研究；不以额外解释条数计分。",
    "D01-original:T4":"明确说现有资料不能给两款长期耐用排名，同时标出地区/耗材实际成本待核；完成复合参考。",
    "D02-miniprogram-outside:T1":"两款均pending，当前C-WECHAT关系deployment_outside_verified_scope，不承诺日本或实机可用。",
    "D02-miniprogram-outside:T2":"两款地区报价标志为false、购买关闭，未由中国区功能升级可购。",
    "D03-color-hard:T1":"两个color_print=false型号均excluded_by_hard_condition，展示的资料不复活为当前适用型号。",
    "D03-color-hard:T2":"purchase_recommendation_approved=false，未给可买承诺。",
    "D04-scan-hard:T1":"HP当前C-SCAN为match，引用R9，限定厂家型号研究。",
    "D04-scan-hard:T2":"Brother当前scan为unknown/not_established且待核，未断言不支持。",
    "D04-scan-hard:T3":"两型号平台身份和地区价仍false，购买关闭。",
    "D05-budget-raised:T1":"C-BUDGET明确读manufacturer_suggested_retail_cny，kind=informational及budget_live_verified=false，来源反证说明非成交价。",
    "D05-budget-raised:T2":"3000元只改变建议价关系；路线实价未核、购买关闭，没有凭空出现地区报价。",
    "D06-higher-volume:T2":"questions无微信工作流补问；源档里保留微信资料不算主动追问。",
}


def write_new(path,obj):
    with path.open("x",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2);f.write("\n")


def main():
    rubric=json.loads(RUBRIC.read_text(encoding="utf-8"))
    source=json.loads(PACKETS.read_text(encoding="utf-8"))
    criteria={t["id"]:t["accept"] for t in rubric["tasks"]}
    annotations=[]
    for packet in source["packets"]:
        output=packet["output"]; task_output=output["task_output"]
        ids={a["id"]:i for i,a in enumerate(task_output["answers"])}
        for task in rubric["tasks"]:
            key=task["id"]
            if not key.startswith(packet["case_id"]+":"):continue
            judgment="partial" if (packet["packet_id"],key) in PARTIALS else "pass"
            locations=["/output/task_output/routes","/output/task_output/purchase_recommendation_approved","/output/known_limits"]
            if key=="D01-original:T2":
                locations=["/output/models/0/wechat_setup","/output/models/1/wechat_setup"]
            elif key in ("D01-original:T3","D06-higher-volume:T1"):
                locations=[f"/output/task_output/answers/{ids['M232dw:C-VOLUME']}/current_check", "/output/models/1/eligibility", "/output/task_output/questions"]
            elif key=="D01-original:T4":
                locations=["/output/known_limits/2", "/output/task_output/questions"]
                if "E-RELIABILITY-UNKNOWN" in ids:
                    locations.append(f"/output/task_output/answers/{ids['E-RELIABILITY-UNKNOWN']}")
                else:
                    locations.append(f"/output/task_output/answers/{ids['HL-L1238W:C-BUDGET']}/source_refs/0/counter")
            elif key.startswith("D02-") and key.endswith(":T1"):
                locations=[f"/output/task_output/answers/{ids[m+':C-WECHAT']}/current_check" for m in ("HL-L1238W","M232dw")]
            elif key.startswith("D03-") and key.endswith(":T1"):
                locations=[f"/output/task_output/answers/{ids[m+':C-COLOR']}/current_check" for m in ("HL-L1238W","M232dw")]+["/output/task_output/routes"]
            elif key.startswith("D04-") and key.endswith((":T1",":T2")):
                name="M232dw" if key.endswith(":T1") else "HL-L1238W"
                locations=[f"/output/task_output/answers/{ids[name+':C-SCAN']}","/output/task_output/routes"]
            elif key=="D05-budget-raised:T1":
                locations=[f"/output/task_output/answers/{ids['HL-L1238W:C-BUDGET']}"]
            elif key=="D06-higher-volume:T2":
                locations=["/output/task_output/questions"]
            annotations.append({"packet_id":packet["packet_id"],"case_id":packet["case_id"],"task_id":key,
                                "reference_acceptance":criteria[key],"judgment":judgment,"locations":locations,
                                "reason":PARTIALS.get((packet["packet_id"],key),REASONS.get(key,"按事前口径记录")),
                                "blind_arm_label_not_consulted_for_this_annotation":True})
    assert len(annotations)==30
    manual_path=ROOT/"reports"/(PREFIX+"_dev_single_arm_scores.json")
    write_new(manual_path,{"role":"independent_evaluator","status":"open_development_single_arm_reading_not_strict_blind",
                          "rubric":str(RUBRIC.relative_to(ROOT)),"packet_file":str(PACKETS.relative_to(ROOT)),
                          "rubric_sha256":hashlib.sha256(RUBRIC.read_bytes()).hexdigest(),
                          "packets_sha256":hashlib.sha256(PACKETS.read_bytes()).hexdigest(),"annotations":annotations,
                          "formal_holdout_started":False})

    # 逐包判断先保存，再读取对应表汇总；公共代码/内容已见，因此不声称盲化成功。
    delivered=json.loads(DELIVERY.read_text(encoding="utf-8"))
    mapping={r["packet_id"]:r["arm"] for r in delivered["review_key_do_not_show_to_blind_reviewer"]}
    groups={}
    for arm in ("baseline","cognition"):
        rows=[r for r in annotations if mapping[r["packet_id"]]==arm]
        cases={c:[r for r in rows if r["case_id"]==c] for c in sorted({r["case_id"] for r in rows})}
        groups[arm]={"tasks":len(rows),"pass":sum(r["judgment"]=="pass" for r in rows),
                     "partial":sum(r["judgment"]=="partial" for r in rows),"fail":sum(r["judgment"]=="fail" for r in rows),
                     "complete_cases":sum(all(r["judgment"]=="pass" for r in cr) for cr in cases.values()),
                     "case_count":len(cases),"case_scores":{c:{"pass":sum(r["judgment"]=="pass" for r in rs),
                                                          "partial":sum(r["judgment"]=="partial" for r in rs),"tasks":len(rs)} for c,rs in cases.items()}}
    paired=[]
    for t in rubric["tasks"]:
        pair={mapping[r["packet_id"]]:r for r in annotations if r["task_id"]==t["id"]}
        paired.append({"task_id":t["id"],"baseline":pair["baseline"]["judgment"],"cognition":pair["cognition"]["judgment"],
                       "same":pair["baseline"]["judgment"]==pair["cognition"]["judgment"]})
    out={"role":"independent_evaluator","date":"2026-11-16","scope":"public_development_explicit_answer_completion_not_real_shopping_effect",
         "case_count":6,"reference_items":15,"single_arm_annotations":30,"groups":groups,"paired_items":paired,
         "same_items":sum(p["same"] for p in paired),"different_items":[p for p in paired if not p["same"]],
         "materially_changed_model_eligibility_cases":0,"new_external_sources":0,
         "manual_annotations":str(manual_path.relative_to(ROOT)),"mapping_read_after_annotation_file_written":True,
         "reviewer_count":1,"strict_blinding_claimed":False,
         "interpretation":"只在原案耐用性未知的显式说明上多完成1项；不证明选型/真实购买改善。D06两组共同只完成部分，不能靠补一句模板制造效果。",
         "sensitivity":"若把没有作无据强断言也视作完成限缩说明，三项partial可同时放宽，两组均15/15、6/6，差异归零。保留该口径敏感性，不选择有利口径宣称增益。",
         "formal_holdout_created":False,"formal_holdout_started":False,"formal_effect_estimate":None,
         "purchase_approved":False,"transactions_enabled":False}
    write_new(ROOT/"reports"/(PREFIX+"_dev_scoring.json"),out)
    print(json.dumps({"groups":groups,"same_items":out["same_items"],"different_items":out["different_items"]},ensure_ascii=False))


if __name__=="__main__":main()
