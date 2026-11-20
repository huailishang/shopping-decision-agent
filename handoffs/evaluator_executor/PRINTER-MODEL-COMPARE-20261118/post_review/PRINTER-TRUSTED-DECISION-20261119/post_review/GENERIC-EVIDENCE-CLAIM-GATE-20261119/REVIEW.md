# GENERIC-EVIDENCE-CLAIM-GATE-20261119｜评估者独立复核（2026-11-20）

## 结论
**任务正式裁定：REJECTED（冻结 VP-04 强制检查未达预期）；核心工程 AC-01～AC-04 的离线受测范围通过，不等于整包 PASS。** 不把历史审计的「任意失败」冒充预期历史失败，也不抹除已证明的局部改进。

项目目标：需求→可靠证据→规则比较→可核发布→反馈→购买前重核。项目已具备需求收集、规则比较及部分商品研究。B06「不可信自由文本可绕过可发布结论」在本包覆盖的规则、模型、手工矩阵和新只读 CLI 路径明显缩小；**主聊天 result_text、桌面 desktop_bridge 的自然语言展示并未调用 claim_gate**，正常消费者入口仍未闭环；B01 型号/微信复用/河南有效报价也没有新验证。

## 独立复测与事实
1. 评估者本机运行 `python3 -X utf8 -m unittest discover -s tests -p test_claim_gate.py -v`，12/12 PASS、退出 0；随后同一环境运行 `python3 -X utf8 -m unittest discover -s tests -q`，497/497 PASS、退出 0（2026-11-20，命令工具实际返回值，不是仅采用执行者报告）。专项涉及超预算反说、自由文本诱导交易、跨候选引用、价格地区与证据等级、撤回重算及合成空气净化器。
2. 独立运行冻结 `python3 -X utf8 scripts/run_model_comparison_experiment.py --audit --task handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118`，**exit 1，输出 `{"status": "failed", "reason": ""}`**，未满足冻结 VP-04 的 `expected_reason_contains: model cases not attempted: C05,C06,C07`。源码 `scripts/run_model_comparison_experiment.py:27-40,135-178` 先执行 HEAD 严格相等断言，当前 HEAD `53fa539bacde631d2359781a61566bc1a1395e5a`，旧 `baseline_head` `ce34764ab7d803b06abbdbcea0afe32048096c0a`；assert 无描述，错误原因被输出为空。不能只凭 exit 1 签 VP-04。
3. 静态独立检查：`shopping_decision/claim_gate.py` 按 `rule_comparison` 的结果重建结构化 claim 和模板文字，`model_comparison.py:155-158,187-190` 只在新增可发布模式/模型成功路径使用；`scripts/verify_claim_publication.py` 三类输入可调用统一门禁。模型原始说明不进入新 PublicDecision（但原始来源内容的外部真实性仍无法离线证明）。
4. 发布覆盖面核对：`shopping_decision/chat_bridge.py:260-314` 的 `render_chat` 将旧 `recommendation.reasons`、`shared.decision_plan.text`、`research_case.report_text` 拼为 `result_text`；`shopping_decision/desktop_bridge.py:62-165` 亦独立拼文本，未调用 `publish_checked_comparison`。旧路径有「不授权购买」提示，但这不等于所有可读结论获得新门禁审核。当前不宣称发现真实用户已被误导；这是尚未纳入统一门禁的明确覆盖缺口。
5. 执行者提供的 `evidence/validation_summary.json` 报告 17 个冻结保护件 SHA 未变、6/10 历史尝试留存和无新外部请求；本轮独立复测没有做新的真实模型、商家 API、购买、Git 提交/推送。外部商品真伪、河南当前地区有效报价、真人选择收益均未独立验证。

## 原子验收
| 项 | 独立裁定 | 理由 |
| --- | --- | --- |
| AC-01 | PASS（限定新发布出口） | 恶意 1300>1000 文字反说被模板发布隔离 |
| AC-02 | PASS（结构化门禁边界） | 证据类型、来源时点、精确型号/区域约束与负例测试通过；不认证来源现实真实性 |
| AC-03 | PASS（合同列明三入口） | 新规则、模型及旧手工矩阵接入同一发布核；正常聊天/桌面旧出口不在本合同覆盖范围 |
| AC-04 | PASS | 独立专项 12、全量 497 通过，离线 CLI 冒烟在专项中 |
| AC-05 | **FAIL（VP-04 强制断言不满足）** | 历史审计提前被 HEAD 不一致拦住，无法仅靠这个正式命令证明预期缺测原因；不得改历史证据、重写 HEAD 或把通用 exit 1 当通过 |

## 项目影响与下一方向
- **瓶颈缩小，但没有清除。** 通用发布核心在可控新出口已成立；最关键的正常会话入口仍直接输出旧研究文字。相比继续公网抓取一批商品资料，优先封住主用户入口的绕过风险，确保将来拿到高质量来源时不会出现「规则和展示各说各话」。
- 下一单包：`GENERIC-PUBLIC-ENTRY-COVERAGE-20261120`，唯一主改变为在正常聊天结果出口建立强制、来源可追溯的可发布/待核分层；旧 VP-04 基线定位以只读法证小修随包带入，**不改旧审计和旧账**。本包原定验收仍保留 REJECTED 记录，新包通过不能追认本包无条件通过。
- 暂不授权真实外部模型/商品 API、账号登录、下单、支付、Git 提交或推送。评估证据不足以判断用户决策收益，下一步只验证发布安全和入口覆盖。

## 大白话总结
新门禁在专门的比较程序中确实挡住了「超预算还说可以买」；我自己又跑了 497 项测试，都是绿的。但是老审计没有在预期的位置失败，所以这整包不能签全过；日常聊天界面也还没用新门禁。下一包先封住真正给用户看的入口，再做商品事实补全。