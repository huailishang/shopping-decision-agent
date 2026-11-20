# R1 冻结续修执行包｜聊天可信结论与可用研究提示同时保住

- 任务ID：`GENERIC-PUBLIC-ENTRY-COVERAGE-20261120`（延续原任务，不另起并行任务）
- 协议：`evaluator-executor-workflow/v2.2`；任务类型：`repair`；主瓶颈：`B06`
- 状态：`AMENDMENT_R1_FROZEN / READY_FOR_EXECUTOR`；接手：Executor
- 原冻结合同：同目录 `CONTRACT.md`；原验证计划：`VALIDATION_PLAN.yaml`；受阻交付：`REPORT.md`
- 本次中期独立评估：`INTERIM_REVIEW_R1.md`；**本修订仅明确扩大两项旧测试的改动白名单，补充研究提示可用性验收，不追溯修改原始冻结版本。**
- 基线HEAD：`53fa539bacde631d2359781a61566bc1a1395e5a`，含已有未提交、未跟踪实现；不得覆盖/丢弃。
- 本包验证计划：`VALIDATION_PLAN.R1.yaml`，交付：`REPORT_R1.md` 与 `evidence/r1/`，完成后交 Evaluator 独立验收，未获通过不得宣告结案。

## 为什么续修
评估者独立运行`python3 -X utf8 -m unittest discover -s tests -q`：504项，502 PASS，2 FAIL；两条旧断言要求`research_case.report_text`/`decision_plan.text`原样出现在用户`result_text`，违反原包不可直通自由文本的安全约束。同时正常聊天目前一律显示笼统「待核」，未能把2/1/0条有限研究输入和「微信必须/可选」转换为安全、有差异的研究进度/下一行动。

## 唯一主要改变
在**不降低统一claim_gate强制可信发布标准**前提下，为聊天增加**非事实认证的结构化研究进度和安全下一行动提示**，并迁移冲突的两条旧测试，使其不再把“直接透传原文”当作功能正确的标准。

### Stage R1-1：区分三种内容，禁止偷换
1. **用户已确认需求**：可显示在 `understanding`、`editable`，并用于生成规则化研究提示；标识来自用户，而非商品事实。
2. **待核研究进度/下一行动**：允许输出确定性模板，但只接受当前会话确认条件及系统可界定的结构化元数据（如当前研究包待核资料记录条数、是否有资料、明确的`wechat_required`分支）；输出须写清“研究资料未经过最终商品事实核验”。`2/1/0`条是本地资料记录数，不等于有效证据数，更不代表已认证商品。
3. **已验商品结论**：只有 `publish_checked_comparison` 正式接纳的claim允许出现具体比较值/满足或不满足的事实命题；其余一律`待核`。`recommendation.reasons`、`research_case.report_text`、`decision_plan.text`、`next_action`、原始模型答案不得以原文或截断/替换方式绕过门禁。

### Stage R1-2：恢复必要的可用性，不作过度扩大
- `2/1/0`三种已有研究包仍正确选择、计数并保留在`report_json`审计；安全研究进度显示出适当差异（例如“2条待核研究记录”，但不得展示未经核实的型号结论、报价、购买建议）。不能通过伪造typed bundle得到差异。
- 微信确认“必须”时，模板提示“优先查证准确型号从微信发起、后续复用条件”；微信确认“可选”时，模板提示“可继续核实低频印量/耗材/所售型号；微信未核不能代表其余研究失败”；未回答时明确需要澄清。**这些是待办，不是声称设备支持。**
- 修改预算1000→800、修改/撤回微信条件或更换品类，研究提示与用户需求展示必须随当前会话重算，不继续展示过期旧claim、旧研究建议；非打印机仍只收需求。
- 所有用户可见内容不得出现“1300<1000”“立刻下单”“已验证河南现价”这类来自旧未核原文的错误肯定断言；`purchase_recommendation_approved`/`transactions_enabled`/`live_price_verified`仍为false。
- 如无法安全取得记录数，仅显示未知；不得为赶测试而引入模型猜测、厂家系列→精确型号映射或新平台数据。不要增加网络查证、模型适配、GUI/Web接线。

