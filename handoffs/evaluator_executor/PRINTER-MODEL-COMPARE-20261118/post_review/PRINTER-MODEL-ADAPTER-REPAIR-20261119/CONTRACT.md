# B05 模型适配器解阻｜下一执行包（2026-11-19）

Task ID: PRINTER-MODEL-ADAPTER-REPAIR-20261119
Task kind: bounded_blocker_repair
Contract state: CONTRACT_FROZEN / READY_FOR_EXECUTOR
Current role: Executor
Baseline HEAD: ce34764ab7d803b06abbdbcea0afe32048096c0a
Project map revision: r35 (冻结原件；本次独立结论见前包REVIEW，不修改保护文件)
Active bottleneck: B05
Hypothesis: H-B05-ADAPTER-PREFLIGHT-01
Previous task: PRINTER-MODEL-COMPARE-20261118（评估者FAIL/BLOCKED；不回写假PASS）
Authorization: api_call=false, commit=false, push=false, history_rewrite=false
Execution budget: ≤2小时有效工时；≤2轮集中本地纠错；不新增任何真实模型推理尝试。

## 为什么要做

离线通用比较专项13/13、全量477/477回归通过，但旧合同VP-02失败且 `accepted={}`：真正的模型响应尚无一次完成。历史CLI显示当前登录账号不支持三个被测模型；C01尝试已2/2，旧合同不能再在不违背冻结规则的前提下达成C01/C08两例成功。一次旧 `item.completed/error` 被误标为工具使用。不能一边猜模型一边烧掉剩余额度，也不能把合成比较冒充实际推理。

## 单一目标

**把“模型调用为何失败、可否安全再次尝试、失败事件如何准确记录”的本地适配器问题做到可审、可复验、可停损。** 本包只产出离线诊断和准备度判决，不要求也不允许进行真实模型推理、重开八例比较或追加打印机资料。无法证明可用模型是合格结论，不是让执行者无休止尝试。

## 原子验收

### AC-01 旧包事实收口（mandatory）
- 为旧任务补 `handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118/REPORT.md`：真实6次调用、三例未尝试、C01已2/2、C08已1/2、残余4次、不合约回执0、一次中断缺回执、未读凭证、时间和费用未知、VP-02失败，明确执行者自报而非评估者PASS。
- 不改旧 `CONTRACT.md` / `VALIDATION_PLAN.yaml` / `cases.json` / `FROZEN_INPUTS*` / `paired.json` / live原始文件、历史 `REVIEW.md`；绝不清零计数。

### AC-02 无推理运行前检查（mandatory）
- 检查本机Codex CLI的 `--version`、`exec --help`、账号登录状态的非敏感标志（可由现有历史回执代替）、支持的隔离/只读/无工具参数与本地模型可见列表。**仅执行不会触发推理、网页登录、外部API或写认证的命令**；不查看、复制、打印Key、token或账号配置内容。
- 输出 `evidence/provider_preflight.json`：环境与命令时间、适配器候选、已知拒绝型号、可核的安全选项、版本/型号不确定项、`inference_success=false`、是否准备发起新一轮申请；“模型列表存在”不得标为“账号有权调用”。
- 对CLI参数不支持、模型授权未知或环境不满足严格只读要求，报告 `BLOCKED_EXTERNAL`，停止；不发真实模型请求。

### AC-03 错误事件分类和回执完整性（mandatory）
- 在 `shopping_decision/model_comparison.py` 及对应专项测试中区分 `item.completed: error`、`turn.failed`、真正工具调用（command/tool）和正确完成；provider错误必须优先保留精确类别，不得因为错误事件把调用误报为工具越权。
- 构造离线夹具（可从历史脱敏原件派生）覆盖：不支持的模型、响应结构错误、工具事件、无完整输出、超时、中断、无有效用量、成功但伪引用、正确成功。真实历史meta不改；测试样本不得反向污染旧账。
- 保持fail-closed：真实工具调用/缺失引用/强行下单均拒绝；离线规则和合成模型响应不能作为实际推理成果。原包历史 `tool_event_count` 不追改。
- 对旧审计失败要如实呈现：`--audit` 仍应退出1，不允许降门槛来获取绿灯。

### AC-04 统一交付和停损（mandatory）
- 交 `REPORT.md` 和 `evidence/` 中的预检、分类专项、验证及变更清单。解释是否还值得做真实模型实验，以及支持/阻塞判断依据。
- 专项与全量必须在当前环境各跑1次并记录准确计数、退出码；可集中修复2轮，不重复无价值的模型尝试。
- 不将旧包剩余4次预算转入本包；本包 `api_call=false`，即使账号表面可用也**停止在预检门口**。
- 验收结果只有两种：`READY_FOR_SEPARATELY_AUTHORIZED_LIVE_PROBE`（仅具备技术前置条件，未证明模型可用），或 `BLOCKED_EXTERNAL`（模型权限/工具隔离无法保证）。二者都不是B05认知收益PASS。

## 允许修改

- `shopping_decision/model_comparison.py`，必要时 `scripts/run_model_comparison_experiment.py` 中仅涉及错误识别/断点显示的最小段落；`tests/test_model_comparison.py`。
- 旧包新建 `REPORT.md`（不改旧REVIEW或历史原件）。
- 新包 `REPORT.md`、`evidence/`，及 `CURRENT.md` 的状态/路由（保留旧冻结SHA声明，以使旧合同审计仍可复核）。
- 不改商品事实、旧冻结样本、其他项目/GUI/知识库；不重构通用研究管道。

## 验证计划

详见同目录 `VALIDATION_PLAN.yaml`。评估者独立按相同离线方法复跑，并人工核对C01历史错误事件不是工具调用。不得用测试覆盖数代替真实比较成果。

## 交接与停止条件

执行者先补旧REPORT、做无推理预检，再最小修复分类与用例，最后集中验证和新REPORT。若本机无法保证真正无工具/只读隔离、需要新模型权限或付费，立即停下并给准确断点，不下载安装/登录/付费/试调。

**后续路线不是自动授权**：若仅剩账号权限阻塞，评估者优先建议项目回到B01的高价值商品事实核验；只有项目负责人另行批准新一轮真实模型尝试，才建立新冻结基线、独立预算与新的任务包（原6/10记录永不重置）。
