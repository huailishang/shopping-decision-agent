# 下一执行者唯一入口

本包180有效小时/6轮集中纠错，已冻结完整范围，按检查点连续推进，不逐段等批准。目标：让当前工作单解释“哪项假设会改变决定、应该先核哪款的哪一项”，并贯通现有Java、补证、保存恢复和本地决定说明。没有真实模型/账号/交易授权。

先读CURRENT→CONTRACT/AMENDMENT_PREPARATION_R1/EVALUATION/VALIDATION_PLAN/DELIVERY_FORMAT→r42地图→上包REVIEW、holdouts-v2/maintenance-flip.json及SCOPE_DISPOSITION。正式基线为BASELINE.R1.json/.sha256；最初BASELINE是保留的准备失败快照，不用于开工。保留全部未提交成果，旧拒绝/失败账不追认。

开工前在本包evidence/executor/active-sessions.jsonl追加本轮start，结束追加end，不再只计命令秒数。先实际执行：

```text
python -X utf8 handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126/VERIFY_SCOPE.py --phase start
python -X utf8 handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126/VERIFY_ACTION.py
python -X utf8 handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126/VERIFY_UNCERTAINTY.py
```

Windows既有Python可跑；正式计划在仓根WSL Python3运行，Java验证自动转现有Windows环境。不安装新依赖。preparation中真实失败/缺失不是实现完成。

顺序：8小时修原行动反例/粗链→24小时精确单变量分析→48小时共同协议/行动/context→72小时真实窗口范围分析→104小时来源/最小补证→136小时保存恢复/决定说明→164小时16链→180小时完整L2交付。提前达标提前交；外部缺件诚实未知，继续本机工作，不等家庭/账号/设备。

精确新增action和uncertainty_json见合同；不要改冻结验收脚本或把旧Java历史检查移出计划。当前审计器的精确Java版本兼容已纳入新白名单，允许最小候选SHA更新，旧历史对象/清单/失败账不动。

正式L2命令（WSL仓根，技能脚本沿用本机实际路径）：

```text
python3 /mnt/c/Users/HuailiShang/.codex/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126/VALIDATION_PLAN.yaml --out handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126/evidence/executor/l2-final --mode executor
```

交REPORT/COMPARISON/USAGE、16链原件/摘要/生成器、完整活动与外部账、真正窗口证据。L2未全过仍EXECUTING；提交不自签通过，Evaluator独立复核。Git提交/推送/索引、模型CLI/API、业务API、账号设备交易、外发安装均0。
