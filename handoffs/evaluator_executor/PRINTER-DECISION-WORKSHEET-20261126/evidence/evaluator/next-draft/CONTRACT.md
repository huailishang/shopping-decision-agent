# 冻结执行包：让下一步真正指向能改变决定的证据

Task ID: PRINTER-DECISIVE-EVIDENCE-20261126
Task name: 打印机关键假设、翻转边界与最小补证贯通现有工作单
Task kind: capability_experiment
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f
Pre-existing changes: 原样接收本包BASELINE记录的全部未提交实现和历轮证据；不回滚、不清理、不改索引。
制定日期：2026-11-26；Evaluator冻结；下一角色Executor。
Validation plan file: handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126/VALIDATION_PLAN.yaml

## Strategic basis

Project map: docs/PROJECT_BOTTLENECK_MAP_CURRENT.md
Map revision: r42
Active bottleneck: B05
Hypothesis: H-B05-DECISIVE-EVIDENCE-01
Measurement status: measured
Metric baseline: 已有工作单能编辑/保存/恢复；独立维护费干预中700/650变为700/750，赢家翻转但下一步仍核新赢家的随箱量/耗材价。尚无可消费的关键变量、翻转边界或有范围证明的稳定取舍。
Estimated affected scope: 原河南家庭及16条离线完整任务链；不外推真人收益、第二真实品类或真实成交。
Expected project impact: 用户在同一窗口知道先核哪个条件/哪款的哪项假设、改变多少才影响取舍、补充/撤回后能否继续；至少14/16完整链、12核心全过、至少8条真实窗口链，安全错误0。
Rollback condition: 硬条件被成本优势越过、抽样被称全区间证明、来源自证或旧结论复活时停扩张；新分析降为未知并保留旧安全决定。
Dispatch mode: SINGLE
Expected material cost: 上限180有效小时、6轮集中纠错；独立复核建议16小时；已有运行环境，不安装依赖。模型/业务API费用0；执行公开查询≤10、读取≤24，独立预留8次读取。实现和维护成本估计中高，置信度中等。
Bounded retry / iteration budget: 同一包180主动小时/6轮；累计8/24/48/72/104/136/164/180小时检查点；充分即交，不耗满预算。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 每个必要命题取得一份可复核、适用的直接来源即可停止；无材料则完成未知影响路径，不为凑命中消耗额度。
Max total attempts: 公开读取32（执行24、独立8）；查询另限10。
Max parallelism: 1
Max attempts per unit: 同URL同定位失败最多2次；业务页面不转账号/接口渠道重试。
Retryable failure families: 暂时性公开页面超时/传输故障；权限、许可不明、型号/命题不适用不盲重试。
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126/evidence/executor/operations.jsonl
Expected value of another round if successful: 由独立结果决定转B01真人/设备证据准备或停止本地功能扩张；不自动再建一层框架。

## Single objective

让原家庭在现有聊天和Java工作单中完成“确认去留→识别决定性未知/假设→看条件化翻转边界→选择一个值得核的下一步→录入有类型材料或修改假设→重算→保存/恢复并导出可审计决定说明”的连续闭环。没有现实证据时也要给出可继续的待核决定；不替用户购买。

单一主改变：在已有共同规则结果上加入**关键假设分析及其补证行动**，并让结果、首问、上下文、工作单、保存和决定说明消费同一结构。复用现有事实门禁、硬条件、成本函数和工作单，不新增第二推荐引擎、会话系统、应用、事实认证系统或模型接线。

长包覆盖完整业务链与交付，不是180小时等待任务。阶段之间连续执行，不逐段等待负责人批准；缺网页/设备/真人只停相应支线，完成本机可测链。测试数和文档页数不算能力增益。

## Carried review corrections

