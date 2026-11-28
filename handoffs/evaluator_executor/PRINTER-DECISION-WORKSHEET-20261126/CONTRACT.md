# 冻结执行包：让家庭在现有入口完成可更新的打印机决定

Task ID: PRINTER-DECISION-WORKSHEET-20261126
Task name: 会话、来源和成本决策工作单贯通现有聊天与Java桌面
Task kind: capability_experiment
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f
Validation plan file: handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126/VALIDATION_PLAN.yaml
Pre-existing changes: 接收当前全部未提交产品/测试、原型与历轮证据，以BASELINE.json记录为准；不回滚、不提交、不改索引。
制定日期：2026-11-26；角色 Evaluator；唯一下一责任 Executor。

## Strategic basis

Project map: docs/PROJECT_BOTTLENECK_MAP_CURRENT.md
Map revision: r41
Active bottleneck: B05
Hypothesis: H-B05-USER-WORKSHEET-01
Dispatch mode: SINGLE
Measurement status: measured
Metric baseline: 既有成本翻转可在render_chat显式Python参数发生，但普通main/Java桥无工作单或成本录入协议；新增preparation实测为唯一前测，不虚构用户成功率。
Estimated affected scope: 本地打印机原家庭及12条完整任务链，不能推广到其他品类/真实用户群。
Expected project impact: 至少10/12链完成且8条核心链全成；规则结果同输入等价，用户无需修改Python调用即可编辑、恢复和重算。
Rollback condition: 安全核心回归、同输入失真、只做helper或依赖第二引擎时停止扩张；新功能可默认关闭，保留旧入口。
Expected material cost: 主动工作≤120小时，独立复核建议12小时；模型和业务API0；匿名查询≤10、来源读取≤32（执行24、评估8）；不安装新依赖。维护复杂度中等（估计），不编造业务ROI。
Bounded retry / iteration budget: 最多5轮集中纠错，总主动时长120小时，达到充分证据立即交，不凑时长。
Attempt execution mode: SEQUENTIAL
Max total attempts: 来源读取32；查询另限10；同一URL同一定位失败至多2次。
Max parallelism: 1
Max attempts per unit: 2
Retryable failure families: 临时超时、缓存失败；权限、型号不适用、缺许可和无决定性内容不盲重试。
Stop-on-sufficiency: true
Attempt ledger: 本包evidence/executor/operations.jsonl，独立另账；每次开始先记，结束追加状态，不改历史条目。
Expected value of another round if successful: 先由独立评估再判断B01真实材料/用户验证是否应升为第一，不自动续建框架。

## Single objective

原河南低频家庭通过现有聊天及Java桌面，在本机完成“确认需求→查看候选与缺件→录入有类型的成本假设/来源材料→同口径重算→只改一项看翻转→显式保存→恢复后按当前条件/时点重算→知道唯一下一步”的一条决定。来源不足仍可完成清楚的待核决定，不能冒充可购买。

单一主改变是用户可编辑的本地决策工作单及薄接线。复用confirmed_values、decision_actions、claim_gate、cost_scenario和已有Java聊天；禁止再造推荐框架、第二会话状态机或第二事实门禁。成本、来源和当前需求建立联系，但工作单不能改写已确认需求、资格或交易授权。

这是一个覆盖完整交付的长包，不是120小时等待任务。下面阶段可按真实依赖调整，阶段结束不等待负责人再批准；缺外部材料只停其支线，继续其余工作。每个检查点交能运行的证据，不交空目录。达到验收可提前交，不能因“包要长”填充无用文档和测试。

## Carried review corrections

