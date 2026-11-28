# 冻结执行包：先让小白理解怎么选，再形成可核的打印机决定

Task ID: PRINTER-COGNITION-FIRST-20261126
Task name: 有来源的品类认知、参数参考、用户确认与条件化比较贯通现有入口
Task kind: capability_experiment
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f
Pre-existing changes: 接收本包BASELINE记录的全部未提交实现和历史证据，不回滚、不清理、不改索引。
Validation plan file: handoffs/evaluator_executor/PRINTER-COGNITION-FIRST-20261126/VALIDATION_PLAN.yaml
制定日期：2026-11-26；角色Evaluator；唯一下一责任Executor。

## Strategic basis

Project map: docs/PROJECT_BOTTLENECK_MAP_CURRENT.md
Map revision: r43
Active bottleneck: B05
Hypothesis: H-B05-COGNITION-FIRST-01
Measurement status: measured
Metric baseline: 现有会话/两型号认知事实/工作单可运行；原生窗口6链有历史独立证据。但前包从已知维度/既定候选起步，未将资料→小白指南/参数参考→本人确认→路线→型号比较列为验收；新guide协议、认知引用绑定及其模型上下文尚待本包实际前测。
Estimated affected scope: 本地打印机研究用户、原河南家庭代理需求及20条离线任务链；不能外推真人学习效果或第二真实品类。
Expected project impact: 用户不用先懂专业参数或自填维护费，能先看懂有条件的选购依据、确认自己的要求，再得到可追溯的路线/候选取舍和补证；20链至少18完成、14核心全过、8原生窗口，安全错误0。
Rollback condition: 认知材料擅改需求/硬门槛、无来源参数参考冒充专业结论、型号事实被一般帖子替代、旧认知/授权复活时停扩张；安全降为具体待核并保留已有用户答案。
Dispatch mode: SINGLE
Expected material cost: 最多180有效小时、6轮集中纠错，独立建议16小时；替代原180小时包，不与其相加。模型/业务API0；公开查询≤12，读取执行32/独立12；不安装新依赖。维护复杂度估计中高，置信度中等，不编造ROI。
Bounded retry / iteration budget: 8小时首个认知粗结果；累计16/40/64/88/108/132/152/172/180小时检查点；目标达到提前交，各阶段连续推进。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 最小真实认知集至少3条可复核主张、2个独立来源组，包含技术/官方原始资料及至少一份专业比较方法或独立测试来源；来源不足可以交工程，但该业务来源项不能签PASS。
Max total attempts: 公开读取44（执行32、独立12）；查询另限12。
Max parallelism: 1
Max attempts per unit: 同URL同定位失败最多2次；失败消耗额度，授权/许可/用途不符不换账号绕行。
Retryable failure families: 暂时公开传输超时、缓存故障；付费墙/登录/用途未获许可停止该来源分支。
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/PRINTER-COGNITION-FIRST-20261126/evidence/executor/operations.jsonl
Expected value of another round if successful: 再由Evaluator决定是否值得真人理解/实际模型效用实验；不以本包离线成功自动批准模型、设备、平台或扩品类。

## Single objective

让只会说“家里想买打印机”的用户，在现有聊天与Java窗口完成：

**初步用途→复用/补查适用来源→理解技术路线、选购因素与常见误区→看到有依据的参数参考→本人确认硬要求/偏好/未知→先判路线再比较已有候选→查决定性缺件→改答/撤回/恢复后重算→得到有来源和日期的决定说明。**

单一主改变是“有来源的品类认知在需求形成与比较链中实际生效”。沿用现有需求状态、research_router、认知/选择依据、claim_gate、候选比较、工作单和上下文；不新建第二推荐引擎、会话系统、知识平台或应用。补一篇静态百科、把专业参数表挪到窗口、或只在结果末尾加来源列表，均不算贯通。

## Supersession and scope reconciliation