| 原包/判据/反例 | 有限处置 | 聚焦复核 | 预算 |
|---|---|---|---|
| WORKSHEET / AC-04、AC-07，HP维护0→100使偏好翻转，行动却核Brother随箱量 | 在cost_scenario/decision_actions/worksheet的共同结构中保留决定性字段和目标，不只改关键词 | 正常桥维护费、主机价、随箱量三种单变量干预；默认/合法后端同源首项 | 前8小时以内先保留结果 |
| WORKSHEET / AC-08，旧Java历史固定字节与允许改桌面冲突 | 本次已独立核的两份当前SHA及历史Git原件为继承基线；下一包明确允许最小更新当前版本精确SHA及测试，历史锚点/失败账不动 | 缺历史对象、旧manifest/账本变造、未审当前字节均拒绝；不加路径通配或环境绕过 | 阶段A/C合计≤4小时 |
| WORKSHEET / AC-09，首轮主动工时不可追补，报告结构不合标准 | 开始工作前追加本轮active-session start；结束追加end，未知单列。报告按标准格式逐项对账 | 当前包活动段、外部操作、物料版本、生成摘要和完整runner三件套可重算 | 全程；旧缺口永不抹除 |

共同基线分两层：B0为本包开工前受保护原始产品；B1为有限行动修复后同输入直接规则路径。B0→B1是纠错收益，B1→新关键假设闭环是主改变收益，分别计数，不把一次bug修复包装成全部新能力。

## 阶段A：真实接手、原反例与一条粗链（累计8小时）

读CURRENT、合同/判据/计划、r42地图、上包REVIEW及维护费原始请求回执。先记录活动会话start，运行范围start与准备探针，保留真实失败。核HEAD/索引/保护SHA；未列明的漂移不得默默吸收，保留用户成果。

沿现有Java→Python链，HP维护费0→100后主结果明确是HP维护假设造成翻转；下一步核HP维护，不随赢家切换而丢失原因。主机价和随箱量用相同规则；没有之前编辑事件的直接入口，也必须根据当前声明的分析变量决定目标，不靠记录某句聊天猜原因。

保留旧安全回退、有限金额/混合回执边界和来源准入。首8小时交一条可运行粗链及实际失败/通过；如果仍只给出“建议研究”泛文，先收敛，不装修窗口。

## 阶段B：有边界的关键假设分析（累计24小时）

分析输入只来自当前已绑定的需求、准入来源、工作单假设及用户显式声明的取值范围。未知不是0；单点不是区间；未给范围不凭模型补造。每项含候选/字段、单位、当前值、下界/上界或明确离散值、来源类型、依赖及当前版本。字段仍是个人情景，不能越权改用户硬条件或厂商事实。

先支持一项数值变量的精确分析：主机价、维护总费、耗材价为非负有限金额；随箱量、实际产量及工作量为合法整数；期间、币种、费用范围保持同口径。鼓粉分离和维护条件保留，但不得把厂家标称量默认为家庭实际产量。至少给出维护费50元等价点、49.999999/50/50.000001相邻值，以及Brother随箱量299/300页处的阶跃：不是平滑插值，不用1500这个既有演示点冒充最小翻转点。

可支持最多4项显式变量；不要求通用优化求解器。必须声明证明范围、分析覆盖范围、次数上限和无法证明的原因；连续金额可用精确规则，整数耗材替换用真实阶跃或有界穷举。共享打印量/多变量交互时不能只算两个端点就称整个范围稳定。最多4096次现有成本函数求值，达限安全给incomplete并指出需缩小哪个范围，不无限扫描或假称证明。缺必要输入返回incomplete，保留可以核的行动，不能为了全绿把所有正例都变未知。

至少一个范围内同一候选始终较低、一个范围内会翻转、一个精确平局、一个变量无影响、一个硬缺证优先、一个超证明能力降级。报告只说“在这些已声明假设范围内”；不能给真实购买胜率、无依据概率、收益率或泛化保证。

## 阶段C：共同结果与稳定本机协议（累计48小时）

沿用--worksheet-stdin五字段请求和tab/base64输出。新增action=analyze_uncertainty，payload恰为 {variables:[{candidate,field,low,high}]}；总量字段candidate=null，单款字段用现有完整候选名。1—4项，不重复；字段合法、低≤高、单位及数值边界同旧成本组件。相同低高合法，表示单点；不以随机抽样决定行动。

