# 条件传递修复｜执行者集中交接（2026-11-17）

Task ID: PRINTER-MIN-CONDITIONS-REPAIR-20261117
Task kind: repair
Executor status: SUBMITTED_FOR_REVIEW
Parent task: PRINTER-MIN-E2E-20261117
Baseline HEAD: ce34764ab7d803b06abbdbcea0afe32048096c0a
Implementation commit: NONE
Authorization commit/push/api_call: false

本报告只说明执行者的本地修复证据，不替代独立L3，更不修改父包的REJECTED结论；旧时间成本继续标记unknown，不倒填。

## Workspace snapshot

- 主仓库：`D:\SoftWare\VScode\install\Project\shopping-decision-agent`；分支main，已有大量脏工作树，保持原状态，不清理、不提交、不推送。
- 上一包已完成的2/1/0条旧厂家摘要进入CLI、聊天研究及反馈缺失处理等部分继续保留；上一轮独立评审见`handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/REVIEW.md`，裁决REJECTED仍有效。
- 本包冻结范围核对：338个受保护文件哈希匹配（`check_scope.py --check frozen`），包括父包、评审原件、旧研究数据和其他产品模块，未改评估者冻结输入。
- 本包先实际跑出16项 **6/16** 的修复前失败基线：`evidence/executor_before/summary.json`；修复后原检查器16/16：`evidence/executor_after_round1/summary.json`、`evidence/executor_after_round2/summary.json`。
- 实施开始即记录UTC时间戳，`evidence/iterations.json`载明集中修复轮次和墙钟上界；父包有效工时保持unknown。

## Changed files

| 文件 | 修复 |
|---|---|
| `shopping_decision/minimal_research.py` | 在`PurchaseRequest`中保留无线/扫描/双面已确认布尔值、预算口径/地区；直接复用现有`printer_conditions`的required/conflicts/unresolved，而非另写关键词解析 |
| `shopping_decision/minimal_research.py` | 原话微信必须和明确微信要求统一记required，不重复问微信是否必须；A3等未识别硬要求在报告、候选未知项与具体核验动作保留 |
| `shopping_decision/minimal_research.py` | 冲突或本包无证据的硬要求使两款先pending_evidence；没有冲突/硬要求时可keep_for_research，不一律阻断；撤销硬条件能回到原案 |
| `shopping_decision/web.py` | 正常Web评价路径向所选研究转发req.requires_wireless，解决CLI有无线而Web遗漏的问题 |
| `tests/test_minimal_research_flow.py` | 保留原14专项，新增7项直接回归：3硬冲突、原文与结构硬要求等价、撤销恢复、原话微信硬条件、未识别A3、Web无线同源、正常正邻居 |
| `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/`、`REPORT.md` | 本次失败与通过原件、实测工时/失败重试、6项L2验证交接 |

没有改动其他产品文件、上一包证据、冻结合同/检查器/计划、商品资料和GUI。

## 已确认的修复效果

1. **F1 扫描/双面/无线冲突**：原话必须扫描、必须双面、必须无线，但相应已确认字段为false时，旧规范化判断与新可见研究一致：具体冲突可见，两款先pending_evidence。原话同义硬要求与结构化true的有限研究结论一致。
2. **F2 微信与A3硬条件**：原话“必须微信打印”配“转App”被识别为微信硬要求，`wechat_requirement_status=required`，`next_actions`不重复询问微信是否必须；原话“必须A3打印”被列为未识别硬条件，正文保留A3、型号待核，不能凭厂家首次设置指南宣称支持。
3. **F3 无线入口同源**：`requires_wireless=true`既进入CLI，也进入Web所选研究，两款都待核，所选事实和来源未变；正常空要求两款继续研究，撤销原话可恢复而不是永久冲突。
4. **事实边界**：仅复用旧R7/R10首次设置资料，不新增事实、不刷新日期、不判实机成功/微信二次复用/长期可靠/河南实时价；真人反馈数0，购买/交易false。父包2/1/0条流程仍按冻结检查器复跑。

评估者冻结的16项具体反例（含正常CLI/聊天/Web输入与输出）保存在`evidence/executor_conditions/`；执行者额外回归保存在专项测试日志和L2 EV-04。测试数量不等于真实购物收益。

## L2 Task Gate

Validation plan: `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/VALIDATION_PLAN.yaml`
Gate summary: `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/L2-GATE.json`

六项依冻结VP-01至VP-06执行，所有原件按EV-01至EV-06三联路径保存。**最终L2 PASS（6/6，强制失败0项）**，全量464项通过，专项21/21、冻结条件16/16、父包三证据量3/3；最终证据为 `evidence/L2-GATE.json`。首次L2曾为5/6、VP-05失败，原因是无线字段过早进入旧无context的研究路径，导致旧Haina/Java桌面桥接输出改变；修复后16项Haina专项通过，最终正式L2全通过。首次失败的原始EV-05在同路径重跑时被验证程序覆盖，因此只保留如实摘要于 `evidence/first_l2_failure.json`，不冒充该摘要为第一次原始日志。

- VP-01：冻结范围、338受保护文件；
- VP-02：冻结16项反例及相邻正常路径；
- VP-03：父包正常2/1/0条CLI/聊天同源；
- VP-04：保留原14项并新增7项，专项共21项；
- VP-05：一次正式全量回归，参见EV-05 stderr；
- VP-06：本包UTC时间与两轮以内集中修复账，历史成本unknown。