用户已明确要求重排。旧PRINTER-DECISIVE-EVIDENCE-20261126合同/基线/准备失败全部保留，正式执行路由由本包替代；它不是被测产品失败，不追认完成。开包前该包3588保护件、产品、HEAD/索引均匹配，未见executor目录；若发现另有实际投入，先如实扣除，不能重置180小时/6轮。

保留：维护/主机价/随箱量行动修复；来源状态/依赖失效；既有工作单/恢复；当前Java精确版本审计兼容；本地决定说明。调整：这些是认知主线的下游支撑，不再先做它们。暂缓：独立analyze_uncertainty协议、最多4变量通用范围引擎、4096求值器及整套robust区间界面，不是本包强制交付；不为兼容旧计划把这些继续塞回来。单变量真实干预和明确假设仍须支持，不声称全范围稳定。

来源研究从“只查型号微信/耗材缺件”前移到“为何选择这些路线与维度、适用条件和例外”；型号/动态价格保持独立核验。详细保留/调整/暂缓见SCOPE_CROSSWALK.md。

## Carried review corrections

| 来源/失败 | 有限修复与范围 | 聚焦回归 | 预算 |
|---|---|---|---|
| WORKSHEET AC-04/07：HP维护0→100使700/650→700/750，下一步却问Brother随箱量 | 同一成本/行动结构保留真实决定性对象/字段，来源于当前显式假设及编辑；不只改文案 | 正常stdin维护/主机价/随箱量三个干预；硬缺证先核资格 | 阶段F内≤8小时，不抢认知前置 |
| WORKSHEET AC-08：历史manifest与当前Java升级冲突 | 接收旧Evaluator已审R4精确差异；允许本包最小更新当前Java最终精确SHA/测试，旧历史锚点、账本、失败结论不动 | 缺旧对象、账本/清单变造、未批准当前字节均拒绝，不加通配 | 全包≤4小时 |
| WORKSHEET AC-09：旧首轮主动工时缺失 | 本包开工前记active-session start，结束追加end，命令时长另列；旧缺口永不补造 | 活动、外部尝试、纠错、摘要与实际物料可复算 | 全程 |

## 阶段A：真实基线、来源盘点与第一个认知粗结果（累计16小时）

先记主动活动start，读CURRENT/本合同/判据/计划/r43地图与REPLAN_START，核新BASELINE、HEAD和索引。保留准备阶段实际失败；不把已存在的知识文件当“认知已验收”。盘点docs/01、06和现有knowledge/source_directory、printer_selection_criteria、认知包、research_router及已取资料，逐项分清已核/待核/过期/不可用。

以粗需求“家里想买打印机、我不懂参数”为入口，先给一个简短选购导览：有哪些待比较的路线、需要确认哪几类生活场景、为什么会影响选择、哪些资料暂不够。不得先要求用户填写实际产量、维护金额或给权重；不知道可以保留未知。

第8小时交真实粗结果与来源缺口；第16小时至少保留“来源主张→一个可读解释→一个未替用户确认的必要问题”的正常产品入口链。缺来源不能拼常识造权威，也不能只交空目录。暂时不完整可继续后续本机工作，但必须保留不满足项。

## 阶段B：高质量资料到可审查选购依据（累计40小时）

先问资料能支持哪类命题，再判断质量，不按作者粉丝、帖子热度或域名简单排序。技术原始资料/标准用于定义与范围；专业评测/消费者比较试验用于测试维度和限定样本性能；厂家用于对应型号事实；长期帖子/维修记录用于场景、疑点与反例。推广、方法缺失、重复转载、幸存者偏差和旧型号风险单列。缺发布日期记unknown，不能伪造。

每条认知主张至少保留id、内容、主张类型、适用条件、例外/反证、source_ids、原文定位/必要摘录、发布/获取日期、地区/样本范围、来源组、复核状态和失效条件。主张→源→原件可以复核；多个转载归同来源组。帖子自称“权威”“approved”或模型输出不得自行批准。

