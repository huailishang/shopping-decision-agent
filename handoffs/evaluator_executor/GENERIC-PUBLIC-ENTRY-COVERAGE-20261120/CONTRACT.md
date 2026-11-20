# GENERIC-PUBLIC-ENTRY-COVERAGE-20261120｜正常聊天入口发布门禁（冻结合同）

- 版本：evaluator-executor-workflow/v2.2
- 状态：CONTRACT_FROZEN / READY_FOR_EXECUTOR；责任：Executor
- task_kind: repair；主瓶颈 B06；前包评估：GENERIC-EVIDENCE-CLAIM-GATE-20261119/REVIEW.md
- 起始本地 HEAD：53fa539bacde631d2359781a61566bc1a1395e5a；不重置/覆盖既有未提交改动
- 权限：offline code/tests only；禁止模型调用、公共网页、商品平台 API、登录、下单、支付、Git commit/push。

## 项目判断与主目标
现有主链是需求→证据→有条件比较→用户可见结论→反馈→购买前复核。新 claim_gate 在规则/模型/手工矩阵的新离线出口已经过 12/12 专项与 497/497 全量独立测试；但是 chat_bridge.py 的正常 result_text 仍拼接旧 recommendation.reasons、shared.decision_plan.text 和 research_case.report_text，desktop_bridge 和 web.py 也有单独输出路径。B06 已缩小但尚未闭环；B01 的河南现价、准确型号微信复用、真实效益尚无新证据。

**唯一主要改变**：让正常聊天的用户可见结论必须经过同一确定性发布边界，或明确降级为「待核研究」，不得将手工/模型自由文本当成已核结论。此次先修聊天出口，旧桌面/Web 只清点不改。

## Stage 0：固定复现与出口清单
- 在新增测试里固定同一用户需求、正常和恶意文本样本，记录既有 render_chat 的 baseline，以及存在/缺失的 typed facts。
- 清点 chat_bridge.result_text、desktop_bridge、web.py、model_comparison 的直接展示路径；标注本包唯一正式接线的聊天入口和未覆盖路径。
- 输入是本地合成数据，禁止抓新来源或伪造真实微信、河南价。

## Stage 1：一处通用聊天发布适配
- 允许在 shopping_decision/chat_bridge.py 及必要的 claim_gate.py 通用辅助函数中新增单一 public_decision 适配器，已验字段只能来自 publish_checked_comparison 输出的 claim_id、status、rule_expression、source/limit 和受控模板。
- 用户填写的条件、待追问和编辑状态可继续由对话逻辑正常展示，但必须与“商品事实已核”的显示隔离。
- 旧研究文本若没有可靠的 typed bundle（准确 candidate/dimension/source/time/region），不得转成 VerifiedClaim；显示未知/待核和下一查证行动，不捏造来源时点/地区价，也不能只靠“仅供参考”字样为错误肯定结论洗白。
- 任何 raw model summary、research_case.report_text、人工 decision_gain 不得作为对外已验结论；已知恶意“1300<1000”“立刻下单”不能留在正常聊天 result_text 的已验区域。
- 交易、购买许可、实时价格已核标志继续全部 false。保留内部 report_json 审计字段，标记 legacy_unverified_research，不能影响公共已验文本。
- 不为某个打印机型号、微信、河南特化通用函数。

## Stage 2：历史审计定位小修（随包带入，不占第二能力假设）
- 旧 VP-04 在旧 HEAD ce34764... 与现 HEAD 53fa539... 对比处提前报无描述断言，不能再把任意 exit 1 当成“旧 C05,C06,C07 缺测”的证据。
- 新增只读 scripts/audit_model_history_readonly.py，直接读取历史 FROZEN_INPUTS、受保护 SHA、cases.json、原始 attempts 事件及 meta，不修改旧审计脚本、冻结文件或历史账；核实历史 6/10 尝试、C05/C06/C07 缺测和当前 HEAD 漂移，并输出清晰证据状态。篡改、缺配对、SHA 不一致必须失败。
- 原 GENERIC-EVIDENCE-CLAIM-GATE 包正式 REJECTED 不追认 PASS；本项只能证明旧账未被改和缺测事实，不证明真实模型成功。

## 原子验收
- AC-01：真实 render_chat 的用户已验文本经过统一 claim_gate，未具证据的结论降级 unknown；至少一个合法合成正向结论能通过并具 claim_id。
- AC-02：超预算反说、伪 research 购买行动、系列/搜索摘录冒充准确型号、旧/外区价格、新事实撤销和用户改答都不能升级已验；不泄露未验诱导文字。
- AC-03：原聊天需求、澄清、改答、无资料、非打印机提示不回退；报告/待核与已验边界明确。
- AC-04：历史只读审计能检出受保护 SHA、6/10、C05/C06/C07 缺测及 HEAD 差异，有篡改负测；旧审计仍维持原貌。
- AC-05：新专项、旧 claim_gate 12项和全套测试 exit=0；保存可重放输入、实际展示、原始命令输出/退出码和范围差分。
- AC-06：不修改所有父包原件及旧 r35 瓶颈图、不推送/提交/调用外部/交易；明确未覆盖旧 desktop/Web 入口。

## 文件与预算
允许：shopping_decision/chat_bridge.py；仅在必要时最小修改 shopping_decision/claim_gate.py；新增 tests/test_publication_entry.py；必要时最小改动既有 test_chat_bridge.py / test_claim_gate.py；新增 scripts/audit_model_history_readonly.py；本包 REPORT.md、evidence/ 及 CURRENT.md 状态。desktop_bridge.py、web.py、旧审计脚本、历史报告、父包冻结文档、旧模型账和 docs/PROJECT_BOTTLENECK_MAP.md 不可修改。

预算≤5有效小时、≤2轮集中离线修正，0 外部调用。旧数据无法准确映射时可安全降级，但不得靠虚构 typed fact 追求“正向通过”；阻断则提交真实差分并停止。完成仅代表主聊天入口封闭 B06 的该段，不等于所有 UI 全部改造或商品可购买。

## 大白话
上一包修好了审核答案的机器，但平常聊天还没真正经过它。这包让聊天也必须先审核，证据不够就说待核；再把旧模型账到底为什么失败查清楚，保留历史记录。