| 原包与失败 | 有限修复 | 聚焦回归 | 预算 |
|---|---|---|---|
| SESSION-COST-EVIDENCE / AC-02，有限字符串1e1000000使两入口decimal.Overflow | 成本数值/精度/数量级在组件边界约束，明确错误并保留规则决定，不静默归零 | 默认与后端实际render_chat；普通、未知、非有限、负数、超界相邻值 | 阶段A内≤4小时 |
| 同包 AC-04，reasoning内部未支持function_call被跳过且排序接受 | 定义支持的reasoning/summary/content形态，递归或结构化拒绝未支持执行内容；两协议兼容合法元数据 | 纯文本、普通reasoning与扩展元数据正例；嵌套工具/函数/refusal及错误类型负例；实际入口回退 | 阶段A内≤4小时 |
| 同包 AC-08，主动工时与9次来源精确时点缺失 | 新包实时记本轮操作和主动段；保留旧缺口，不修造旧时点 | operations与active-time可按原始开始/结束重算，失败也计次 | 全程，不单开修复包 |
| 同包工作流格式未被标准校验器识别 | 本包标签/计划/原生runner完整，执行者不得改上包冻结合同 | 新包标准结构校验；旧错误及7/7并存 | 本包准备与收尾 |

先解决影响安全和测量的修复，再冻结共同“修复后直接规则入口”比较基线。修复收益单列，不算作工作单主改变的增益。旧REJECTED及其原件不追认。

## 阶段A：接手、反例修复与第一粗链（累计8有效小时）

先读CURRENT→本合同/判据/计划→r41地图→上一包REVIEW与两个独立反例。核BASELINE SHA、HEAD、索引及保护集合，运行VERIFY_SCOPE --phase start和VERIFY_BUSINESS，保留实际首轮失败，不重建假前测。用户工作区不得清理。

先收敛两项边界。明确支持数值上限、精度、页数/期间和费用单位；采用合理可解释的本机保护，不只catch一条异常。有限但不可处理值按输入错误报告，未知仍未知，零值仍合法。保留普通回执、合法reasoning与供应商元数据；工具字段及嵌套含义不得被正常文本掩盖，没有任何工具执行或重试。

第4小时保留两入口反例处置和已跑焦点回归；第8小时交现有桌面/桥→工作单草稿→同一比较结果的粗链，至少能操作一个成本变量并在现有result_text看见数值变化。还没有完整恢复/核源时如实标注，继续后续阶段，不能停在设计。

## 阶段B：最小工作单与稳定输入协议（累计24小时）

工作单是数据载体，不是已算结果或新规则系统。至少包含schema版本、本机工作单标识、绑定当前会话与确认摘要、候选集合、成本口径、各值及来源类型、必要来源引用、撤回/版本状态。明确字段是用户需求、用户情景假设、已审厂家事实、未审外部摘录、动态报价线索还是未知；不能互相替代。

缺值是未知；显式0是输入；暂缓不是否；撤回移除适用条件但保留独立事实。工作量、期间、币种、费用范围和情景版本必须一致才能比较；保留独立鼓、初始鼓及满寿命假设，不把标称量当实际产量。工作单允许完整合成正例，但清晰标成假设；默认原家庭不用假价格填空。

定义一个有界UTF-8本机输入协议，复用 `python -m shopping_decision.chat_bridge --worksheet-stdin`。stdin JSON包含 `schema_version=1`、`action`、`state`、`worksheet`、`payload`；至少 `action="create"` 且worksheet=null/payload={}创建工作单并返回现有tab/base64格式的原结果字段及 `worksheet_json`。后续编辑、撤回、预览/恢复动作及payload由执行者在本包USAGE冻结说明，保持单一协议；旧三参数base64调用继续可用。

读入大小≤256KiB、集合和嵌套有界；不采用eval、pickle、可执行脚本、远端URL自动抓取或任意路径include。JSON根对象、版本、重复关键键、错误类型和未知动作有明确错误。外来 `state` 经过已有状态校验，不允许载入工作单反写用户需求或购买授权。桥错误可读、可恢复，不吞异常伪造成功。

第24小时交协议/状态迁移简明说明、直接规则与工作单同输入结果对照、输入/输出原件；对错误保留当前有效会话，而不是整会话消失。

## 阶段C：现有Java入口可操作（累计44小时）