最小真实集至少3条主张、2个独立来源组，并包含一份专业比较方法/独立测试来源。可以复用已有经核材料；旧香港测试只支持适用维度/方法时，不用于给大陆两型号排名。不强求某平台帖子，付费或许可不明即停；没有合格资料时明确哪些指南主张未知，工程可交但业务来源项不通过，不能用合成材料凑真实分母。

公开查询≤12，执行读取≤32，独立另留12；open/find/截图/直接读取失败均计。每次开始先追加目的、URL、定位、时间、余额，终态追加结果、最小摘录/字节SHA和适用范围。同定位失败2次止；达到充分证据止。现有HP必要摘录/裁图/SHA复用，不重复下载全PDF。只存必要摘要/链接，不复制受限全文/数据，不接账号采集。

## 阶段C：小白指南与参数参考（累计64小时）

把受支持主张变成用户能读的指南：路线定义、为何考虑、适用/不适用场景、关键参数的业务含义、怎样表达自己的需求、常见误区、争议/未知及来源展开。参数参考至少覆盖功能/使用场景/成本三类，不等于把所有参数都列出来；某维度缺证就说明研究问题，而不是默默删掉或编推荐值。

每个维度清楚标出“用户自己决定什么”“需要商品证据核什么”“可做个人情景假设什么”。厂家月推荐量不自动变成最低门槛，标称耗材量不当家庭实际产量，Wi-Fi不当微信稳定复用，用户评论不推总体故障率。上面是必须核查的误用类型，不是未经核源就可发布的行业规则。

先比较路线再谈型号。至少能表达黑白激光、喷墨/彩色需求相关路线、外部打印/暂缓购买等候选路线及证据不足状态；只有资料支持才给倾向，不能预先宣布一种路线最好。已有Brother/HP是下游研究样本，不是每个新手任务的必然候选。若用户必须在家彩印而两者不覆盖，应说明当前候选集合不适用并回到路线/发现计划；不新增真实型号来伪造覆盖。

指南不强制阅读考试。用户已有清楚要求可跳过/查看来源，既有明确需求保留；小白可逐项理解后选择、拒绝或暂缓。字数/知识卡数不是验收，首屏应能找到“我该先想清楚什么”。

## 阶段D：认知引导后的本人确认与现有窗口（累计88小时）

在现有聊天/Java增加“选购前先看”的薄视图，复用现有编辑、参考答案草稿、发送确认与版本机制。粗用途后可以先看导览，再展开技术/参数/来源；不用跳到第二应用。点参考只是草稿，发送/明确提交才改变需求。指南、模型或外来帖子不能替用户把偏好改成硬要求，不能重问已经确认的同一条件。

认知维度与现有需求槽位建立可追溯映射：知道某个问题来自哪条依据，答案如何进入路线/商品条件，哪一环仍缺证。至少验证一个原先未被充分表达的使用因素（例如连续闲置情景，具体字段由执行者在USAGE冻结）能有类型地保持已确认/暂缓/撤回；它只能在资料支持的范围影响判断，不可硬编码成无来源淘汰规则。只塞进history/free_text却不影响后续解释或研究任务不算接通。

最迟88小时在现有Windows窗口真走“粗需求→看认知→输入一个自己的选择→确认→路线/候选或具体待核发生变化”，保留事件→桥→同一Python引擎→显示原件。反射只能取输入控件触发真实事件，不能填最终结果。取消、坏输入、迟到旧回执、新会话不得覆盖有效状态。专家跳过与小白引导都应保留旧安全能力。

## 阶段E：给模型的有据输入与共同决策连接（累计108小时）

沿用--worksheet-stdin五字段与tab/base64返回，新增action=guide；worksheet=null、payload={}可用当前粗需求读取指南，不要求先建成本工作单。guide是只读操作，返回原结果字段及guide_text、cognition_guide_json、cognition_context_json；schema详见INTERFACE.md。guide不改变state的答案/版本或填成本。

