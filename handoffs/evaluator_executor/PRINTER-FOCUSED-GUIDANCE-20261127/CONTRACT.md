# Frozen Task Contract：有据且聚焦的打印机引导

Task ID: PRINTER-FOCUSED-GUIDANCE-20261127
Task name: 每次讲清一个会改变决定的问题，并验证是否减少无效交互
Task kind: capability_experiment
Risk: L1
Contract state: CONTRACT_FROZEN
Branch: 当前分支沿用，不建新分支、不提交
Baseline HEAD: c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f
Pre-existing changes: BASELINE.json逐文件记录现有脏工作区；全部继承，不归为本包增量。

## Strategic basis

Project map: docs/PROJECT_BOTTLENECK_MAP_CURRENT.md
Map revision: r44
Active bottleneck: B05
Hypothesis: H-B05-FOCUSED-GUIDANCE-01
Measurement status: measured
Metric baseline: 旧包独立675回归、6复合留出与原生链；六组已知答案全字段注入对照全部持平。当前guide固定展开5维度且路线evidence_ids为空；新任务层交互基线需先重放测量，不冒充已测。
Estimated affected scope: 本地打印机粗需求到路线/适用候选/下一补证步骤；限已有两型号研究样本，非市场覆盖或真实购买。
Expected project impact: 在同资料同任务下减少与目标无关的必要答复及重复追问，保持证据正确性、本人确认和明确未知。只声称离线流程效果，不声称真人学会或真实模型改善。
Rollback condition: 代确认、硬条件绕过、来源造真、旧授权复活立即关闭新聚焦路径；保留旧明确需求入口和审计证据，回滚不抹失败。
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE
Expected material cost: 至多240有效小时/8集中纠错；独立验收建议20小时。主要成本是公平测量、来源适用审核和原生窗口验证，不以小时数作成果。
Bounded retry / iteration budget: BUDGET.md的12个累积检查点；达标提前交，48小时信号门槛和连续两轮无净进展停止优先。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 至少24对同口径任务、4次测量灵敏度挑战、12条新增复合链、至少10原生事件链；未来Evaluator另选8独立留出。保留旧20链回归意图。
Max total attempts: 匿名查询8、执行读取24、独立读取8；无真实模型尝试。
Max parallelism: 1
Max attempts per unit: 同URL同定位失败最多2次；本机同一高成本验证失败最多8轮集中修复，便宜定位可汇总。
Retryable failure families: 公开传输超时/缓存失败；本机确定性缺陷有明确解释时修复。付费墙/登录/用途不符不绕过。
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/PRINTER-FOCUSED-GUIDANCE-20261127/evidence/executor/operations.jsonl
Expected value of another round if successful: 先由Evaluator看收益幅度及维护负担，再决定真人理解或真实模型实验是否值得另行授权。

## Single objective

把“有据认知”从一整段静态导览变为当前决定所需的一次简短解释和一次明确询问，在现有会话、模型上下文、Windows窗口、恢复和决定说明中使用同一个当前问题。通过真实产品重放验证它是否减少无效交互。**唯一主改变是按当前已确认需求选择并解释下一认知问题。**

本包不是增补百科、通用检索平台、第二会话引擎或新的成本求解器。资料增量、旧缺陷修复与问题组织收益分别计。完整12阶段见WORK_BREAKDOWN.md；顺序相连不逐阶段等授权。

## Carried review corrections

