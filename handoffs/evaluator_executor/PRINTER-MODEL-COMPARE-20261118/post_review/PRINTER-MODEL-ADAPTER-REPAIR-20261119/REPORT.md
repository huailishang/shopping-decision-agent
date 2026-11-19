# PRINTER-MODEL-ADAPTER-REPAIR-20261119｜执行者交付（2026-11-19）

**执行结论：BLOCKED_EXTERNAL（本轮离线修复已实施并可交独立评估；真实模型可用性仍未验证）。** 当前角色从Executor交回Evaluator。本报告不声明B05认知收益达标，不重开旧包，不补造成功调用。

## 执行范围与成果

- **AC-01 历史收口**：已补旧包报告（完整路径：`handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118/REPORT.md`），如实记录6/10历史调用、C01 2/2、C08 1/2、C05/C06/C07未尝试、已接受模型输出0、一条C04中断缺回执、原费用和实际用量未知、旧VP-02 FAIL。历史6次仍有效计数，剩余4次未使用。
- **AC-02 无推理预检**：见 `evidence/provider_preflight.json`。通过WSL的 `codex --version` / `codex exec --help` 均退出 **127**；WSL `python3` 可用，但 `codex`、`node`、`npm`、`cmd.exe` 未发现于PATH。Windows `/mnt/d/SoftWare/npm/codex.CMD` 文件存在，但不能以此证明在本环境可执行、可强制禁工具、账号有权调用具体模型。历史列表中的 `gpt-5.5`、`gpt-5.4-mini`、`gpt-5.3-codex` 已被真实失败账本拒绝；未再次登陆或读取账号配置。**没有真正验证当前CLI版本或参数支持，保守判 `BLOCKED_EXTERNAL`。**
- **AC-03 事件与异常保护**：`shopping_decision/model_comparison.py` 新增纯离线 `classify_cli_events`。区分 `item.completed:error` / `turn.failed`（provider错误）和 `command_execution`、其他实际/未知工具事件（强制fail-closed）；优先保留provider失败原因，同时记录工具事件数；对进程启动异常、超时、KeyboardInterrupt补失败回执；无完成事件、非法事件行、无有效用量、无回复、非法结构及虚假引用拒绝。对应专项离线反例已纳入 `tests/test_model_comparison.py`，所有测试模拟子进程，没有调用真实模型。
- **旧错判独立重读**：`C01-01`历史`meta.tool_event_count=1`，而新解析器只读该原始JSONL得 `tool_event_count=0`；其错误事件和`turn.failed`保留provider失败。**未修改任何旧live原件**，旧审计脚本也没有被降低门槛。

## 验证回执（本轮实跑）

| 检查 | 命令/方法 | 本轮结果 | 定性 |
| --- | --- | --- | --- |
| VP-01 | `python3 -X utf8 -m unittest discover -s tests -p test_model_comparison.py -v` | **19/19 PASS；退出0** | 新分类与负向用例工程通过 |
| VP-02 | `python3 -X utf8 scripts/run_model_comparison_experiment.py --audit --task handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118` | **退出1**，`model cases not attempted: C05,C06,C07` | **旧包审计仍失败（预期保护检查）** |
| VP-03 | `python3 -X utf8 -m unittest discover -s tests -q` | **483/483 PASS；退出0** | 全量离线回归通过 |
| 历史账核对 | 只读 `attempts.jsonl`、`C01-01` 和冻结哈希 | scheduled **6**、completed **6**；C01旧1工具新0工具；`FROZEN_INPUTS` SHA匹配 | 历史未洗账 |

结果采集：本轮CodexProshl WSL命令回执；`evidence/validation_summary.json`保留结构化验收摘要及重跑命令。原专项13/13、全量477/477是前次旧包成绩，不混入本次19/19、483/483。离线测试通过不等于模型比较质量已知，也不等于有可核河南到手价或真实购物推荐。

## 文件与范围

本轮仅触及 `shopping_decision/model_comparison.py`、`tests/test_model_comparison.py`、旧任务新补`REPORT.md`、本任务`REPORT.md`和`evidence/`、`CURRENT.md`状态/路由。核对变化与SHA见 `evidence/changed_files.json`。原有工作树中的其他改动与未跟踪文件均不做清理。

严禁修改的旧`CONTRACT.md`、`VALIDATION_PLAN.yaml`、`cases.json`、`FROZEN_INPUTS*`、`paired.json`、`evidence/live/**`、`REVIEW.md`仍保留；**新模型推理0次，外部API0次，Git提交/推送0次，实际下单/支付0次**。

## 停止与下一角色

**BLOCKED_EXTERNAL** 是技术前置条件未被证明，不是“模型全部不可用”的断言，也不是业务能力PASS。当前WSL工具链无法无风险确认Codex版本、账号模型权限或隔离参数，按合同停止于预检；不切换环境试调、不消耗旧包最后4次，不重新登录或付费。交由**Evaluator**复核当前代码、负向用例、历史保护及失败结论。

如果模型权限问题仍需外部授权，后续更有价值的主线应优先回B01，补打印机平台SKU、河南有效价和微信打印复用的事实证据；任何真实模型实验须负责人另行授权、冻结独立新合同和预算，不得挪用原6/10账。