返回新增uncertainty_json字符串，解析后schema_version=1，包含status、current_preference、robust_preference、factors、next_action、assumption_only=true。factors保留输入candidate/field/low/high及分析适用条件、精确/部分覆盖说明；next_action至少kind/candidate/field/description，缺项可null但理由清楚。status至少区分sensitive、robust、incomplete、hard_conditions_first；invalid/stale可由既有错误字段或独立状态安全拒绝。敏感区间不宣布robust_preference，当前单点偏好与全范围结论分开。纯数值分析不能把硬缺证/硬失败抬为robust。

工作单只保存已确认的分析输入和依赖，禁止把uncertainty_json、winner、public_text、授权存成下次可信结论。旧存档可读；必要时支持显式schema迁移，保留0/未知/暂缓/撤回。旧客户端请求/旧三参数桥不因新增字段失效。

共享decision_actions/上下文/用户主结果消费同一结构，默认与合法后端一致；不得一条路径维护费、另一条路径随箱量。成本分析仅在去留已满足后优先；硬反证先淘汰、全部失败停止比较、单候选待核不强选冠军；未答/暂缓/撤回尊重原共同契约。

## 阶段D：用户能完成的现有窗口（累计72小时）

在现有“成本与资料”内增加关键变量选择、范围输入、分析/提交/取消和结果显示。无需用户写JSON或改Python；字段显示业务名和单位，未知留空且解释影响。主屏先显示候选去留、当前取舍的条件、对结论最有影响的一个变量、其翻转点/无法证明原因和一个下一步。完整来源/范围/哈希放可展开审计，不淹没主屏。

窗口实际完成：选择HP维护0—100→分析显示可能翻转且核HP维护；缩至0—40→仅条件范围内HP稳定较低；Brother随箱量0—1500→找到阶跃；取消草稿不改变已提交结论。过期后台回执、重建、取消、新会话都不能覆盖新状态；异常后能继续。程序化Swing必须真走按钮/输入事件→桥→显示，不能把最终字符串反射填入结果控件。最迟72小时必须有这一条原生粗闭环，否则停止装饰并在剩余额度内收敛。

## 阶段E：最小补证与有类型材料（累计104小时）

每个建议核查动作给具体对象、命题、适用条件、当前正反证据、来源/日期/有效范围、为何会影响决定以及核成/核不成各走哪里。没有可信来源时写明未知；不得用宣传页、评论或自填报价替代厂家事实/实时平台核价，也不把成本分析变成查所有软功能。

原河南家庭先尊重扫描/双面确认及微信/首次设置等硬条件；核不到稳定微信复用就保留待核。复用HP既有必要摘录、裁图与版本SHA，不重下相同PDF。新公开取证只用于当前第一决定性缺件：微信准确适用范围/随箱配置/维护条件/专业评测至多选择必要命题，不搜排行榜凑材料。执行查询10/读取24，评估8读取另留；失败计次，同定位失败2次停。每次操作开始前记目的、URL、时间和余额，终态追加必要摘录/字节SHA、定位、适用型号/地区、日期与限制；不存整份受限资料、不复制限制名单代码/数据。

导入资料默认未审，只能登记待核或用户假设。自称approved、错型号/地区、过期价、来源冲突、广告性评测不能升级。用户可在同一窗口将材料关联到所核变量；关联本身不是认证。已受审来源变版、撤回/过期或需求改动时，只失效依赖的分析/行动/context，独立事实、用户答案保留。外部无法取得不是本机主线停止理由，交出可检查的未知和核查任务即可。

## 阶段F：保存恢复与可审计决定说明（累计136小时）

显式选择新路径保存必要输入、分析范围及来源引用；默认不写盘，不保存凭证/对话原文/账号数据，不覆盖原文件。新进程恢复后按当前引擎、需求、来源状态及时点重算，不能复用旧敏感性、旧赢家或旧授权。坏版本、结构/深度/大小错误、非法范围、恶意路径/URL和缓存结论均安全拒绝或隔离；保留旧会话和已有文件。不同会话需求须先预览和本人确认，不静默替换。