| 原包/缺口 | 本包有限处置 | 回归及预算 |
|---|---|---|
| COGNITION-FIRST AC-11，start前初读缺失 | 旧过程缺口永久保留；本包实时活动账；未知段只记未知，使用保守上界控制预算 | VERIFY_DELIVERY，≤6小时工具和记录配置 |
| 原报告标准结构与EV映射不全 | 不改旧REPORT；本包标准逐AC交付、命令原件引用 | REPORT/标准runner/工作流检查，≤4小时 |
| 六组oracle全字段注入，不能区分引导效果 | 冻结同任务、只答当前问题的重放；A/A、错问题、隐藏答案和换资料挑战 | MEASUREMENT及24对任务，前24小时先解决 |
| 来源来自执行者取证文件的精确哈希，运行依赖交接目录 | 可将已核最小来源记录迁入knowledge；保留旧review定位与SHA，不复制全文、不扩大批准命题 | 双臂同资料、缺文件/改版本/撤回回归，≤12小时 |
| guide部分维度无源，路线未连接依据 | 先标逻辑定义/用户选择/专业事实各自性质；仅有足够材料才增加解释和适用倾向 | SOURCE_PLAN语义核验；不凑强制行业结论 |

旧L2/L3 FAIL与拒绝不追认。新包不是重置旧180小时：新假设、新测量和新产品增量单列，新240小时仅覆盖本合同；累计项目投入因旧缺口仍未知。

## Acceptance criteria

### AC-01
Type: 来源正确性。
Given: 已核HP/Brother/RTINGS最低集及有限补源。
When: 聚焦解释、路线倾向或参数参考出现。
Must observe: 每个专业判断有条件、正反依据/限制、原文定位、来源组、发布与获取日期、复核期限或失效条件；事实/逻辑定义/用户选择/个人假设分型。至少3条既有可复核主张保留，补源不按数量刷分。
Must not observe: 无源建议值、把方法当实测排名、广告当共识、以active或域名自证、用型号例子覆盖全品类。
Evidence required: source-audit.json与最小公开取证账、Evaluator逐主张核读。
Mandatory: yes

### AC-02
Type: 下一问题的业务正确性。
Given: 粗需求、明确专家要求、在家彩色、彩色可外包、扫描/双面、使用间隔未知等冻结任务。
When: 正常聊天或guide刷新。
Must observe: INTERFACE规定的guidance_focus_json与当前prompt同源；仅一项当前问题，说明为何会影响决定、什么由本人决定、什么需商品证据，明确下一步与未知；已确认条件不重复问；用户可看完整指南或跳过。
Must not observe: 为少提问而隐藏硬缺证、强行填0/否、所有场景固定问一个因素、要求先填维护费或真实产量。
Evidence required: VERIFY_FOCUS与12新增任务链原件。
Mandatory: yes

### AC-03
Type: 本人确认与同源状态。
Given: 查看/点参考/提交/暂缓/撤回/更改已有硬要求。
When: 实际产品入口执行。
Must observe: 查看和草稿不改状态；发送后才确认；已确认/暂缓/撤回分开；至少彩色路线和一个有源场景因素改变路线解释或具体补证；反应来自原会话状态。
Must not observe: 引入第二权威用户状态、模型或指南代确认、弱偏好升硬条件、静默覆盖旧答案。
Evidence required: bridge真实stdin、模型上下文、决定说明、Java事件一致性。
Mandatory: yes

### AC-04
Type: 比较和研究任务的因果连接。
Given: 已确认路线要求与已有候选事实。
When: 改答或补证。
Must observe: 先路线、再硬条件、再适用候选和显式成本假设；黑白两候选不覆盖必须在家彩色时返回候选集合不适用；缺件是具体命题/来源类型/成功失败两分支；旧维护/主机价/随箱行动反例继续正确。
Must not observe: 软成本复活硬失败、单候选待核称可买、用general claim替代型号事实、给实时价格/库存造真。
Evidence required: 旧VERIFY_ACTION/VERIFY_BUSINESS/12案及新增任务链。
Mandatory: yes

### AC-05
Type: 协议、模型输入及错误恢复。
Given: 真实guide和普通聊天；坏类型/重复键/超界/陈旧提案/资料注入。
When: 真实stdin、当前context_builder或受控transport使用。
Must observe: 新focus上下文与guide版本、state版本、来源状态绑定；受控模型仅允许解释/排序，缺必要依据或超预算安全回退；真实模型调用0。
Must not observe: 只造JSON未被产品消费、外来文字成为指令、原始模型文本当权威、错误丢当前状态。
Evidence required: 冻结探针、专项测试、受控上下文原件。
Mandatory: yes

