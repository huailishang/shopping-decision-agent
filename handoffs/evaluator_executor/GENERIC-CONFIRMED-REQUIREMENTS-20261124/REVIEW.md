# 通用确认条件比较独立复核

Task ID: GENERIC-CONFIRMED-REQUIREMENTS-20261124
Baseline HEAD: 4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf

## 评估前检查

打印机需求收集、改答和待核研究已经能在普通聊天中重放。当前要验证用户条件、证据与候选资格能否正确连接，再接入会改变选购的真实资料。B06 是可信展示的发布前提，B01 的准确型号微信路径、河南应付价和真人收益依旧待证。

已核对四份改动文件与差分的 SHA-256、冻结计划、L2 报告与结构校验。冻结范围核对 1628 份保护件，无差异，HEAD 与索引无变化。评估者接收同一工作区快照，用 WSL Python 独立复跑。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/L3-GATE.json
- Validation plan: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/VALIDATION_PLAN.yaml
- Mandatory failures: 0

15 条冻结命令全部退出 0。原反例 7/7、冻结水壶 9/9 与正常聊天共用入口 1/1、专项 6/6、全量 533/533。原家庭需求和两次改答、预算与地区隔离、安全标志和历史审计均通过。旧模型账 6/10、C05/C06/C07 缺测、合约成功输出 0。

## 独立相邻补测

水壶换成前缀相同的两个候选，并调换候选与条件排列。正确型号列表保留两款各自的判断。事实限定于另一款准确型号时，短名候选的高度待核，容量结果仍保留。将型号列表字段错误地传成字符串后，短名恰好是较长型号的子串，该型号的高度被判满足，候选成为可继续研究。相同输入格式在真实打印机聊天渲染入口也会把另一型号的微信功能判为满足。两个观察均用离线合成资料，购买、交易与实时价已核标志仍为 false。

根因是旧比较器对事实级 `scope_models` 直接用成员判断。字符串会按子串匹配。当前共用入口在进入它之前没有约束事实字段的类型。资料来源覆盖两个型号时，来源检查无法纠正更细一层的事实适用范围。

[独立检查脚本](evidence/evaluator/replay_model_scope.py) 退出 1，5 项检查通过 3 项。[原始输出](evidence/evaluator/model-scope.stdout.json) 保留两个入口的输入、命题与用户可见文本。

## AC 逐条裁决

| 条件 | 裁定 | 独立依据 |
|---|---|---|
| AC-01 | 不通过 | 用户确认条件的三个已知错误修复，扫描和改答回归也过。但打印机入口的独立补测仍以另一型号的规格支持微信硬条件 |
| AC-02 | 不通过 | 两品类确实调用同一入口，全部冻结样例通过。新增型号相邻反例显示候选错误借用另一型号的事实，违反适用范围约定 |
| AC-03 | 通过 | 继承回归与安全标志通过，全量 533 项，历史模型账和旧裁定完整 |
| AC-04 | 通过 | 前后文本、命题、冻结回执、差分与保护件可复核。执行报告留有连接中断导致的精确主动工时缺口 |

## RV-EV-10

- AC: AC-03
- Meta: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/RV-EV-10.meta.json
- Stdout: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/RV-EV-10.stdout.log
- Stderr: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/RV-EV-10.stderr.log

## RV-EV-14

- AC: AC-02, AC-03
- Meta: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/RV-EV-14.meta.json
- Stdout: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/RV-EV-14.stdout.log
- Stderr: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/RV-EV-14.stderr.log

## RV-EV-15

- AC: AC-04
- Meta: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/RV-EV-15.meta.json
- Stdout: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/RV-EV-15.stdout.log
- Stderr: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/l3/RV-EV-15.stderr.log

## Final verdict

REJECTED

## 项目影响裁决

Impact verdict: NOT_APPLICABLE

会话确认条件已独立驱动比较，打印机与水壶工程复用有证据。B06 从资料可改写条件缩小到型号范围畸形时可能串用证据，仍阻断发布可靠的候选资格。本轮未获得实际商品或用户效果增量。

## 下一步

Continuation decision: CONTINUE

交 [准确型号绑定补修包](../CONFIRMED-FACT-MODEL-SCOPE-20261124/CONTRACT.md) 给执行者。一次限时修复共用入口的事实型号范围，保持合法独立容量、报价及匹配型号结论。补修落在已接入两个入口的共用层，保留历史比较器和审计。新增 B01 数据会依赖这个前提，原案例也没有可直接发布的新证据，因此先做短补修。完成后回到真实打印机事实核对。
