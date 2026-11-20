# GENERIC-PUBLIC-ENTRY-COVERAGE-20261120｜执行者交付

日期：2026-11-20。角色：Executor。  
**结果：BLOCKED（新聊天发布功能局部验证通过；冻结 AC-05 的全套回归 504 项中 2 项未通过）。不得宣称整包 PASS。**

## 1. 本包做了什么

- **主聊天入口已换发布边界**：`shopping_decision/chat_bridge.py` 的 `render_chat(...).result_text` 不再直接拼接旧 `recommendation.reasons`、`shared.decision_plan.text`、`research_case.report_text`；这些仍保存在 `report_json.research_result`，并标 `legacy_unverified_research`。
- 新增 `_publish_for_chat`：只有来自当前 `analysis.verified_research_bundle` 的完整结构化输入，且品类、对话版本、已确认条件哈希、预算和实际使用地区对应当前会话，才可调用已有 `publish_checked_comparison`，生成命题 ID、已判状态、规则比较式、来源限制与受控行动文本。
- 现生产 `evaluate_input` 尚不提供该可靠 typed bundle；因此普通打印机聊天会**降级为“商品判断：待核研究”**，绝不伪造机型/河南报价/型号功能已验证。测试对模拟后端提供的合法合成结构化事实可展示 `claim_id` 与 `900 ≤ 1000`，并明确“仅本地合成验证，不代表真实商品”。
- 用户的填答、草稿、追问、改答、暂不确定和非打印机品类保留在独立 `understanding/prompt/editable`，与商品已验结论分隔。状态 `recommendation.status` 仅保留为原工作流字段，不赋予购买资格。
- `purchase_recommendation_approved=false`、`transactions_enabled=false`、`live_price_verified=false` 均保持。无真实模型/平台/用户购买调用。
- 新增 `scripts/audit_model_history_readonly.py`：核对原冻结清单 SHA、上一包固定 17 份保护件、8 例场景、6 次 scheduled/completed、meta / 请求 / stdout / stderr 配对及原始 SHA；明确标记旧 HEAD ce34764 与现 HEAD 53fa539 不同，而不改写 HEAD、旧审计脚本或证据。静态源文件 `chat_bridge.py` 是本合同内预期变化，其余历史原清单文件均未漂移。旧实验仍是 0 份合格模型成功输出，C05/C06/C07 缺测；不会追认原 REJECTED 包。

## 2. 可复现的主入口前后对比

本包 `evidence/baseline_reproduction.json` 对同一合成场景做了实际两次调用：

- **修改前基线**：通过 `git show HEAD:shopping_decision/chat_bridge.py` 隔离执行旧 `render_chat`，模拟旧研究文案含“1300<1000，立刻下单”，旧 `result_text` **确实含诱导文字**。
- **修改后**：同一 `analysis` 送给新的 `render_chat`，`result_text` **不再含上述文字**，输出待核研究说明。未验原文只在内部审计保留。
- **合成正样本**：匹配当前对话版本、用户条件哈希、预算和地区的 synthetic_probe 结构化事实经 `publish_checked_comparison` 输出 `claim_id`、`900 ≤ 1000`、`met`，同时说明合成输入不代表真实商品可买。

原始输出分别在 `evidence/baseline_old_chat.json`、`new_chat_unverified.json`、`new_chat_synthetic_verified.json`。出口清单见 `evidence/entry_inventory.json`。**本包只改正常聊天 `result_text`；旧 `desktop_bridge.py` / `web.py` 仍未接新发布门。**

## 3. 冻结计划的真实测试结果

| 验证 | 退出码 | 结果 |
| --- | --- | --- |
| VP-01 主聊天新增专项 | 0 | 7/7 PASS，含恶意文字、型号/地区价降级、编辑重算、合成正样本及只读账本篡改负测 |
| VP-02 旧通用 claim_gate 专项 | 0 | 12/12 PASS |
| VP-03 全量 | **1** | **504 项，502 PASS、2 FAIL** |
| VP-04 历史只读审计 | 0 | 原件不变、6/10、C05/C06/C07 未试、HEAD 漂移已说明；旧原包不被追认 |
| VP-05 真实入口重放 | 适用 | 修改前诱导文字出现、修改后消失；合成 claim_id 正向可见 |
| VP-06 保护范围和副作用 | 适用 | 上一包固定17文件SHA无变更；未提交/推送、无外部调用/下单，旧桌面/Web未覆盖 |

原始日志：`evidence/VP-01.log` 至 `VP-04.log`，汇总：`evidence/validation_summary.json`。

### 2 项全量失败的根因（不是安全绕过）

1. `tests/test_minimal_research_flow.py::test_chat_selected_pack_switch_and_answer`：旧测试仍要求 `research_case.report_text` 原样包含在面向用户的 `result_text`；新合同 Stage1 明确禁止直接发布这类未经新统一门核验的文本。
2. `tests/test_printer_decision_plan.py::test_chat_result_contains_same_plan`：旧测试仍要求 `shared.decision_plan.text` 原样呈现在 `result_text`；新合同同样要求隔离为未核审计，不能把全文直接显示成已验证解释。

**决定：不恢复不可信直通文本，不擅自改动合同白名单以外的两个旧测试文件，不掩饰全量测试失败。** 这是规范切换时的测试冲突；评估者需明确批准对这两项旧断言改为：原始文案留审计、用户展示只接受门禁模板 / 待核，并冻结相应验收和白名单后，才能由执行者完成全套绿灯。

## 4. 变更范围、限制与下一动作

本包代码：修改 `shopping_decision/chat_bridge.py`；新增 `tests/test_publication_entry.py`、`scripts/audit_model_history_readonly.py`；新增本 `REPORT.md` 与 `evidence/`。只允许按已冻结合同工作，没有修改旧测试、旧冻结审计、父包材料、瓶颈图、桌面和 Web。

`CURRENT.md` 记录 **执行受阻 / 不满足 AC-05**，不自行签 `PASS`。评估者应先判断旧测试的保护目的，在新合同范围内允许最小修改两项“原文必须可见”的旧断言；随后执行者复跑 504+ 项并交独立复核。若评估者不同意更新旧测试，当前不可同时满足“旧原文必须出现在 result_text”和“未核原文不得作为商品结论直通”的两个要求，必须保持阻断。

## 大白话总结

现在普通聊天也挡住了“1300 元明明超过预算，却让用户立刻下单”的错误话术，没证据就说待核。旧模型调用记录查清楚了：六次尝试留存，三组用例没做，历史文件没被动过。但有两个老测试还要求把以前那段未经审核的推荐原文放回用户界面；这和新安全要求冲突。我没有为了刷绿灯把风险放回来，这两条需要评估者批准更新测试后再继续收口。
