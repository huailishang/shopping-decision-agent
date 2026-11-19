# 交付格式与独立复核

这是格式说明，不是研究结果。JSON使用UTF-8，引用使用仓库相对路径和SHA-256；执行者只写本包evidence/、COMPARISON.md、REPORT.md。

## attempts.jsonl：外部取证账

每行一个事件。发起前追加`{"event":"scheduled","id":"A01","kind":"search或open","target":"完整查询或官方URL","at":"含时区ISO时间"}`。结束后追加`{"event":"completed","id":"A01","at":"含时区ISO时间","outcome":"success或failure","record":{"path":"本包evidence/sources/A01.txt","sha256":"实际回执SHA"}}`。不改旧行；修正另加说明。失败也留实际工具回执。只保存必要短片段、标题、最终URL、定位、状态/失败，不整站或整本复制，不以回忆补原件。

同查询/URL第二次尝试必须在scheduled事件中加`retry_reason`（timeout或5xx），对应上一次实际失败；登录/验证码/权限拒绝不重试。所有外部事件必须包含在单个acquisition工作段中，≤90分钟；串行执行。

## decision.json：固定需求下的判断

根对象字段：

- `task_id`为本任务ID，`input_basis`为`project_owner_proxy`，`input_sha256`为preparation/confirmed_need.input.jsonl的SHA。
- `sources`列表，可为空。每项`id`、`attempt_id`（成功open）、`url`（官方最终URL）、`locator`（章节/页码）、`retrieved_at`（含时区）、`published_or_updated`（日期或unknown）、`model_binding`（准确型号覆盖依据）、`mainland_scope`（范围依据）、`limitations`（非空）和`record`（同对应completed的文件引用）。
- `facts`列表，可为空。每项`id`、`model_id`、`criterion`（wechat_entry/later_print_steps/current_service）、`finding`（supports/contradicts）、`source_ids`（至少一个）、`statement`、`counter_evidence`和`limitations`。型号/范围不足只在比较中作线索，不进facts。旧说明不支持current_service肯定断言。
- `models`恰好两项，model_id分别为HL-L1238W、M232dw。每项`before`固定pending_evidence，`after`为pending_evidence/conditional_document_support/documented_scope_exclusion之一，`changed_fact_ids`（可空）、`before_action`、`next_action`（具体事项）、`unknowns`列表、`workflow_branches`对象（miniprogram和transfer_to_app分别说明证据、未知、用户接受度未确认）。无facts时after只能pending_evidence；状态变化须有本型号事实。事实增量但状态未变也据实说明。
- 全部固定false：`program_integrated`、`purchase_recommendation_approved`、`transactions_enabled`、`wechat_reuse_verified`、`live_price_verified`、`long_term_reliability_verified`、`real_user_effect_verified`。
- `actual_feedback_count`为0；`questions_prepared_not_sent`为0—3条剩余问题，不重复已确认事项。
- `risk_review`对象：missing_evidence、adversarial_content、stale_price、condition_conflict、accidental_order、wrong_model、setup_vs_reuse、old_doc_vs_live_service八项，分别写实际处理与证据定位；未遇到也如实记未遇到及约束，不造攻击。

## execution.json：实际成本

字段`task_id`、`correction_rounds`（0—2整数）、`historical_effective_hours`（unknown）、`segments`（每段started_at/ended_at含时区，phase为acquisition/synthesis/validation，activity非空）和`forbidden_actions`。段不能重叠，最多一个acquisition段包住全部外部事件。

`forbidden_actions`对象中business_api_calls、credentials_read、messages_sent、device_operations、transactions、git_commit、git_push全部0。门禁尚在运行时，已完成段记到启动门禁；未计部分由门禁meta原件补足，不冒充全部工作时间。

## 白话比较与报告

COMPARISON.md先说明现在能决定什么；两款表格包含微信路径、后续步骤、适用条件、正反证据、来源/日期、未知和下一行动。价格未知不排序预算，不强选冠军，标明“人工研究交付，尚未接入程序”，无实机/真人反馈。

REPORT.md按技能格式填写Task ID、Baseline HEAD、Executor status、工作树前后快照、变动文件SHA、L2 Task Gate、Validation plan、三个EV索引、Impact comparison（同输入前/后/差异/限制）、Iteration ledger、预算用量、偏差/断点。报告引用实际原件，不能提前建“通过”。提交快照列全部交付文件SHA，提交后不可改原件。

## 评估者离线逐源复核（强制）

1. 验提交快照与冻结根SHA，跑同计划evaluator模式留独立L3；自动过关只证明结构。
2. 从每项facts对应的completed回执独立重读：官方最终域名、dw/dwc区分、系列覆盖、大陆范围、原文定位和日期含义。先写支持/反对/未知，再与执行者对照，逐项索引原文和哈希；无法复核的肯定断言不采信，不联网补救。
3. 固定同输入，逐型号重判：仅首次设置/无线，还是支持微信发起及后续步骤；用户方式接受度是否仍未知；changed_fact_ids是否真改变下一行动。不得以字段数、模板覆盖或测试数计收益。
4. 无新增事实但失败账完整，可判任务依约交付、项目无可测收益；有不实肯定断言则对应AC不通过。实机/真人收益仍不可判。
5. 核每次重试对应超时/5xx原件、预算、失败批次与工作段，合并门禁meta核总4小时；越预算为范围违约。给每个AC裁决、项目影响和停止/切换理由。