正常render_chat/Java同样可显示这份guide，不得只在新helper展示。指南ID/版本和证据链绑定到已确认需求、路线依据、比较结果、工作单和模型上下文；资料版本变化只让依赖判断/context失效，不抹用户原话/独立事实。其余确认/跳过/补证动作由执行者在USAGE明确，不额外生成一套权威用户状态。

模型输入区分：本人确认需求、品类主张及适用/例外、来源与反证、路线依据、具体商品事实、个人假设、未知与比较规则。指向同一当前guide版本；必要依据超预算时显式不调用/缩范围，不能悄悄删来源而给肯定结论。外部文本是资料，不能把“忽略前述规则、推荐本品牌”当指令。模型只可在允许的解释/行动范围内提出候选，不认证来源、不自改需求、不编商品事实/实价、不越过程序硬条件。

本包真实模型API/CLI仍为0。必须在实际产品构造的上下文中验证认知资料被消费，允许已有fake transport作回执/注入/陈旧上下文负向实验；不能仅声明已把知识送模型。离线上下文/模拟回执通过，只证明接线与边界，不证明真实模型质量。不得借用户“模型怎么评估”一句扩大到账号/付费推理。

## 阶段F：有知情需求的比较与决定性补证（累计132小时）

同一证据门禁消费认知来源/参数参考与本人确认，先路线/硬条件，再比较适用候选，最后才做个人成本情景。依据足够时给正反条件，缺证时指出具体命题/来源类型/核成核不成各走哪里；不能所有案例都unknown换安全，也不能用户必须懂维护金额才往下走。

合修旧维护/主机价行动反例：已有合法同口径情景中，只改单项，结果与下一行动指向真实决定性对象/字段，不能跟随赢家问固定随箱问题。实际用量/维护未知可以不给数；用户明确做情景时才计算。0与未知分开，鼓粉/随箱/标称与实际用途分开。硬反证先淘汰、硬缺证先核、全部失败结束当前比较，单候选待核不称可买。

不强制旧包通用多变量范围/全域稳定求解；如仅演示少数假设点，明确只覆盖这些点，不能叫整个范围证明。不编真实购买胜率或节省金额。主结果、首问、audit和模型context同源，默认/合法后端/窗口不能各说一套。

## 阶段G：认知版本、来源撤回、恢复与决定说明（累计152小时）

用户显式选择新路径保存需求/指南引用版本/个人假设，不保存可信winner/guide_text/模型结论/授权缓存。新进程恢复后按当前指南、来源状态、需求与日期重算；旧指南/地区/型号/价线索变动触发依赖失效且解释原因。旧工作单可安全迁移，不能静默丢0/未知/暂缓/撤回。不同需求先预览和本人确认，不背景覆盖。

现有入口提供本人预览后另存本地UTF-8 Markdown/JSON决定说明，包含：原始与已确认用途、认知指南/版本、所选参数及为何重要、路线去留、现有候选正反证据、来源日期/适用/例外、假设和未知、一个下一步及失效条件、购买授权false/交易关闭。文件是研究说明，不是订单/支付指令，不外发、不跨仓调用。

取消/失败不破坏当前会话或旧文件，拒绝执行URL/文件内容/恶意路径。私有资料默认不入Git；本包评测只用合成个人资料，不读取凭证/Cookie/家庭真实私人文件。

## 阶段H：公平对照、20条任务链及独立可复核测量（累计172小时）

实施前登记expectations.json与证据支持的参考判断，固定20链见EVALUATION。≥18/20且14核心全过，至少8条实际Java窗口链；G01粗需求导览、G05本人确认、G13认知源失效、G14新进程恢复必须含窗口。其余可真实stdin进程。受控材料测试、真实认知来源和真人观察分别记，不混分母。

保留B0开工前产品；承接修复完成后冻结B1共同安全基线，纠错收益单列。A为公平直接参数筛选/澄清，B为先认知→本人确认→比较；两组同初始场景、可得原始来源/商品事实、底层用户偏好、时点与资源上限。不能删弱A的硬条件/澄清或只给B新增资料；新增资料收益与组织/引导收益分别计。