### Stage R1-3：严格迁移两项旧测试
- `tests/test_minimal_research_flow.py::test_chat_selected_pack_switch_and_answer`：保留 `used_facts` 的2/1/0与改答语义；改断言为旧`report_text`只在`report_json`，不直接存在`result_text`；研究记录数/分支安全提示按新模板；恶意断言负测。不可删整个测试或仅改名跳过。
- `tests/test_printer_decision_plan.py::test_chat_result_contains_same_plan`：保留 `decision_plan.current_path=continue_model_research`、未授权交易和用户微信可选语义；旧`plan.text`只留审计；对外只能是门禁事实＋规则化研究待办，不把“同一段原文”作为正确性。
- 扩充 `tests/test_publication_entry.py` 对两种微信状态、2/1/0包、改答、恶意自由文本、合成合法claim进行端到端回归。不能用仅检测某一个硬编码字符串替代行为断言。

## 冻结验收（全部强制）
- **AC-R1-01 安全**：正常 `render_chat.result_text` 仍不能透传任何未核旧文本；恶意预算反说、即时购买诱导、陈旧或外区价都不能升级为已验；合成合法claim仍能带`claim_id`。
- **AC-R1-02 有用**：资料2/1/0与微信必须/可选有安全可解释的研究进度和下一步差异；未知不等于故障；用户编辑/撤回/换品类不能输出过期内容。
- **AC-R1-03 旧测试语义保留**：仅两项明确过时的原文透传断言迁移，保留它们的输入/研究计划/状态验证；不删测试、不skip、不降低全部回归数量。
- **AC-R1-04 测试**：本计划中专项与完整`unittest discover -s tests -q`实际退出0；记录完整输出/退出码；不得用预期失败或忽略失败冒充绿灯。
- **AC-R1-05 历史完整性**：旧模型尝试6/10、未试C05/C06/C07、受保护SHA、历史旧包 REJECTED 状态及HEAD漂移不变；旧案不追认，B01真实收益不宣称获得。
- **AC-R1-06 变更与权限**：不触及历史冻结原件、r35瓶颈图、桌面/Web遗留出口；无网络/模型/业务API/登录/加购/下单/支付、Git commit/push。

## 允许路径与明确禁区
可改：`shopping_decision/chat_bridge.py`（有限模板及受控元数据适配）；必要时`tests/test_publication_entry.py`；**新授权**仅`tests/test_minimal_research_flow.py`、`tests/test_printer_decision_plan.py`内相关测试的最小修订；本包`REPORT_R1.md`、`evidence/r1/`、`CURRENT.md`状态。不修改`claim_gate.py`语义、`model_comparison.py`、`desktop_bridge.py`、`web.py`、`docs/PROJECT_BOTTLENECK_MAP.md`、父包任何冻结证据和历史模型账。

## 有界预算/停止线
继续消耗原包**未使用**的≤5有效小时及≤2轮集中修复总上限，**不重置**；R1至多一次有界集中修订与一轮全量测试，另外必要的专项廉价检查；用量不清先整理原包记录，不能假设有新增额度。0公网、0模型、0真实交易、0提交/推送。若修复必须直通未核文字、扩大新来源、修改受保护文件、或再次两项以外的强制失败仍无解，停止，连同原始输出交回 Evaluator。

## 提交/接手
Executor 仅在本地完成实现和证据，不提交Git；报告列出前后`result_text`与`report_json`对照、全部验证退出码、未完成项、变更清单。Evaluator 独立重跑后方可决定是否签本任务PASS，再考虑 B01 实际商品证据或未覆盖桌面/Web发布出口。

### 大白话
下一轮不是让模型说得更好听，而是保留安全审核的同时，让用户看得懂“目前有几条待核资料、接下来该核什么”。那两条老测试要换成正确的检验方式，但不能删掉。完整测试全部通过并由评估者复核，才算修完。