### AC-06
Type: 失效与恢复。
Given: 同ID新来源版/撤回/日期/地区变更，保存0/未知/暂缓/撤回。
When: 本人另存、全新进程恢复、聚焦问题重算。
Must observe: 仅依赖结果失效；保留独立事实和本人原话；focus/current context/决定说明重新计算；冲突先明确确认。
Must not observe: 旧问题缓存/赢家/可信指南文字/购买授权复活，URL或文件内容执行，坏文件破坏旧文件。
Evidence required: 新进程stdin、取消/失败原件及原生链。
Mandatory: yes

### AC-07
Type: 现有窗口端到端。
Given: 现有Windows JDK/Python，无新安装。
When: 普通按钮和输入事件走桥到同一Python。
Must observe: ≥10条带编号原生链，包含粗需求聚焦、明确确认、来源失效、新进程恢复、取消/坏值/迟到回执、新会话和说明预览另存；无需第二应用。
Must not observe: 反射注入结果、helper替代窗口、SKIP当通过、暗中保存私人资料。
Evidence required: VERIFY_NATIVE原件、事件→请求→引擎→显示字节链及摘要哈希。
Mandatory: yes

### AC-08
Type: 公平测量的可辨识性。
Given: 冻结B0与B1共同修复/同源基线、24合成任务及同一回答能力。
When: A/A、故意错误问题、隐藏答案和资料差异挑战及真实A/B重放。
Must observe: 测量器能检出已知劣化和资源差异；每次只答实际当前字段，参考与目标在运行前冻结；两臂同源同预算同目标；新来源和修复收益单列。
Must not observe: 枚举oracle批量注入、目标来自被测函数、只削弱A、只给B新资料、把阅读/引用数量当主要收益。
Evidence required: MEASUREMENT指定事件账、24对原件、challenge-results与VERIFY_MEASUREMENT重算。
Mandatory: yes

### AC-09
Type: 任务层效果与诚实结论。
Given: ≥24公平配对及12新增完整复合链，旧20链意图保留。
When: 汇总正确性、关键因素遗漏/保留未知、无效答复、重复追问、额外阅读与错误。
Must observe: 所有安全关键样本通过，新增至少11/12且核心全过；24对完整不挑样，报告改善/持平/退化及实际代价；无收益也如实交付。Evaluator另8独立留出不混分母。
Must not observe: 强制正收益刷分、只用字符数称理解改善、伪造真人/模型结果、未知全部当错误或全部当正确。
Evidence required: 独立参考、原件重算、COMPARISON；真实用户/模型收益明确未证。
Mandatory: yes

### AC-10
Type: 工程与历史保护。
Given: 当前继承脏工作区和完整675行为。
When: 完整冻结计划、HEAD/索引/保护件与模型历史核对。
Must observe: 全量与旧关键回归无安全语义删减；新Java仅精确SHA候选兼容；6次安排/结束、0接受及C05/C06/C07未试保持；原合同/基线/报告/拒绝原件不变。
Must not observe: 修改旧验收器/历史manifest、通配放行、删除/skip刷绿、新依赖或Git索引操作。
Evidence required: 标准L2/L3、VERIFY_SCOPE、历史审计。
Mandatory: yes

### AC-11
Type: 过程、权限和交付。
Given: BUDGET与AUTHORISATION约束。
When: 开工到交付。
Must observe: 实时start/end与外部每次start/finish；已知区间、未知段、命令时长和预算保守上界分开；逐AC报告/原件/摘要可复算；旧工时缺口永久保留。
Must not observe: 补造过去时间、把会话经过当有效工时、失联自动重置预算、擅自账号/模型/交易/外发/提交推送。
Evidence required: VERIFY_DELIVERY、日志、标准报告与范围。
Mandatory: yes