在现有聊天窗口增加必要的“成本与资料”操作，复用DesktopBridgeClient及现有后台线程/超时机制，不建新桌面或网页。普通用户无需写JSON、调用Python或编辑知识文件就能设用量/期间、输入两款假设主机/耗材/维护值、清空为未知、改一项并重算。输入字段用业务名，说明单位、总量或月量的区别。

草稿未提交不生效；明确提交才更新工作单。取消编辑保留旧决定；主窗口继续可用；后台旧请求完成不能覆盖新会话/新工作单。失败/超时/损坏输入有明确恢复操作。减少复杂度时优先完成核心字段和路径，不先装修。

Java只传结构化输入、显示Python返回结果，不自行重算资格/成本，不解析自由文字决定逻辑。默认不存盘、不打开浏览器、不联网；本人点击保存/导入才发生本地文件动作。留现有正常主入口的真实窗口或程序化Swing操作证据；只有桥单测/截图/反射改控件值不等于完整可用路径，需实际调用事件→桥→显示。

第44小时检查：在未修改测试helper的正常窗口中完成一次同口径成本翻转，并保留字段输入、提交、桥请求、返回和展示。如果仍需Python参数注入才可用，不能用更多helper或文档掩盖；先停止装饰，记录断点并在本包剩余额度内收敛。

## 阶段D：来源类型、决定性补证与局部失效（累计68小时）

先复用本轮独立复证的HP必要原文及型号裁图，保留新/旧获取版本关系，不能将评估者PDF SHA冒充执行者旧获取SHA。再按原家庭第一缺件选择少量决定性官方资料；微信稳定复用、准确耗材配置/随箱量或专业维护评测中，仅查会改变条件或行动的一项优先，不批量搜索品牌排行榜。

公开研究额度执行查询≤10、读取≤24，评估另预留8；open/find/截图/直接下载失败均按次计。每次操作开始前登记URL/目的/时间/剩余，结束追加结果、字节或必要摘录SHA、定位、版本、适用型号/地区与使用边界。同URL同定位失败最多2次，达到证据充分即停，限额或时段到不扩大渠道。无需账号、设备、家人回传才能完成主线。

原家庭用户能在同一工作单看到“当前来源已审/未审/过期/撤回/冲突/型号不适用”，并通过本机资料导入或撤回操作看到影响。导入不是认定真实：文件里的 `review_status`、source_type、合成标签、hash或模型文字不能自我认证；新材料默认待审/情景，只能按明确准入策略消费，不能把自填价格升级为实时权威价。允许本包执行者人工核源后维护已有受审知识包，但须留原文/日期/版本/作用范围和独立复核依据。

来源→事实/成本输入→比较/行动→context的依赖可以解释。撤回/过期/同ID新版本只让依赖结果失效，保留当前用户条件和其他独立功能事实。冲突不得只挑便宜/有利的一边；错误型号隔离好邻居；旧工作单外部URL不触发自动抓取。

获得资料、未获得、发现不适用均需完成输入状态和影响处置。没有新决定性事实可记无新事实，不算工程失败，也不能声称维护费用/真实购买收益通过。专业评测、评论、厂家事实分开；不得复制限制名单源码/数据或安装第三方采集工具。

## 阶段E：显式保存、恢复与重新计算（累计92小时）

本人操作预览/另存，工作单仅保存必要确认、假设及引用，不自动保存对话原文/凭证/网络会话；实际测试使用合成家庭数据。文件选择取消不写；用新文件/原子写入等方式避免破坏已有文件；覆盖要有明确本人动作。默认私有数据放data/private，不入Git、不上传、不带Cookie/API key。

恢复是加载输入后用当前引擎和当前日期重算，不信任文件中的已算winner/claims/public_text/授权标记。过期价、来源撤回、新版本、修改需求、换地区或切品类后，旧成本/行动/context不能恢复为当前结论。版本未知/损坏/超长/恶意路径不崩溃，给出可以从当前会话继续的错误；不执行文件内容。

