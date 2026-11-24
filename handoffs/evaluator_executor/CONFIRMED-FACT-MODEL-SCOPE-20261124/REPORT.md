# 商品事实准确型号绑定｜执行者修复报告

Task ID: CONFIRMED-FACT-MODEL-SCOPE-20261124
Executor status: SUBMITTED_FOR_REVIEW
Baseline HEAD: 4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf
Implementation commit: NONE

## Workspace snapshot

- 开工范围检查 evidence/executor/start.json：6/6，1683份保护件。原评估者重放 model-before.json 退出1，3/5。
- EV-17：6/6，1683份保护件不变，HEAD与索引不变。
- 最终工作区 evidence/executor/workspace-status.txt；差分 evidence/executor/workspace-diff.patch（CURRENT及共用程序完整未提交内容含既有改动），SHA-256: 41c80d592efb8ecae054c83acb53cd76374d62259ddd11307bc3c4a5b096b925；文件哈希 evidence/executor/changed-sha256.json。

## Changed files

| File | Action | SHA-256 | Factual change |
|---|---|---|---|
| CURRENT.md | 修改 | ae2851360bd608ad3d6d20a69c8b0400e28f991300a61ea8b1302de025ab9a97 | 送审路由 |
| shopping_decision/confirmed_comparison.py | 修改 | c949ab1147f92e49e0dcd68cd90e6d258b087822f6b820cfb552889812c12136 | 新增准确型号范围准入函数；在共用入口逐事实执行双重精确匹配，畸形证据仅在副本撤销 |
| tests/test_confirmed_fact_model_scope.py | 新增 | 9f05a5751a2dbdd8c76cdfaed10f4217e8f9aec7ff92082154a027eca679502f | 5项专项，含多种畸形范围、交集、合法邻项和正常聊天 |

## L2 Task Gate

- Gate result: PASS
- Gate summary: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/L2-GATE.json
- Validation plan: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/VALIDATION_PLAN.yaml
- Mandatory failures: 0

17/17冻结检查退出0；全量538/538（533+5）。
AC-01：EV-15/16。来源和事实只要显式提供scope_models，就必须是非空有效字符串列表，完整匹配当前候选；缺字段时维持旧门禁。字符串、null、空列表、映射、布尔、数字、混入非字符串或空白ID均待核。来源与事实的交集约束同时成立才准入。仅在比较副本标记撤销，不改原包；合法独立价格、容量、型号及同条件合法事实保留。原反例3/5→5/5。
AC-02：EV-01至15；旧打印机聊天、预算、地区、撤回、历史门禁及水壶共用入口通过。EV-11历史6/10、C05/C06/C07缺测、合约成功0、旧REJECTED不改。交易与真实核验标志保持false。
AC-03：EV-17，前后原始重放、文件哈希、差分、此报告。计时见逐项元数据。

## EV-01

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-01.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-01.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-01.stderr.log

## EV-02

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-02.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-02.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-02.stderr.log

## EV-03

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-03.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-03.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-03.stderr.log

## EV-04

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-04.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-04.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-04.stderr.log

## EV-05

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-05.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-05.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-05.stderr.log

## EV-06

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-06.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-06.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-06.stderr.log

## EV-07

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-07.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-07.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-07.stderr.log

## EV-08

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-08.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-08.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-08.stderr.log

## EV-09

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-09.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-09.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-09.stderr.log

## EV-10

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-10.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-10.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-10.stderr.log

## EV-11

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-11.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-11.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-11.stderr.log

## EV-12

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-12.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-12.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-12.stderr.log

## EV-13

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-13.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-13.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-13.stderr.log

## EV-14

- AC: AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-14.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-14.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-14.stderr.log

## EV-15

- AC: AC-01, AC-02
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-15.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-15.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-15.stderr.log

## EV-16

- AC: AC-01
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-16.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-16.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-16.stderr.log

## EV-17

- AC: AC-03
- Meta: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-17.meta.json
- Stdout: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-17.stdout.log
- Stderr: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/evidence/executor/l2/EV-17.stderr.log

## Impact comparison

- Measurement evidence: evidence/executor/model-before.json、model-after.json、special-tests.log、l2/EV-15.stdout.log、EV-16.stderr.log、EV-17.stdout.log。
- Before: 短型号以字符串子串借用长型号规格，打印机及水壶两入口均复现，3/5。
- After: 5/5原重放，5/5新增专项，538/538全量；畸形范围不作为适用证据，合法证据保留其原命题及来源。
- Delta: 原两处已知失败降至0；不是现实购买效果增量。
- Guardrail result: 原始资料不改，双范围精确匹配，无购买、交易或实时价核验授权。
- Scope caveat: 只修共用确认条件比较入口，其他保护程序未改；水壶是合成案例，真实河南价格、准确型号微信使用及真人收益待证。

## Iteration ledger

- 2026-11-24：重新连接后先执行范围检查与原重放，实际退出0、1；一次集中实现，新增专项5/5；L2 17/17，逐项计时见meta，全量538项用时42.353秒。
- 网络曾中断，主动工时无精确独立计时；合同上限2有效小时、1轮集中修正保留。命令守卫拒绝一次包含多个操作的命令，未执行，后采用工作区专用edit/write完成非破坏性许可编辑。无第二次实现轮次。
- 外部模型、平台API、账号、设备、付款及交易调用0。停止原因：冻结检查均通过，提交独立复核。

## Deviations and unresolved items

- 未修改既有比较器、门禁、聊天适配、历史审计、旧测试或冻结原件；仅合同允许的共用程序、测试与本包证据及CURRENT。
- 尚未完成评估者独立L3。建议独立复跑并另建型号范围变体，核对合法邻项。
- 真实商品取证仍待下一阶段；未提交或推送Git，不改写历史。