在现有入口提供“预览决定说明→本人选择新文件导出”，只导出本地UTF-8 Markdown或JSON，不联网、不发消息、不打开商家页面。内容包含当前需求/版本、候选去留、正反证据、单点和范围假设、关键变量及证明范围、第一补证任务、来源日期/失效条件、动态价格未知、购买授权false/交易关闭。文件是研究说明，不叫可执行订单/支付凭据；不跨仓调用。不要求新文档框架或第三方渲染库。

导出内容必须从当前同源结构重生成；恢复、需求变化、来源撤回后旧说明不得在产品里冒充最新。合成评测材料明确标注；真实私人资料默认私有路径并忽略Git。本包只用合成个人需求，不读取用户现有私人文件。

## 阶段G：16条完整任务与独立可复核测量（累计164小时）

实施前在expectations.json登记固定16链及期望，保留B0/B1公共基线、相同需求/日期/资料/输入。详见EVALUATION。≥14/16且12核心全过；至少8条原生Java事件链，其中维护费翻转、随箱阶跃、保存新进程恢复、来源撤回必须含窗口。其他可真实stdin子进程；不能全由helper替代。来源受控样本另标，不伪称厂家已确认。

关键度量是“选中的下一行动是否指向决定性对象和变量、证明范围是否真实、补证/改值/撤回后是否正确继续”，不是是否含某几个字。至少一条无增益、一条正确未知、一条故障恢复；留出至少6条由评估者独立选择的复合链，不混分母。源码路径、窗口工程可用、真人可理解、真人收益和模型效果分级记录；本包不承诺真人或真实模型收益，不造时间节省。

## 阶段H：一次完整收口（累计180小时）

运行本包标准runner完整L2，不手拼绿表；旧业务/历史12案、全量、旧历史账、当前范围、Java旧回归及新事件回归、交付摘要全部实际跑。历史兼容只允许保留原锚点后对本包明确修改的当前Java最终精确SHA做候选版本更新，并保留变造拒绝测试；评估者再独立核，不以变量通配免审。

REPORT按标准格式逐项列完成/部分/未完成、原件和限制；COMPARISON列16链B0/B1/新路径、分母、失效/无收益和成本；USAGE给负责人可直接启动和操作的一页说明，不能只给回归命令。原始请求/回执、生成器、摘要SHA及版本可重生成。工作期间先记活动session再开工，结束即记终态；命令时长和主动工作分开，暂停/未知如实保留，不能只汇总同步命令秒数冒充整包工时。

CURRENT在L2未全过时保持EXECUTING/Executor；达标后提交报告供Evaluator接收，执行者不自签总体PASS。旧包拒绝、6次模型尝试/0接受、历史缺口永不追认。

## Acceptance criteria

全部强制；机器计划与EVALUATION的人为语义复核共同裁定。

- AC-01：维护费、主机价、随箱量三类干预的下一行动指向真实决定性对象/字段；旧安全边界及硬条件优先保持。
- AC-02：精确单变量平局/阶跃及合法相邻值可复算，稳定/敏感/未知分开；共享工作量/交互范围不以抽样谎称全域证明，求值有界。
- AC-03：输入类型、范围、单位、来源和依赖完整；stdin真实进程和旧协议兼容；分析/行动/context同源且不可越权。
- AC-04：现有Java真实操作录入范围、分析、取消、故障恢复及迟到回执处置，无helper替代窗口。
- AC-05：最小补证任务具体且有正反证据/来源/日期/适用条件，导入不自证，版本/撤回/过期只让依赖失效；原家庭缺件诚实保留。
- AC-06：显式保存/新进程恢复/当前时点重算，缓存结论和恶意授权不复活；取消/写入失败保全原文件/状态。
- AC-07：决定说明本人预览并选择新路径导出；与当前结构一致、来源可核、范围/未知/授权边界齐全；不外发。
- AC-08：16链≥14且12核心全过、至少8原生窗口链；B0/B1/主改变分开，同输入对照成立，独立留出不混分母。
- AC-09：完整机器计划退出码符合预期；保护件/HEAD/索引/历史账及旧安全语义保持，所有当前变更在明确范围内。
- AC-10：当前包活动/外部操作/纠错与物料版本可追溯，报告/摘要/原件/CURRENT一致，旧缺口不补造，无越权副作用。