保存/恢复往返应保留来源类型、单位、0/未知、暂缓/撤回和实际确认；导入含需求时先给本人核对，不能在背景覆盖正在进行的会话。明确定义当前会话与文件需求冲突时采用何者，用户无需理解哈希。关闭再开或新进程恢复有真实证据，不能只在同一内存对象copy一遍。

第92小时交正常窗口显式保存→关闭/新会话→恢复→当前时点重算原件；另给过期、损坏、恶意授权及取消四条负向链。

## 阶段F：家庭可读结果与连续任务评估（累计112小时）

结果首屏先说明当前候选去留、成立条件、最关键正反证据、成本是否可比/哪些是假设，以及一个下一问题或核查。不把几十条哈希、英文维度名、schema或request_id塞进主要决策文字；审计仍可展开。相同状态的默认/后端/工作单结果的第一行动及先决相同。

成本翻转同时在结果和下一行动体现：硬条件未核先核去留；受控满足后显示哪个变量造成情景偏好变化，下一步是确认该假设或收集决定性缺件，不再优先查明确无需且不相关的软功能。平局指出能打破平局的一个变量；都失败结束原比较；单候选仍待核的不冒充冠军。

预先登记12条完整任务链（见EVALUATION），每条保留输入、用户操作序列、期望、实际、版本、准入事实、结果及失败原因。8条核心链全过，≥10/12总体完成；安全核心零错误。链路前测与后测使用相同需求/证据/时点/成本，共同修复基线与工作单路径分开，不把修复收益或assert数量当主收益。另至少4条未参与实现的评估者留出链不混入12分母。

完成定义是“可以通过产品入口完成此任务且结果正确”，不是文字中包含关键词。桥协议、程序化窗口、独立真人体验分级记录；本包只承诺前两者，真人收益/模型质量、token、费用与延迟仍未证。至少有无增益、规则故障回退与有效翻转，不要求每案都有改善。

## 阶段G：一次完整收口与交接（累计120小时）

按冻结计划执行原生L2，不手拼绿门禁。全量、原案、历史只读账、原包关键反例与本包范围均真实执行；旧断言不为刷绿改意图。合理行为迁移仅限白名单内测试，说明旧/新意义，保留安全覆盖。Java编译/桥/窗口证据明确平台、JDK、命令、退出码；没运行不能宣称窗口通过。

REPORT逐项核合同任务、实际完成/部分/未完成、真实原件路径和限制；COMPARISON写12链前后与安全/来源/输入状态变化；USAGE为负责人可直接启动并操作的一页说明。当前汇总从最终原件生成，列原件及生成器SHA、版本、计数依据和前后时点；旧结果不覆盖。CURRENT交Executor提交状态与下一Evaluator责任，未独立评估前不自签整体PASS。

## Allowed scope

精确机器白名单见VERIFY_SCOPE.py的PRODUCT，与本节一致：

- 可改已有 shopping_decision/chat_bridge.py、cognition_comparison.py、cost_scenario.py、decision_actions.py、confirmed_comparison.py、claim_gate.py、evidence_snapshot.py、context_builder.py、action_ranking.py、model_adapter.py、evidence_comparison.py；新增 decision_worksheet.py、worksheet_io.py 两个薄模块。优先复用，不必须两份都建。
- 可改已有 desktop/ShoppingDecisionDesktop.java、DesktopBridgeClient.java、ChatBridgeRegression.java、ChatSwingRegression.java、ChatNativeAuditRegression.java；新增 DecisionWorksheetRegression.java、DecisionWorksheetSwingRegression.java。不得改其他旧Java回归意图。
- 可按真实取证最小维护 knowledge/printer_cognition_comparison_v1.json，并同步受控哈希；不扩真实型号/品类。
- 可改 tests/test_cost_scenario_binding.py、test_printer_decision_journey.py、test_model_receipt_boundaries.py、test_session_decision_contract.py、test_evidence_snapshot_lineage.py、test_action_ranking.py；新增 test_decision_worksheet.py、test_worksheet_bridge.py、test_worksheet_persistence.py、test_worksheet_evidence.py、test_worksheet_journeys.py。
- 可改CURRENT.md、README.md当前启动说明；本包REPORT.md/COMPARISON.md/USAGE.md及evidence/executor。Evaluator写REVIEW及evidence/evaluator。本包合同/计划/判据/验收脚本/preparation/BASELINE及r41地图冻结只读。