离线可用冻结的合成回答脚本作为同一偏好oracle，但必须明说不是用户真的学会。测关键维度遗漏、无据规则、必要追问/路线解释/下一步是否正确、资格/来源错误、代价与退化，不用说明条数或引用数量冒充效果。至少保留一条无收益、一条退化/故障安全降级及一条有证据阳性路径；不要求B每案都赢，若无净增益如实交。独立Evaluator另选至少6复合留出，不与20混分母，参考不能由被测函数自己生成。

三项分开：认知资料/规则正确性；实际上下文接线与受控回执；真人理解/真实模型收益。前两项可在本包证明，后两种真实效果仍未证，不伪造访谈/模型输出。无需等家人/设备/账号才能交付离线链。

## 阶段I：完整收口（累计180小时）

标准runner完整L2执行本包计划，不手拼绿表。新认知探针/专项/产品链、旧业务探针/12案、全量/历史审计、当前范围、旧Java与新认知事件、交付摘要全部真实运行。最小旧测试迁移解释语义，保留所有安全断言，不删除/跳过测试刷绿。

REPORT标准格式逐AC与阶段列完成/部分/未完成、来源真实范围及证据路径；COMPARISON给20链和A/B对照、B0/B1修复分账、无收益/退化；USAGE给负责人可直接启动及普通操作说明。原件/摘要/生成器SHA和版本可复算，实时活动/外部账及纠错轮次完整；旧缺口不补造。L2未全过仍EXECUTING/Executor，提交后Evaluator独立接收和验收，执行者不签总体PASS。

## Acceptance criteria

全部强制；机器计划加EVALUATION语义复核共同裁定。

- AC-01：真实认知依据最小集可复核，来源职责/独立性/条件/反证/日期明确；广告和帖子不自证，不把受控材料充真实来源。
- AC-02：粗需求可得到小白可读的路线/参数参考，知道为什么重要、自己决定什么、哪些未知；不强迫先懂参数/填维护金额。
- AC-03：认知引导进入本人明确确认/暂缓/撤回和路线判断，至少一个新增使用因素有类型映射与后续影响；指南不代用户确认。
- AC-04：真实guide协议及正常聊天/Java同源，旧桥兼容；输入和外来资料安全，不能仅helper显示。
- AC-05：真实产品上下文包含当前认知依据/来源/确认/商品事实/未知，支持受控提案和注入/陈旧回执回退，真实模型调用0且不宣称效果。
- AC-06：先路线/硬条件后适用候选与成本，维护/主机价/随箱干预的行动正确；不把一般品类主张当型号/实价事实。
- AC-07：认知版本/来源撤回/地区变化仅使依赖失效；保存/新进程恢复重算，旧结论/授权不复活。
- AC-08：现有Java实际事件完成指南、本人确认、比较/补证、取消/故障/迟到回执、恢复及说明导出；主屏可读且审计可展开。
- AC-09：20链≥18、14核心全过、8原生及6独立留出；A/B同资料公平、修复/资料/组织收益分开，离线回放不冒充理解改善。
- AC-10：完整机器计划、HEAD/索引/保护/历史和旧安全行为通过；当前Java精确兼容和允许变更可审，不改旧失败账。
- AC-11：当前活动/取证/纠错/版本完整，标准交付与CURRENT一致；本人显式本地导出，账号模型交易外发提交推送0。

## Allowed scope

精确列表冻结于VERIFY_SCOPE.py，以下业务说明不扩范围。

已有Python可改：shopping_decision/{chat_bridge,dialogue_flow,research_router,knowledge,selection_criteria,cognition_comparison,confirmed_comparison,claim_gate,evidence_comparison,decision_actions,decision_worksheet,cost_scenario,context_builder,action_ranking,model_adapter,evidence_snapshot,printer_effect_probe}.py。可新增cognition_guide.py、guide_binding.py、decision_note.py薄模块；优先复用，不必都建。不得再造第二规则/事实/状态引擎。

