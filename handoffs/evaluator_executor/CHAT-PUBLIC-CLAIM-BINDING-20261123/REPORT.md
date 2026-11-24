# CHAT-PUBLIC-CLAIM-BINDING-20261123｜执行者修复交付

日期：2026-11-23 · Executor · 瓶颈 B06  
**执行结论：`READY_FOR_REVIEW`。本地冻结重放、新专项及全部六项继承验收命令均退出 0；尚未由 Evaluator 独立签 PASS。**

## 1. 修复前复现与唯一主要改动

读取 `CURRENT.md`、`CONTRACT.md`、`VALIDATION_PLAN.yaml`、`BASELINE.json` 及上一轮 `REVIEW_R2.md` 后，使用冻结的 `VERIFY_FROZEN_REPLAYS.py` 复测。原始前测（本包 preparation 目录）退出 1，九项检查中 `purchase_budget_kept`、`mixed_usage_keeps_its_own_region`、`future_observation_pending` 失败，其他六项为真。此次只改 `shopping_decision/chat_bridge.py`，新增 `tests/test_chat_claim_binding.py`，不改 `claim_gate.py`、`evidence_comparison.py` 或上一轮受评文件。

- **预算绑定**：来自用户当前会话的购机上限须绑定到唯一的硬约束 `cost/CNY/lte`；单靠耗材维度数值碰巧相等、改写成本维度名称、放入更宽松的 1500 元限制都不获准展示“购机满足”。没有完整、可核的含运费／额外耗材总成本时，不把单项费用宣称为已符合总预算，降为待核。
- **适用地逐项绑定**：不是把整个资料包的 `region` 当成所有事实的共同适用范围。每一项约束分别使用当前已确认的收货地（报价）或使用地（功能）建立独立、只供门禁计算的副本，再调用既有 `publish_checked_comparison`。按原候选和约束顺序汇总**门禁生成**的命题、说明和受控下一行动；原始未验材料保留在 `report_json`。河南收货、日本使用时，河南合法报价可作条件比较、只支持河南的微信功能必须待核；同批其他候选的合法报价不因一个候选无效而遭撤销。
- **报价时序**：使用聊天侧可信日期而非资料包自报 `as_of`；逐条核实报价的时区观察日期（本地与 UTC）、采集日期、截止日期先后关系。未来观察、采集早于观察、采集晚于展示、已到期或时间顺序矛盾时，只对该候选的报价降为待核。仍按本包要求以**日期**为有效期粒度。
- 任何发布仍须经过原规则门禁。模型自由叙述不直接发布；`purchase_recommendation_approved`、`transactions_enabled`、`live_price_verified` 均保持 false。

## 2. 独立评估三案前后对照

固定 2026-11-23 为聊天展示日，离线向正常 `render_chat` 注入冻结合成输入，实际 `result_text`、claim 状态、命题 ID 和三个安全标志逐条保存在 `evidence/executor/VP-01-before-after.json`，不是推测结果。

| 场景 | 修复前 | 修复后 |
| --- | --- | --- |
| 预算 1000 写到耗材，购机 1300 与另设 1500 上限 | 耗材 `met`、购机 `met`，展示 `1300 ≤ 1500` | 不再认证这份冲突包，聊天显示待核；无错误 `met` |
| 河南收货、日本使用，报价和微信功能都只在河南适用 | 报价 `met`、微信功能 `met` | 河南报价 `met`，日本微信使用 `unknown`；各自保留不同适用范围 |
| 11 月 24 日才观察的报价，却在 11 月 23 日展示 | 预算 `met` | 预算 `unknown`，不得以未来报价为依据 |
| 正确地区、时间内的合成报价 | `met` | `met`，保留命题 ID |
| 原有合法合成命题 | `met` | `met`，保留命题 ID |

冻结重放 `VP-01` 的 9 项检查全部 `true`，退出码 0。输出：`evidence/executor/VP-01.stdout.txt`、`VP-01.stderr.txt`。前测原始证据 `evidence/preparation/` 保持未改。

## 3. 实际测试和原始证据

环境：本地 WSL Ubuntu / Python 3.12.3；纯离线，没有模型或业务接口调用。

| 检查 | 实测 | 退出 |
| --- | --- | --- |
| VP-01 冻结的前后重放 | 9 项检查全真 | 0 |
| VP-02 新的聊天绑定专项 | **10/10** | 0 |
| R1-VP-01 研究流 | 21/21 | 0 |
| R1-VP-02 打印机决策路径 | 9/9 | 0 |
| R1-VP-03 旧聊天发布 | 13/13 | 0 |
| R1-VP-04 通用结论门禁 | 12/12 | 0 |
| R1-VP-05 全量测试 | **520/520** | 0 |
| R1-VP-06 历史只读审计 | 历史回执完整、旧实验仍未完成 | 0 |

原始命令、stdout/stderr、SHA-256、退出码、每项用时见 `evidence/executor/exit_codes.json` 及 `{检查ID}.stdout.txt`／`{检查ID}.stderr.txt`。最后一次完整执行 8 项检查合计 **104.111 秒**。首次带时间戳的前测为 2026-11-23 13:04:49 UTC，完成时刻记录为 13:18:00 UTC，观察窗口约 13 分 11 秒；该窗口包含阅读、实现与验证，不将它冒充纯编码或精确累计主动执行工时。本包远低于 3 有效小时上限的观察范围。

## 4. 基线、变更与历史保护

最终只读 SHA 复核：本包基线中的 **86 份不可变文件全部一致**（0 个哈希不匹配），仓库 HEAD 保持 `4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf`。回执：`evidence/executor/scope_sha.json`。

此次新增的代码范围仅 `shopping_decision/chat_bridge.py` 与 `tests/test_chat_claim_binding.py`；此前已有的 `scripts/audit_model_history_readonly.py`、`tests/test_publication_entry.py` 未改。本包只新增 `REPORT.md`、`evidence/executor/` 和 `CURRENT.md` 状态更新。评估者的合同、冻结重放脚本、评估材料和旧模型账本未被覆盖。

历史模型实验仍为 **6/10 尝试、C05／C06／C07 未尝试、0 份成功合约模型输出**，父包正式 `REJECTED` 不追认。无公网搜索、外部模型、平台业务 API、登录、订单、付款、Git commit/push，也未重置历史调用预算。

## 5. 交付边界与下一责任

此次只验证**正常聊天的结构化事实到可信文本的绑定**，未将原 Web/Java 桌面所有旧出口视作已统一改造；河南真实在售 SKU、现价、微信实机后续复用和用户选购收益（B01）仍未证实。含额外耗材的完整成本尚无可审总额契约，当前只能保守提示待核。下一责任 **Evaluator**：按 `VALIDATION_PLAN.yaml` 独立重放 `VP-01/VP-02/VP-03/VP-04` 并出正式复核意见；执行者不能自签 PASS。

### 大白话

之前程序能把耗材的 1000 元误当购机预算，也可能拿河南的微信能力证明日本能用，甚至提前使用明天的报价。这三处现在都堵上了；本地 520 条测试全过，也没有把另一款商品的合格证据一块误删。最后还需要评估者独立验证一次，真实商品能不能买仍要靠实际报价和功能证据。