## Exclusions

不修改任何旧合同/基线/验收器/失败账/原型/旧汇总；不修改其他仓库、自动化真实账号、持久化会话、设备试打、模型API/CLI/平台业务API、采购/安装、外发消息、加购填单订单支付退款。Git commit/push/history/index均不授权。不复制百度知识图谱、球球、ShopSimulator、EComAgentBench源码/数据。不扩真实品类或另建应用。

不把专业资料、评论、厂家事实、动态报价、用户授权混作一种证据。动态事实仍需未来权威平台实时核验，本包自填数字仅假设。无新模型请求不等于已测模型收益；无真人观测不等于已有选购收益。

## Authorization

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_existing_local_model_cli: false
authorization_platform_business_api: false
authorization_public_research: true

只读公开来源研究、仓内离线实现/测试、本机合成窗口和用户明确选择的本地保存/恢复在本包范围内。不可借工作单入口扩大权限。没有隐藏“最后再确认”步骤；已冻结范围内可连续完成，不为每阶段返回询问。

## Acceptance criteria

AC-01：两条承接反例在默认/后端及实际建议消费安全修复，合法相邻正例保留，无网络/工具执行。

AC-02：工作单完整区分需求、事实、假设、未知与授权；口径/单位/谱系一致，坏输入可恢复，同输入与共同修复规则基线等价。

AC-03：旧桥兼容，新stdin协议真实进程可创建/修改/撤回/预览工作单；现有Java窗口实际事件→桥→正确结果，用户无需改代码。

AC-04：正常入口仅改单变量实际成本分支与下一行动同步变化；硬条件未核/失败优先，平局和单候选合理，不查明确无需的软功能。

AC-05：来源类型、原文/版本/定位与准入状态可见；必要公开取证有界；导入不自证、撤回/过期/冲突/版本变化只失效依赖结论。

AC-06：显式保存/新进程恢复保真且重算；恶意授权、旧结论、损坏/超长/错误版本隔离，取消和写入失败不破坏旧文件或会话。

AC-07：首屏可读、有关键正反证据和一个下一步，12条完整链≥10且8核心全过；修复收益、代码路径、窗口与真人效果分别计。

AC-08：冻结机器检查实际通过、继承611行为、历史和新范围不漂移；Java验证真实执行，无未经授权行为。

AC-09：本轮主动段/外部操作/纠错轮次可重算，失败计数，汇总由最终原件生成，交付文件内容完整，旧缺失不补造。

## Validation plan

执行本包VALIDATION_PLAN.yaml九项命令（含业务探针、五组专项、上一包探针、原案、全量、历史审计、Java/窗口交付检查、范围及过程/配对账检查）。具体argv/期望exit均已冻结。Executor最终用本机技能scripts/run_validation.py --mode executor，Evaluator以相同计划独立--mode evaluator，再按EVALUATION人工判读。

前测应实际暴露承接2反例及新协议缺失，新增专项未实现时计划相关命令退出1是预期未完成，不预先记PASS。执行者不能编辑冻结检查器跳过缺失文件/命令。

## Stop conditions

120主动小时或5轮集中纠错耗尽停止并完整交付；不得自动新开包重置预算。第8/24/44/68/92/112小时保存可接续检查点；超过检查点不抹掉失败，不把墙钟当有效工时。目标达到提前交；长期无净进展则停止扩张，报告具体断点。

来源限额/同定位2次失败停止该支线，主线继续；新付费/权限/安装/外发/真实模型/交易需求不执行，不以等待授权阻断其余已可做工作。需要改假设、扩大白名单、改变强制AC或接第二引擎时交Evaluator重新冻结，不自行改合同。错误数值/回执/导入只能使输入拒绝或规则回退，不能产生网络、工具或交易。
