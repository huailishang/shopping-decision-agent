# REPAIR_R1｜适配器回执严格校验（评估者续修指令 2026-11-19）

本指令属于现有 `PRINTER-MODEL-ADAPTER-REPAIR-20261119` 冻结合同允许的最小集中纠错，不新设长包、不重开历史预算。依据同目录 `REVIEW.md` 的两条独立复现失败；执行者可直接实施并统一交付。

## 唯一目标

修复回执结构和用量字段的两个fail-closed漏口。**不得发真实模型请求、安装软件、登录账号、扩充购物业务、提交或推送。**

## 仅需改动

- `shopping_decision/model_comparison.py` 的 `classify_cli_events`：R1 用严格 `type(x) is int` 或等价手段验证正整数/非负Token计数，不可把 `True/False` 当int；不因 `turn.completed` 有效就忽略非法用量。既有真实CLI字段只要合法应不受影响。
- R2 对 `item.started` / `item.updated` / `item.completed` / `item.failed` 等含item载荷的事件，出现 `item` 不存在、非对象、或item.type缺失/不可用时计入畸形事件并拒绝；不得把未知工具类型改列白名单绕过安全门禁。仍要正确区分 `item.type=error` 的provider错误与 `command_execution/file_change` 工具活动。
- `tests/test_model_comparison.py` 增加独立的最小用例：`usage.input_tokens=true`、`usage.output_tokens=false` 均必须被拒，合法非负整数必须允许；`item.completed` 携带字符串、缺失item或缺少item.type应被拒；实际工具调用仍拒绝，错误日志不误算为工具；合成有效完整响应仍能通过离线校验。
- 更新本包 `REPORT.md`（补R1处理说明、最新结果），`evidence/` 内输出新复验凭据和文件差分/哈希。不覆盖旧版证据，先存后验。

## 验收与停止

集中执行：1）`python3 -X utf8 -m unittest discover -s tests -p test_model_comparison.py -v` 退出0；2）`python3 -X utf8 -m unittest discover -s tests -q` 退出0；3）旧 `--audit` 应仍退出1并原因为 `model cases not attempted: C05,C06,C07`，不得为了变绿而修改冻结门禁或重写旧回执；4）冻结范围、历史live SHA与原6/10次数未改变。

仅修改上面允许的原文件和本包报告/证据与必要的 `CURRENT.md` 路由；不改旧 `REVIEW.md`、旧 `CONTRACT.md`、`FROZEN_INPUTS*`、案例及 `evidence/live/**`。这两项都修好后回交Evaluator，同一任务复评，不派新的同类型小包。若遇到不可解决阻断，报告确切失败及剩余点即可，不能隐瞒或标PASS。

**大白话**：模型说“用了true个token”或把工具回执弄成一串乱码时，程序应当拒绝，而不是装作正常。把这两个判断加严，再把旧测试都跑通。