EV-01: `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-01.meta.json`, `EV-01.stdout.log`, `EV-01.stderr.log`。
EV-02: `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-02.meta.json`, `EV-02.stdout.log`, `EV-02.stderr.log`。
EV-03: `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-03.meta.json`, `EV-03.stdout.log`, `EV-03.stderr.log`。
EV-04: `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-04.meta.json`, `EV-04.stdout.log`, `EV-04.stderr.log`。
EV-05: `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-05.meta.json`, `EV-05.stdout.log`, `EV-05.stderr.log`。
EV-06: `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-06.meta.json`, `EV-06.stdout.log`, `EV-06.stderr.log`。

## Impact comparison

- **Before**：独立相邻反例只有3/11符合；本次冻结扩展检查为6/16。扫描/双面/无线冲突丢失；微信/A3已表达硬要求在结果丢失；网页无线true不能进入所选研究。
- **After**：冻结16/16、专项21/21均实际通过；父包正常2/1/0条同源、全量与范围仍需以L2为最终机器校验。原有情况不因加一条暂缺事实全部阻塞。
- **Delta**：恢复条件传递完整性和可见研究的安全未知判断；**没有新增任何商品事实、真实用户体验或可购买报价**。
- **Guardrail**：原话/确认冲突优先；明确未识别硬要求不作无证据的合格判断；无新增外部/账号/交易操作；不扩大品类、商品或GUI。
- **Scope caveat**：本轮是确定性工程缺陷修复，不是认知推荐准确率或真实销售转化改善。

## 未解决与评估责任

- 外部关键B01仍缺真实在售SKU身份、河南有效报价、第二次微信打印实测、长期可靠性和亲戚自愿反馈。
- 资料/厂家适用范围仍限旧首次设置摘要；配对业务收益与真正用户效果仍不可判。
- 原包有效工时未记录，独立评审REJECTED不改变，本包只提供从本次UTC开工起的可核时间段。
- 由评估者独立L3复核冻结反例、原材料范围、典型硬要求正反邻居和本包迭代账；执行者不自签最终PASS。

## L2 Gate evidence summary

- Gate result: PASS
- Gate summary: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/L2-GATE.json
- Validation plan: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/VALIDATION_PLAN.yaml
Gate level: L2
L2 Gate result: PASS
Mandatory failures: 0
Validation plan: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/VALIDATION_PLAN.yaml
L2 summary path: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/L2-GATE.json

## EV-01

- AC: AC-03
- Meta: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-01.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-01.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-01.stderr.log
- Observation: 338个范围外文件SHA与冻结清单匹配。

## EV-02

- AC: AC-01 AC-02
- Meta: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-02.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-02.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-02.stderr.log
- Observation: 16个独立条件反例全部通过；修复前6个通过，有据的负向与正邻居同在。

## EV-03

- AC: AC-02 AC-03
- Meta: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-03.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-03.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-03.stderr.log
- Observation: 正常命令行/聊天用2、1、0条指定事实的三案3/3通过，无context父包旧能力保留。

## EV-04

- AC: AC-01 AC-02 AC-03
- Meta: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-04.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-04.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-04.stderr.log
- Observation: 专项回归21项通过，保留原14项并新增7项相邻条件回归。

## EV-05

- AC: AC-03
- Meta: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-05.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-05.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-05.stderr.log
- Observation: 完整回归464/464通过，用时37.064秒；第一次L2全量门禁失败及原因已单列说明。

## EV-06

- AC: AC-03
- Meta: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-06.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-06.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/EV-06.stderr.log
- Observation: 本包UTC墙钟上界398.312秒、两轮以内集中修复；父包历史有效工时仍unknown。

## Deviations and unresolved items

- 第一次L2门禁FAIL：VP-05单项失败，原因是增加无线条件后旧无context入口行为发生改变。没有改冻结验收器或父包，收窄web.py字段传递后，原失败的海纳/Java桥接专项16/16通过，第二次L2六项PASS。
- 首次L2 runner的EV-05日志被重跑覆盖：保留执行者基于当场错误输出的诚实摘要 `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/first_l2_failure.json`，明确不是首次原始日志；最终EV-05是成功重跑原件。
- 本包连接中断曾多次发生、重连后恢复；未启动任何外网业务请求。父包无法追溯的工时继续unknown，修复包从开工时才记录。
- 不擅自增加测试范围、销售渠道、真实用户数据或账号交易行为；仍需独立L3。

## Impact comparison details

- Measurement evidence: `handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/executor_before/summary.json`、`handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/executor_conditions/summary.json`、`handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/executor_flow/summary.json`、`handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/L2-GATE.json`、`handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/iterations.json`。
- Before: 修复前冻结16条条件检查仅6/16通过；父包独立11项反例中仅3项通过，漏传扫描、无线、双面确认项，且没有完整继承原话微信/A3硬要求。
- After: 冻结16/16通过，专项21/21通过，父包正常三证据量3/3通过，正式全量464/464通过，L2 6/6通过；正常无硬要求样本仍能继续研究。
- Delta: 修复既有证据研究的条件传递一致性，避免冲突漏掉、硬要求偷降级，以及Web和CLI异判；没有新增厂家、商城事实。
- Guardrail result: 购买/交易关闭、无真人反馈、无新增外部/API/账号/付费/提交/推送；老数据与338个受保护文件未变，源日期未刷新。
- Scope caveat: 这些数字仅代表单份代理需求的工程回归检查；真实SKU、河南报价、设备第二次微信打印、长期可靠性及用户价值均仍未知，不能据此声称推荐效果提高。