可维护knowledge/{printer_selection_criteria,printer_cognition_comparison_v1,source_directory}.json并有真实依据；可新增printer_cognition_guide_v1.json。data/private的本人显式合成存档/临时输出按既有忽略规则，不写真实秘密。

Java可改desktop/{ShoppingDecisionDesktop,DesktopBridgeClient,DecisionWorksheetRegression,DecisionWorksheetSwingRegression}.java；新增CognitionGuideRegression.java、CognitionGuideSwingRegression.java。旧ChatBridge/ChatSwing/ChatNativeAudit回归只读，保持原意图。scripts/audit_model_history_readonly.py仅做已声明的当前Java最终精确SHA候选版本兼容，不改旧锚点/账本。

可最小迁移tests/{test_cost_scenario_binding,test_printer_decision_journey,test_session_decision_contract,test_action_ranking,test_context_builder,test_decision_worksheet,test_worksheet_bridge,test_worksheet_persistence,test_worksheet_evidence,test_worksheet_journeys,test_history_audit_version_transition,test_dialogue_flow,test_research_router,test_selection_criteria,test_cognition_comparison}.py；新增test_cognition_guide.py、test_guided_requirements.py、test_cognition_guide_bridge.py、test_cognition_context_lineage.py、test_cognition_guide_persistence.py。不存在的列名不要求凭空建旧测试；新五组必须实际实现。

可改CURRENT.md、README.md当前启动说明、本包REPORT/COMPARISON/USAGE和evidence/executor；Evaluator写本包REVIEW/evidence/evaluator。本包合同/计划/接口/判据/准备/BASELINE/VERIFY脚本、r43地图和旧材料冻结只读。

## Exclusions and forbidden side effects

不改旧合同/基线/报告/失败账/原件，不清理未提交成果；不改其他仓，不扩真实品类/实际候选型号，不新应用，不导入重型检索/向量框架或第三方源码/数据。docs/06、07只作原设计依据，不把其历史扩品类建议当当前授权。

模型API/CLI、平台业务API、账号自动化/持久化登录、设备试打、采购/安装/付费、对外消息/上传/发布、加购/填单/订单/支付/退款、Git提交/推送/索引/历史改写全0。动态事实必须未来平台权威实时核验，不能靠指南/LLM生成。

## Validation plan

精确argv/cwd/预期退出码见VALIDATION_PLAN.yaml：新认知只读/上下文探针、新五组专项、承接行动反例、旧业务/12案、全量、历史审计、原生Java、范围和完整交付。准备阶段缺失/失败是真实待做，不是产品已验收；Frozen checker不能由执行者改。

## Authorization

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_existing_local_model_cli: false
authorization_platform_business_api: false
authorization_public_research: true

已授权范围内可连续推进，不逐阶段等批准。新型副作用、范围外资料/代码/依赖或模型权限需返回Evaluator，不自行扩大。

## Stop conditions

180有效小时/6轮到停止并交真实断点；充分即交，不凑工时。连续两轮认知→本人确认→判断变化无净进展，停止堆知识/字段，交证据由Evaluator重判。

第16小时仍只有静态文档或缺源常识，先缩到一条有据问题链；第88小时仍只能helper注入、无法窗口引导确认，停止装饰；第132小时仍只做成本算术、没有认知依据影响需求/路线，不能转成旧成本包冒充完成。

来源额度到只停该支线，缺真实资料如实未知并交业务不通过；不等账号/设备/家人、不把合成资料当真实。事实自证、擅改用户需求、硬条件绕过、旧授权复活立即停扩张修复；无法修复新功能安全关闭，不改强制判据。需要新假设/范围/权限时交Evaluator，不能新开包重置预算。

## Amendments

None。本包按用户明确纠偏替代旧包执行入口，历史接受/拒绝及准备失败均不改变。
