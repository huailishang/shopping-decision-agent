# PRINTER-MODEL-ADAPTER-REPAIR-20261119｜评估者独立复核（2026-11-19）

**独立裁定：NEEDS_REPAIR（限一轮最小续修），不可签PASS；真实模型可用性仍BLOCKED_EXTERNAL/UNKNOWN。**

## 已确认完成

1. AC-01 历史失败事实补报：PASS。旧 `PRINTER-MODEL-COMPARE-20261118/REPORT.md` 已补全，冻结8例、历史6/10次、C01 2/2、C08 1/2、C05/06/07未尝试、accepted=0、C04中断原件缺失，均未冒充成功。
2. AC-02 无推理预检及诚实停损：PASS（仅报告就绪度/阻塞，不是模型接通）。WSL `codex --version` 和 `codex exec --help` 均退出127，Windows `/mnt/d/SoftWare/npm/codex.CMD`存在不等于WSL可执行或账号授权。未新调用模型；`BLOCKED_EXTERNAL`应解释为**当前WSL运行环境及账号权限未证实**，不是“所有模型一定不可用”。
3. 冻结保护：PASS。评估者只读比对 `FROZEN_INPUTS.json`：受保护文件SHA不匹配数0、清单增减数0；`evidence/live/attempts.jsonl` 排程6、终结6，SHA-256 `dc0f8631caa98df123206ef751312f42998e3f55614ac81b730bd7dbfe372026`，与执行者回执相同；未重置历史额度。
4. 本轮独立实跑（WSL `python3`）：VP-01专项19/19通过、退出0；VP-03全量483/483通过、退出0；VP-02旧 `--audit` 退出1，原因为 `model cases not attempted: C05,C06,C07`，与合同预期一致，**不记作旧包通过**。
5. C01-01原始错误消息属于 `item.completed: error` 和 `turn.failed`，不能据此称真实工具调用；新分类器对此按0个工具事件处理，旧meta及账本保持不变。
6. 真实模型推理成功数仍为0，河南现价、型号微信后续条件、可售身份及真人选购改善均未在此包解决。此处仅能判工程测试与诚实停损，不能判B05认知收益。

## 独立新增反例，AC-03暂不通过

**R1（必须修）**：`classify_cli_events` 的 `valid_usage` 用 `isinstance(value, int)`，Python中 `isinstance(True,int) is True`。评估者通过真实本机解释器构造 `{"type":"turn.completed","usage":{"input_tokens":true,"output_tokens":5}}`，实际返回 `valid_usage=True`；浮点数被拒，布尔值未拒。违反合同“无有效用量拒绝”，未来可能错误标记伪造或畸形回执合格。

**R2（必须修）**：构造 `{"type":"item.completed","item":"this-is-not-an-object"}` 后接合法 `turn.completed` 和合法用量，实际返回 `tool_event_count=0, malformed_lines=0, valid_usage=True, provider_errors=[]`。应显式将畸形的item事件标记格式错误并拒绝，而非忽略未知结构。已有的真实 `file_change` 工具事件能被识别，故只需补结构门禁。

以上均为**离线合成对抗输入**，不代表历史CLI实际发生了这些问题，也不代表真实购买已出现风险。由于AC-03要求无效用量与不合规事件拒绝，此两项为定向余项，不能因19/19、483/483为绿就直接签PASS。

## 评估者决定

- 状态：`NEEDS_REPAIR`；下一责任`Executor`；保持同一任务ID，不分叉大型执行包，使用合同已允许的≤2轮本地纠错额度中的一轮。
- **唯一下一步**：依 `REPAIR_R1.md` 修复R1/R2，给各自最小负向测试，并只做一次集中专项+全量+旧审计验证，更新新包 `REPORT.md` 和 `evidence/`；不碰旧live、冻结输入、商品/GUI或真实模型。
- 如果两项通过且未引入回归，评估者下一次可签**本地适配器维护PASS，阻塞状态仍然保留**；不应擅自切换到真实模型实验。
- 不创建新模型推理预算，旧6/10账永久保留；无需新登录、支付、Git提交或推送。模型适配仍被WSL环境挡住时，后续业务主线优先评估B01高价值商品事实，不因模型不可用而空转。

**用大白话说**：执行者把大部分故障日志处理好了、测试也都能跑，但还有两种奇怪的假数据能漏进来。先把这两个小口堵住，再签本轮工程验收；模型还没真正接通，别说已经能靠AI选好商品。
