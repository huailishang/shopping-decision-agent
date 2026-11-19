# 最小证据贯通｜独立集中评审（2026-11-17）

Task ID: PRINTER-MIN-E2E-20261117
Reviewed baseline HEAD: ce34764ab7d803b06abbdbcea0afe32048096c0a

## 项目全局概览

目标是帮助实际家庭按需求和证据作购物取舍，主链为需求→证据→比较→可读结果→反馈→复核。已有需求整理、条件改答、旧r3有限分支与保存能力。本包确实把2/1/0条旧厂家摘要接入正常研究和后半程缺失处理；这项成果保留。

第一外部瓶颈仍是B01：准确销售身份、河南有效价格、二次微信复用及真人收益没有证据。本轮针对“缺件就整包停在准备”的内部障碍，不能把走通样本当成购买建议充分。独立反例又暴露了B02条件传递缺陷，应先修现有路径，再投入新事实或扩界面。

## Pre-review checks

| 项目 | 结果与依据 |
|---|---|
| 地图/合同/计划 | 已读地图r30、冻结合同与六项计划；任务和HEAD一致 |
| 执行者自检 | L2六项通过，原件完整 |
| 范围 | 冻结检查96个受保护文件吻合；本轮评估未改产品 |
| 提交快照 | evidence/evaluator_start_snapshot.json记录226个可读文件；结束核对全部未变 |
| 环境 | 评估在Windows原生Python运行；原执行者WSL解释器链接本机不可访问，快照记录该项并保留链接，未改工具链 |
| 来源 | 本地旧来源映射SHA吻合；R7仅Brother首次设置，R10为HP系列首次设置；没有重新联网核源 |
| 授权 | 未读取凭证、联网取证、调用业务接口、外发、操作设备或交易，未提交/推送 |

## L3 Independent Gate

- Gate result: PASS
- Gate summary: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/L3-GATE.json
- Validation plan: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/VALIDATION_PLAN.yaml
- 六项均退出0；正常命令行/聊天三案3/3，检查器12/12，专项14/14，全量457/457。
- 使用冻结的评估者命令，将新回放写入evidence/evaluator_flow，未覆盖执行者或首轮原件。自动检查通过不替代下述逐条裁决。

## RV-EV-01

- AC: AC-01 AC-06
- Meta: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-01.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-01.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-01.stderr.log
- 观察：冻结输入及范围匹配。

## RV-EV-02

- AC: AC-01 AC-02 AC-05
- Meta: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-02.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-02.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-02.stderr.log
- 观察：检查器自检12项通过，但没有覆盖本轮发现的完整条件传递反例。

## RV-EV-03

- AC: AC-01 AC-02 AC-03
- Meta: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-03.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-03.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-03.stderr.log
- 观察：原代理样本与单条/零条反例均产生可见同源研究结果。

## RV-EV-04

- AC: AC-01 AC-02 AC-03 AC-05
- Meta: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-04.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-04.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-04.stderr.log
- 观察：14项原专项通过；原冲突测试只覆盖微信，遗漏扫描/无线/双面确认项。

## RV-EV-05

- AC: AC-03 AC-05 AC-06
- Meta: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-05.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-05.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-05.stderr.log
- 观察：457项通过，耗时35.854秒；不代表推荐准确率。

## RV-EV-06

- AC: AC-03 AC-04 AC-06
- Meta: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-06.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-06.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/RV-EV-06.stderr.log
- 观察：六环节记录及SHA绑定存在；反馈0、效果未知，未冒充真人评测。

## 独立反例与发现

普通入口原件及判读：evidence/evaluator_counterexamples/summary.json；构造脚本：evidence/evaluator_probe.py。共11项边界检查，3项符合、8项不符合，归为以下三组；这是工程反例数量，不是推荐准确率。

1. **F1 / P2：扫描、双面、无线的明确冲突在新报告消失。** 原话“必须扫描”并确认扫描不是必须时，旧正常比较为condition_conflict（条件冲突）；所选包结果却给空冲突列表，两款都保留研究，正文还说可继续。双面、无线同样复现；扫描/双面还在正常聊天可见结果复现。原因在minimal_research.py:60重建请求时漏传三个确认项，已有冲突识别器因此收不到完整输入。违反AC-02/AC-05，不能用“研究不购买”消除该错误。
2. **F2 / P2：已识别的硬条件没有进入可见判断。** 原话“必须微信打印”、方式为转App时，正常约束已经识别为微信硬要求，新结果却称“微信是否必须仍是未答目标”；“必须A3打印”已进入未识别硬要求，新正文完全遗漏A3，两款仍保留研究。minimal_research.py:69后只消费冲突，没有完整处理已有硬要求与待澄清项，且微信分支只看原始布尔字段。应保留明确硬要求、未知和具体待核动作；不能要求用户重复勾选，也不能猜A3能力。违反AC-02/AC-05。
3. **F3 / P2：无线条件在入口之间丢失。** 相同明确requires_wireless=true（无线必须），命令行两款待核，网页正常化约束含无线必须，但所选包两款却保留研究。web.py:134—150构造研究输入漏掉requires_wireless。当前自动三案未覆盖该字段，因而仍全绿。违反AC-05的输入改答与同源判断要求。

