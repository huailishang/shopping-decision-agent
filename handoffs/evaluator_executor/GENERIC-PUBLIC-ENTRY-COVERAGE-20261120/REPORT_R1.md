# GENERIC-PUBLIC-ENTRY-COVERAGE-20261120｜R1 续修执行者报告

日期：2026-11-20。角色：Executor。  
**交付结论：核心修复完成，强制验收仍 BLOCKED，不能签 PASS。** R1 全量 506 项，505 项通过、1 项报错；唯一本地阻断为此前已冻结的历史只读审计脚本未同步 R1 正式授权的两项旧测试文件变更白名单。

## 1. 本轮已实施的内容

1. `shopping_decision/chat_bridge.py` 在原有 `publish_checked_comparison` 可信发布边界之外，新增 `_safe_research_progress`：只消费用户当前确认字段以及 `minimal_research.selected_pack` 根据固定 SHA/合法 pack id 取出的受限研究包元数据，不读取原 `report_text`、`decision_plan.text` 或 `recommendation.reasons` 发布商品事实。
2. 正常聊天显示受保护研究包的 **2／1／0 条「待核研究记录」**。0 条明确说明本次没有留存待核型号记录，所有数量均明确「不代表有效商品证据数」；未知包则显示数量未知。
3. 微信「必须」→优先核准确型号的微信发起/后续复用条件；「可选」→继续核低频印量、耗材和准确型号，微信未核不阻断其他研究；未答→提示先澄清。均为研究动作模板，而非设备已支持的结论。
4. 随当前用户改答 1000→800、微信必须→可选、品类切换重新显示，失效旧 `claim_id` 不得直通；用户已确认预算只标为用户需求，不作为已核地区报价。
5. 按 `AMENDMENT_R1.md` 的新白名单，对 `tests/test_minimal_research_flow.py` 和 `tests/test_printer_decision_plan.py` 的两项过时断言做最小语义迁移：原研究文字仍在 `report_json`、原 `used_facts` 和 `decision_plan.current_path` 保留，但对外 `result_text` 不再原样透传；未删/跳过既有测试。
6. 在 `tests/test_publication_entry.py` 增加 2／1／0 数量、微信必需／可选／未答、预算改答、换品类的实际 `render_chat` 回归。原反向预算话术/促单文本仍不可发布，真实商品价格与外部来源不在本包验证范围。

## 2. 冻结计划真实执行与回执

完整日志：`handoffs/evaluator_executor/GENERIC-PUBLIC-ENTRY-COVERAGE-20261120/evidence/r1/`。另保存 `public_replays.json`（5组真实 render_chat 重放，2/1/0 记录计数与微信必须/可选的用户展示，以及对应审计字段；均无旧诱导文字进入公开结果）。

| 检查 | 实际运行 | 退出 | 结论 |
| --- | --- | --- | --- |
| R1-VP-01 | `test_minimal_research_flow.py`，21 项 | 0 | PASS |
| R1-VP-02 | `test_printer_decision_plan.py`，9 项 | 0 | PASS |
| R1-VP-03 | `test_publication_entry.py`，9 项 | **1** | **8 通过、1 ERROR**，旧历史审计固定 allowlist 与 R1 新授权冲突 |
| R1-VP-04 | `test_claim_gate.py`，12 项 | 0 | PASS |
| R1-VP-05 | 全量 `unittest discover -s tests -q`，506 项 | **1** | **505 通过、1 ERROR**，同上 |
| R1-VP-06 | `scripts/audit_model_history_readonly.py --task ...` | **1** | **FAIL**，`unapproved_historical_file_drift:tests/test_minimal_research_flow.py` |

`R1-VP-03.log`、`R1-VP-05.log`、`R1-VP-06.log` 是正式原始失败记录，不得涂改或改记 PASS。

## 3. 唯一强制阻断及最小建议

- 冻结 R1 合同明确允许最小修改 `tests/test_minimal_research_flow.py` 和 `tests/test_printer_decision_plan.py`，但上一轮创建的 `scripts/audit_model_history_readonly.py` 常量 `CURRENT_TASK_ALLOWED_DRIFT` 仍只允许 `shopping_decision/chat_bridge.py`。因此历史清单校验把本包 **已授权** 的两处旧测试变更误判为异常。
- R1 明确禁止执行者擅自修改只读审计脚本，故我没有偷偷扩大变更白名单，也没覆盖受保护旧账。
- 在**不写回脚本**的只读法证核查中，仅对本次调用的内存常量临时加入这两处 R1 已授权测试路径，审计就能完整核验：17 份固定保护件 SHA 不变，6 次 scheduled／6 次 completed、10 次上限、C05/C06/C07 未试、旧 HEAD `ce34764` 与现 HEAD `53fa539` 漂移，零成功模型输出。原件没有被修改。证据在 `evidence/r1/history_scope_diagnostic.json`。这只是诊断，不是 R1-VP-06 正式 PASS。
- **交评估者处理**：针对 `scripts/audit_model_history_readonly.py` 冻结一个极小范围补充授权，允许原本 1 个变化路径增加为严格明确的 3 个 R1 合法变化路径，仍逐个验证其他 1229 个冻结文件及旧账 SHA。不要整体关闭 SHA 校验。授权后再复跑 R1-VP-03、R1-VP-05、R1-VP-06；本轮不自行签验收。

## 4. 改动和权限边界

本轮只修改 `shopping_decision/chat_bridge.py`、`tests/test_minimal_research_flow.py`、`tests/test_printer_decision_plan.py`、`tests/test_publication_entry.py`，新增本 `REPORT_R1.md` 与 `evidence/r1/`，更新 `CURRENT.md` 执行交接。未碰历史 `model_comparison.py`、`claim_gate.py`、`desktop_bridge.py`、`web.py`、旧实验冻结材料或 r35 地图；没有外部模型/网页/API 调用、加购/付款、Git 提交或推送。前包已有未提交文件保持原状，不重置历史。

### 大白话总结

聊天现在既能挡住没有证据的“可以买”，也能告诉用户手上有 2、1 或 0 条待核研究资料，微信是硬要求还是偏好，对应下一步也会变化。老的两项测试已经修好。剩下唯一的问题是历史检查程序还不知道这轮获准改动了两个测试文件，导致整套测试 506 项只有这一个地方报错。我没有偷改冻结范围，已把最小修复办法和原始证据交评估者。