## Allowed scope

精确路径由VERIFY_SCOPE.py的PRODUCT冻结，人工说明不能扩展它：

可改已有 shopping_decision/{chat_bridge,decision_worksheet,cost_scenario,decision_actions,context_builder,action_ranking,cognition_comparison,confirmed_comparison,claim_gate,evidence_snapshot,model_adapter,evidence_comparison}.py；可新增decision_uncertainty.py、decision_note.py两个薄模块。model_adapter仅为保持原边界，不新增真实调用或工具执行。

可改desktop/{ShoppingDecisionDesktop,DesktopBridgeClient,DecisionWorksheetRegression,DecisionWorksheetSwingRegression}.java；可新增DecisionEvidenceRegression.java、DecisionEvidenceSwingRegression.java。旧ChatBridge/ChatSwing/ChatNativeAudit回归只读，不改意图。

可改 tests/{test_cost_scenario_binding,test_printer_decision_journey,test_session_decision_contract,test_action_ranking,test_decision_worksheet,test_worksheet_bridge,test_worksheet_persistence,test_worksheet_evidence,test_worksheet_journeys,test_history_audit_version_transition}.py；新增test_decision_uncertainty.py、test_decisive_evidence_actions.py、test_uncertainty_bridge.py、test_uncertainty_persistence.py、test_decision_note.py。不得删除安全断言、以SKIP代运行或改冻结验收器。

可最小维护knowledge/printer_cognition_comparison_v1.json且有实际核源；scripts/audit_model_history_readonly.py仅按前述精确版本兼容更新。可改CURRENT.md、README.md启动说明、本包REPORT/COMPARISON/USAGE及evidence/executor。Evaluator写本包REVIEW/evidence/evaluator。必要的本地合成保存写临时目录或被忽略private；不读取真实私人数据。

## Exclusions and forbidden side effects

本包合同/计划/判据/所有VERIFY脚本/preparation/BASELINE/r42冻结地图原件及旧合同/基线/失败账/原件只读。当前项目地图由Evaluator更新，执行者不改。

模型API/CLI/平台业务API、账号自动化/持久化登录、设备试打、安装/付费、加购/填单/订单/支付/退款、外发消息/上传/发布、跨仓执行、第二真实品类、新应用、Git提交/推送/索引/历史改写均不授权。公开研究只限匿名人工可读来源；未知动态价格不得合成为实时权威价。不复制限制名单源码/数据。

## Validation plan

精确argv、cwd、预期退出码和Evaluator命令见VALIDATION_PLAN.yaml：承接反例、新分析黑盒、五组专项、旧业务探针/12案、全量、历史审计、Java原生、范围和完整交付。准备阶段真实缺失/失败是EXPECTED_FAILURES，不是已实现证明。

## Authorization

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_existing_local_model_cli: false
authorization_platform_business_api: false
authorization_public_research: true

本机合成实现/验证、现有环境窗口、本人显式选择的新本地文件和有界公开资料读取可连续执行。不存在每阶段再批准的要求；范围变更才返回Evaluator。

## Stop conditions

预算180有效小时或6轮集中纠错到即交；达到充分证据提前交。连续两轮在“下一步对准关键变量/证明范围/真实窗口链”无净进展，停止扩张交断点，不新开包重置。

8小时仍无法维护费粗链，优先缩实现；72小时仍只能代码参数/helper注入，停止装饰；136小时仍只能抽样冒充全范围，降级incomplete并记录未达目标。硬条件越过、事实自证、交易授权复活立即停扩张并在范围内修复，无法修则功能默认安全关闭并判不通过。

外部额度或同定位失败上限到只停外部支线；不得等家人、账号、设备或调用模型才能交离线主线。发现需要范围外文件/新依赖/许可证不明/新授权时，保留已有成果，交Evaluator具体边界，不能自行扩大。

## Amendments

None。旧包R4两文件的继承由旧包REVIEW/SCOPE_DISPOSITION记录；本合同不追改旧冻结门禁。