## Allowed scope

精确名单以VERIFY_SCOPE.py及BASELINE.json为准。可改原有shopping_decision/{chat_bridge,dialogue_flow,research_router,cognition_guide,guide_binding,cognition_comparison,confirmed_comparison,context_builder,action_ranking,decision_actions,decision_worksheet,decision_note}.py；可新增focus_guidance.py一个薄模块。复用原事实/状态/规则，不复制第二引擎。
可维护knowledge/{printer_cognition_guide_v1,printer_cognition_comparison_v1,printer_selection_criteria,source_directory}.json，可新增printer_guidance_sources_v1.json保留必要来源记录。
Java可改ShoppingDecisionDesktop/DesktopBridgeClient/CognitionGuideRegression/CognitionGuideSwingRegression，可新增FocusGuidanceRegression/FocusGuidanceSwingRegression。旧Chat与Worksheet回归只读。
可最小迁移原15个明确测试（见scope），新增test_focus_guidance.py、test_focus_guidance_bridge.py、test_focus_guidance_lineage.py、test_guidance_replay.py。不改变旧安全期望来迎合新代码。
scripts/audit_model_history_readonly.py仅允许增加本包当前Java/桥/状态精确字节的兼容候选；旧锚点不改。
可改CURRENT/README本包REPORT/COMPARISON/USAGE与evidence/executor；Evaluator写本包REVIEW/evidence/evaluator。新冻结合同/接口/计划/探针/基线/夹具均只读。地图仅Evaluator可改。

## Exclusions and forbidden side effects

不扩真实品类/实际候选型号，不开发平台核价或账号自动化，不做通用区间成本引擎、向量检索、第二应用或第二用户状态。不搬入第三方源码/数据，不修改别仓。旧材料及旧错误账只读；本包A基线只在临时只读副本重放，不回写原件。
模型API/CLI、平台业务API、账号/设备/采购/安装/付费/消息/上传/发布/加购/填单/订单/支付/退款/Git提交推送索引历史改写全0。公开资料只能必要匿名读取，条款不符停。私人保存仅本人显式选择的新本地路径。

## Validation plan

Validation plan file: handoffs/evaluator_executor/PRINTER-FOCUSED-GUIDANCE-20261127/VALIDATION_PLAN.yaml

精确argv见计划；新focus探针、来源和重放审计、新四专项、旧guide/context/行动/业务/12案、全量、历史、Windows原生、范围、完整交付全部mandatory。前测真实失败保留，不将旧工时失败机械移作新目标，也不删除其历史。L2未全过保持EXECUTING/Executor，不自行提交通过。L3必要但不替代来源语义与独立留出。

## Authorization

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_existing_local_model_cli: false
authorization_platform_business_api: false
authorization_public_research: true

用户当前只要求评估并制定下一包；Executor仅获本合同本机实现和有限匿名研究范围。240小时是上限估计，不是外部副作用或实际持续运行承诺。阶段可连续推进，无需重复确认。

## Stop conditions

24小时测量不能检出故意劣化/答案泄露时，停止产品实现，交测量断点；不拿失灵指标推动功能。48小时无一条同材料任务层正向信号，只允许一轮说明理由的局部调整；仍无信号即停止扩张并报告持平/退化。连续两轮无净进展、240小时/8轮任一到限均停止交真实断点。不得为用满预算等候或制造工作。
范围/假设/验证语义/依赖/副作用需要变化时返回Evaluator；缺现实来源停该源分支，保留未知继续工程；出现安全关键错误先关闭新路径修复。早期共同基线新增非继承失败先定位，不改参考答案。来源额度或同定位失败上限到即止。不存在“新开同类包重置预算”的默认权利。

## Amendments

None。补充解释在USAGE记录；改变本合同的行为/验收/范围必须Evaluator显式修订，保留前版和SHA。