正向保护成立：拒绝首次设置、原有微信冲突、境外范围三项均仍待核；所有已查路径的购买/交易标志关闭。

## Acceptance matrix

| AC | 裁决 | 执行/独立证据 | 具体依据 |
|---|---|---|---|
| AC-01 | 通过 | EV/RV-EV-01至04、evaluator_flow | 选包、型号、日期、限制和来源一致，2/1/0条实际改变来源与状态 |
| AC-02 | 不通过 | RV-EV-03/04、独立F1/F2 | 原案稀疏处理成立，但明确冲突和未识别硬条件被新结论漏掉 |
| AC-03 | 通过 | RV-EV-03/05/06、first_walkthrough、flow_trace | 首轮与六环节原件存在，正常样本聊天可见，缺反馈处理后继续复核；不把缺失处理说成真人反馈 |
| AC-04 | 通过 | RV-EV-06、assessment、paired_diagnosis | RQ-01至03局限合理；旧入口不能限定同一证据集的理由与实际路径相符；不报公平双组收益 |
| AC-05 | 不通过 | RV-EV-04/05、独立F1至F3 | 原负向全绿，但相邻实际冲突与改答反例失败 |
| AC-06 | 不通过 | RV-EV-01/06、iterations | 范围/冻结/两轮原件成立；有效工时明确未计时，首4/总20小时等时间约束无法独立复核，不能签已兑现 |

工时缺口是可验证性不足，**没有证据指称已经超时**。无法复核，建议人工抽查；后续不得凭文件时间倒填历史有效工时，也不重复旧完整包来补造历史。

## Final verdict
REJECTED

- 未通过：AC-02、AC-05、AC-06。
- 最小修复：完整传递已有确认条件、硬要求、冲突及未知，修复无线字段遗漏，增加实际入口回归；保留原包完成部分及失败原件。历史有效工时继续未知，新修复包从开工起记录可审时间。
- 所需外部材料/授权：本次修复无新增需要；不得因为缺真人/价格再退回全包准备。

## Project impact verdict

Impact verdict: INCONCLUSIVE

最小选包贯通是实际工程变化，不只是新字段：删减资料会改变来源与候选状态，正文可见，后半程处理存在。但条件传播错误使完整正确性未成立，不能签可靠的整体改善；新事实0、真人反馈0，真实选购收益仍未知。不把此裁决解释成原案流程从未走过，亦不把原L3自动通过抹掉。

地图需更新至r31：B01关键事实不足未消除，新增B02内部条件传递余项；当前先做一次小范围修复，比继续给同一不完整路径加资料/界面更有价值。

## 迭代价值与下一动作

Continuation decision: CONTINUE

本轮有价值的变化是选包隔离和缺失后的继续交付，影响范围仅一份代理原案。独立证据置信度高；实际用户效用不可判。计算成本可见为457项约36秒，另有有限本地回放；执行者历史有效工时和费用未独立计量，不虚构收益率。新增一个小模块也引入第二次需求映射，已暴露维护风险。

下一轮只值得修这些已实证的条件传递错误，不继续堆分支或扩大事实/框架。预计小范围本地修复最多4有效工时、独立复核1小时、最多2轮集中纠错；完成即可停止同方向实现扩张。较强替代是新增关键事实，但在当前约束会被漏掉的情况下，先修确定错误更便宜、信号更明确。

## 瓶颈变化与下一执行包

少量资料贯通障碍已部分缩小，B01外部事实和实际用户收益未移动；F1—F3暴露内部B02阻断。下一方向为PRINTER-MIN-CONDITIONS-REPAIR-20261117，单方向修复，不执行新研究或交易。

- 新合同：handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/CONTRACT.md
- 下一状态/责任：CONTRACT_FROZEN / Executor。
- 主要改变：新有限研究完整消费当前已确认条件和已有规范化结果。
- 已备：具体反例、冻结预期、输入、范围、验证命令和预算；无缺失人工决定。
- 历史有效工时无法追溯的问题保留在本评审，新包不声称修复历史记录或改写原裁决。
