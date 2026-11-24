# 商品事实仅支持准确型号

Task ID: CONFIRMED-FACT-MODEL-SCOPE-20261124
Task kind: repair
Contract state: CONTRACT_FROZEN
Current role: Executor
Baseline HEAD: 4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf
Validation plan file: handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124/VALIDATION_PLAN.yaml

## 战略依据

B06 已将用户确认条件与资料分开，正常打印机聊天和水壶样例共用比较函数。仍有一处发布阻断：事实的型号范围误以字符串传递时，短型号可按子串匹配到长型号。独立补测在两个入口都复现错误满足。新资料接入同样会依赖准确型号匹配，当前没有新的可发布真实资料，因此安排一次短程离线补修。[独立裁定](../GENERIC-CONFIRMED-REQUIREMENTS-20261124/REVIEW.md)

假设是在共用入口验证型号范围的类型、成员和意义，可同时消除两个反例并保留同包其他合格证据。水壶保持离线样例。验收后停止扩张此类合成修复，回到会改变实际打印机选择的真实材料。

## 强制验收

### AC-01 事实型号准确绑定

在共用比较入口，若事实或来源提供 `scope_models`，它须为非空的准确型号字符串列表，条目应为非空有效型号 ID。只按完整 ID 判断，禁止子串匹配。保留缺少事实级范围字段时的既有来源约束。畸形范围的事实待核，其他独立合法事实依旧有命题、来源和原比较结果。原资料保留在审计中。两个独立失败由 3/5 改为 5/5，新增专项覆盖字符串、空值、空列表、混入非字符串，以及来源级和事实级范围的交集。

### AC-02 保留两入口和历史回归

打印机正常入口与水壶离线样例仍走同一比较器。合法全名列表、不同候选、功能与报价、河南原案、撤回、安全和旧 533 项回归继续通过。冻结历史审计保持旧 6/10、C05/C06/C07 缺测、合约成功 0、父包历史裁定不变。购买、交易、实时价已核标志为 false。

### AC-03 可独立复核

留存工作区前测、两个入口修前和修后原始结果、范围哈希、冻结命令退出码、差分、实际时间或计时缺口，交 `REPORT.md` 与 `evidence/executor/`。下一评估者独立复跑，并另改一种型号范围表示，核合法邻项。

## 执行顺序

同一工作区根目录，使用 WSL Python 3.12 与 PyYAML。前测原件 [model-scope.stdout.json](../GENERIC-CONFIRMED-REQUIREMENTS-20261124/evidence/evaluator/model-scope.stdout.json) 退出 1。开始范围检查应退出 0。只修共用入口并补专项，全部验证通过后交评估。

```bash
task=handoffs/evaluator_executor/CONFIRMED-FACT-MODEL-SCOPE-20261124
prior=handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124
workflow=/mnt/c/Users/HuailiShang/.codex/skills/evaluator-executor-workflow/scripts
python3 -X utf8 "$task/VERIFY_SCOPE.py" --phase start
python3 -X utf8 "$prior/evidence/evaluator/replay_model_scope.py"
python3 -X utf8 "$workflow/run_validation.py" --repo . --plan "$task/VALIDATION_PLAN.yaml" --out "$task/evidence/executor/l2" --mode executor
python3 -X utf8 "$workflow/validate_workflow.py" --repo . --current CURRENT.md
```

## 允许改动范围

仅允许修改 `shopping_decision/confirmed_comparison.py`、新增 `tests/test_confirmed_fact_model_scope.py`，填写本包报告、执行证据和 `CURRENT.md` 阶段。既有比较器、门禁、聊天适配、历史审计与先前所有验收原件均保护。

## 明确排除和授权

仅本地离线工程。不启动外部取证或第二品类业务。无公网、平台接口、模型、账号、设备、外发、付费、交易、Git 提交推送或改写历史授权。

## 停止条件

最多 2 有效小时、1 轮集中修正。独立复核建议上限 1 小时。范围受阻或强制项到上限仍失败时保留原始回执并报告。独立通过后评估真实打印机证据的最小取证步骤。
