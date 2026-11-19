# 最小证据先走完整流程｜连续长执行包

Task ID: PRINTER-MIN-E2E-20261117
Task name: 用少量已有真实资料把打印机研究流程完整走一遍
Task kind: capability_experiment
Contract revision: r1-minimum-end-to-end / 2026-11-17
Contract state: CONTRACT_FROZEN
Baseline HEAD: ce34764ab7d803b06abbdbcea0afe32048096c0a
Branch: main
Risk: L1

用户本轮明确要求：条件不足时按最小条件向后推进，用一个长的连续包先走完整流程，避免某一点细节反复将任务拆回准备。本合同按该指令冻结；旧B01草案及r3成果保留，不再先等新材料。

## 一句话目标与完成标准

**同一份河南家庭代理需求，带一小包已经允许研究的旧真实摘要，从需求整理、证据处理、正常程序比较、用户可读结果，一直走到反馈处理、小样本复核和集中交付。** 证据少就给有限判断，反馈没有就处理缺失，价格没有就不确认购买；流程继续。

必须实际交出：正常程序的输入输出、亲戚能看懂的比较、六个环节的真实记录、首轮完整运行、同资料前后观察、真正暴露的断点及集中验收。只有文档/新字段/“请继续找资料”不算走通。

流程通过与事实充分、用户受益分别裁定。允许“研究流程走通，真实购买/用户效果仍未知”；不允许把缺失写成已有、凭空选冠军或降低来源/交易边界。

## 战略依据

Project map: docs/PROJECT_BOTTLENECK_MAP.md
Map revision: r30
Active bottleneck: B01
Hypothesis: H-B01-MIN-FLOW-01
Measurement status: measured
Metric baseline: r3已验同旧事实的条件化分支，L3 6/6、原全量443项通过；新增外部事实0，真人反馈未取得，当前B01草案仍因材料未到停在前置。新鲜正常CLI基线可运行且有r3路径，但未消费所选最小证据包产生贯通的research_case；旧能力不记为本包收益。
Estimated affected scope: 一个河南家庭代理原案、既有HL-L1238W和M232dw两研究锚点；主路径两条旧厂家事实，另有一条/零条的工程反例，不扩品类或候选。
Expected project impact: 在不补齐全部外部条件的情况下，得到首次可审的最小证据全程样本，识别实际数据接线/比较/反馈/评测断点；真实推荐效果可以仍不可判。
Rollback condition: 源日期被刷新、未选事实偷用、不同型号混证、虚构反馈/实机/现价、条件冲突仍确定推荐、任何越权操作；撤回该断言/受影响分支并保留失败，其他安全研究继续。
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE
Expected material cost: 新包规划执行最多20有效工时、独立评估最多4小时，置信度中等；首4小时必须优先尝试首轮全程并记录，后续完善/回归/集中纠错不超过总上限。替代旧未执行规划，不与旧24+6、r3的6+2或待材料包额度叠加；历史实际成本单列不清零。无新增付费或公网额度。
Bounded retry / iteration budget: 一个连续包、一次集中提交、最多2轮集中纠错；单支线最多90分钟，正常入口必要接线最多2小时后复盘缩范围；不为了局部完美耗尽全包。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 主路径使用现成2条真实旧摘要即可；单条仍能比较，零条反例也要到达明确未知的结果；不要求新来源、真人反馈、实机、有效价或3个效果题才继续。
Max total attempts: 2
Max parallelism: 1
Max attempts per unit: 2
Retryable failure families: 合同内本地接线、渲染、来源映射和复现问题；无账号/无许可/无设备/无新事实直接降级对应项，不重试外部入口
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/evidence/iterations.json
Expected value of another round if successful: 根据本轮实际走过的断点选择下一投入；若只是格式更完整、资料和判断均无实质变化，记未见可测改善，不再靠加字段续包。

**唯一主要改变：让选定的最小真实证据包贯通正常研究入口与全程交付。** 需求、来源处理、比较、结果、反馈处理、复核是同一个改变的验证链，不同时换模型、建新商品库、做新GUI或扩大品类。

## 立即可用的最小输入

- 原案：预算1000元、月0—50页、黑白/彩印可外包、河南使用、接受首次设置、微信硬性程度未知。来自既有负责人代理报告，不能改成亲戚本人答复。微信未知保留分支，不重复问已答地区/首次设置，也不把等待回答当开工条件。
- evidence_packs.json：已经评估者定稿的有限归因摘要。主包setup_two含R7的Brother初次连接/联机设置与R10的HP系列无线后扫码绑定，共2条事实；setup_one只含Brother一条；setup_empty不含事实。获取日期仍2026-11-15，本轮仅本地打包，不算新外部事实。
- R7/R10已用于旧r3限定研究。此包不扩大其用途，不复制新整页/业务响应；主包只证明首次设置说明，价格、后续复用、长期可靠性均未知。
- cases.json绑定正常输入和所选包。任务准备基线、参考、检查器、冻结SHA均已在本机落实，执行者不等评估者再造工具。
- 原r3输入、实现、报告和L2/L3不清理/覆盖。既有大量脏工作树保留，仅本包允许路径可变。

## 最小条件与降级办法

| 缺什么 | 当前仍可做什么 | 具体结论的限制 |
|---|---|---|
| 只有1—2条已有资料，没有新资料 | 用明确来源进入比较、写支持/反证/未知，继续走后半程 | 不报新增取证成功，不推断资料没有写的能力 |
| 某型号一条事实都没有 | 仍列为待核、写清本次缺哪条依据，输出可读研究结果 | 不判不支持/合格，也不从未选资料偷补 |
| 微信是否必须没回答 | 保留两种条件说明其影响，继续其他有据研究 | 不默认硬要求/软偏好，不代本人作答 |
| 海纳用途不明 | 跳过海纳数据，继续已允许的厂家最小包 | 海纳导入/接入成功不宣称 |
| 当前价/所售配置缺 | 完成型号研究及购前待核项 | 不说符合1000元现价，不批准购买 |
| 真人/设备没有 | 准备最多三句反馈问题，记录未取得并继续复核 | 不伪造回答，不把代理/模拟称体验或实机结果 |
| 可判效果题仅0—1题、两组难公平生成 | 核能判的一题；不能判则保留实际诊断和未知，继续交付 | 不造三题、不报总体准确率，不把工程负向凑效果题 |
| 样式、措辞或非关键兼容问题 | 记待办，沿现有文本入口继续，集中最后处理 | 不因美化退回前置，不重建界面 |

不可降级的边界：真实/合成分开、来源可核、反证/日期/有效范围保留、不能捏造动态事实或用户反馈、所有交易与账号边界仍关闭。某条断言无法安全成立时去掉该断言，而不是擅自放宽事实门槛。

## 连续执行里程碑：不逐步重新派包

### M1 首4有效小时：先留第一轮完整但粗的研究

复用既有原案与2条已给事实；把证据包接到正常CLI，产生两款有限比较与可读文字；反馈缺席分支照实处理；按至少一条已冻结参考核对或记录不可判；留first_walkthrough.json及实际输入输出。不要先补外部数据、扩规则或打磨界面。

4小时是强制检查是否陷入细节的节点：尚未全程时冻结美化/旁支，把剩余工作缩到能完成首轮的必要接线；写真实断点与投入，不虚报已走通或停在等资料。首轮原件不被后续“更好版本”覆盖。

### M2 第4—10小时：同源接线和可读交付

把同一结果进入正常CLI与聊天可见result_text、完整审计；selected pack改变时结果/来源同步。用单条/零条反例检查缺证据仍能到结果；不能偷偷回退到旧静态完整事实补齐选定包。r3无context旧路径保留，带context路径的主要可见结论只来自本次选定包。

输出RESEARCH_DELIVERY.md：原条件、两款各自支持/反证/未知、来源/日期/适用范围、有限取舍与下一步、未取得反馈的状态和最多3句反馈问题。允许两款均暂缓最终选择，但要说明原因及哪项事实会改变结论。

### M3 第10—16小时：实际复核、同资料比较和负向

按EVALUATION_RULES.md核最小可判问题，不设至少3题；能公平生成两组就分别保留同输入/同资料输出，否则记录真实不可比较原因。评测环节必须处理，不能跳过或为凑实验重建框架。

五类负向：缺证据/撤销、恶意评测或推广指令、过期价、明确条件冲突、诱导下单；另测所选包替换、单条/零条、来源串型号、输入改答。只跑受影响专项与一次必要全量，除非新变更/失败，不反复已过检查。

### M4 第16—20小时：集中修必要缺陷、一次交付

优先修会改变事实、候选状态、可见结果或安全边界的问题；样式和不影响主流程的小问题登记而不扩大。交完整六环节flow_trace、断点列表、对照/反馈状态、实际工时/失败/限制、L2和REPORT。整包最多两轮集中纠错，不按每个小点拆新包。

## 普通入口与最小输出约定

正常JSONL输入保留text/answers，额外research_context仅含case_id、input_basis=project_owner_proxy、evidence_pack_id。无context走旧r3兼容；有context选用固定准入registry的指定包，不接受输入自填approved或任意URL/文件/业务响应作为新事实。

运行时registry为knowledge/printer_minimal_evidence_packs.json，内容须与本任务evidence_packs.json逐字一致；最多新增一个小的minimal_research模块做明确解析/比较/结果，不能建通用证据平台。可用现有字段映射和生成器，避免双套计算。

CLI最后事件的research_case及聊天report_json.research_result.research_case必须同源：
- schema_version=1，case_id=PRINTER-HENAN-FAMILY-20261116，input_basis=project_owner_proxy；flow_status=research_delivered_with_limits。
- evidence_pack_id、used_facts（逐条原样保留选包内事实记录）、source_registry与选包匹配；新外部事实计数0。
- candidate_assessments逐两锚点包含model_id、supported_claim_ids、research_status=keep_for_research或pending_evidence、reason、unknown_fields至少wechat_reuse/live_price/long_term_reliability。无事实不能淘汰、选冠军或偷用其他来源。
- processed_stages含requirements/evidence/comparison/explanation；report_text为完整白话比较，直接出现在聊天result_text，不能只藏审计字段。旧兼容字段若与当前研究指令不同，只留审计，不并排显示冲突指令。
- feedback.status=not_collected、actual_response_count=0；next_actions逐条写action/owner_role/exact_item，不把技术未知问成用户专业知识考题。
- purchase_recommendation_approved、transactions_enabled、wechat_reuse_verified、live_price_verified、long_term_reliability_verified、real_user_effect_verified均false。结构化未知不等于功能不支持。

evidence/flow_trace.json负责完整六环节requirements/evidence/comparison/explanation/feedback/evaluation，逐步status/observation及实际文件SHA绑定。反馈缺失/效果不可判也须有诚实处理记录；不得将“进入缺失处理”说成“已取得真人反馈”。

## 原子验收条件

### AC-01 最小证据真正进入正常研究

Given 已有2条/1条/0条固定包；When 通过正常CLI/聊天输入；Must observe 所选资料而非写死旧完整资料参与判断，来源/日期/型号/范围可回查，主路径至少使用已给2条，不要求新增外部材料；Must not observe 执行者只写人工表格、复制静态r3条件文字、刷新旧日期、未经许可的海纳数据或新事实。Evidence required 普通原件、来源映射、包切换反例。Mandatory: yes

### AC-02 少量或缺证据仍交有限比较

Given 原案未答微信硬性程度、缺价/长期/某型号依据；When 一步步处理；Must observe 每款有支持/反证/未知与具体理由，当前能做的研究继续，单条与零条反例也到达明确受限结果；Must not observe 因缺一个外部条件全包停、未知当失败/合格、强制排名、建议价当现价。Evidence required 三个普通入口结果及人工事实判读。Mandatory: yes

### AC-03 首轮全程、用户可见与后半程处理

Given 有限资料和真人缺席；When 正常程序交付；Must observe 首轮粗完整记录、CLI/聊天同源可见比较、六环节处理记录、反馈缺失真实标记及实际复核；Must not observe 只多一个审计字段、每步重新派包、在反馈缺席处中断全包、代填真人答复。Evidence required first_walkthrough、flow_trace、聊天原件、RESEARCH_DELIVERY及反馈问题。Mandatory: yes

### AC-04 最小评测与项目结论诚实

Given 同一原案与旧资料；When 看前后输出并尝试公平同资料两组；Must observe 核至少可判参考或准确记录0可判原因，对照可行则各自真实生成，不可行则实际诊断；流程结论、事实充分性、用户效果分开。Must not observe 最低3题挡流程、工程题冒充效果、弱化基线、复制同一输出换标签、流程通过就称真实推荐提升。Evidence required assessment.json、原始输出/尝试、EVALUATION_RULES逐题理由。Mandatory: yes

### AC-05 五类负向和已验能力不退化

Given 缺证据/来源变化、恶意指令、过期价、冲突、诱导交易以及原r3入口；When 经过受影响实际逻辑；Must observe 拒绝越权，受影响断言失效/未知，明确冲突优先，原无context模式仍可用；Must not observe 串型号、对抗内容控行动、擅自确认用户、自动登录/加购/下单。Evidence required 新专项至少8个有意义例子、一次必要全量与独立反例。Mandatory: yes

### AC-06 范围、时间、迭代与集中交接

Given 当前脏工作树、固定材料与执行边界；When 连续实施与集中验收；Must observe 首轮/支线/集中纠错投入据实记录，真实断点清楚，旧交付/冻结输入保留，正式L2后独立L3；Must not observe 重置公网预算、主线不断拆回准备、为过关改验收器、隐去失败或用新框架替代业务。Evidence required 冻结核对、迭代账、diff/SHA、L2、REPORT与断点记录。Mandatory: yes

## 允许改动范围

- 产品接点：shopping_decision/dialogue_flow.py、chat_bridge.py、web.py、real_printer_case.py、research_snapshot.py、printer_decision_plan.py、selection_criteria.py、contracts.py；仅为本包最小资料贯通、同源可见和改答/来源失效必要逻辑。
- 可新增一个shopping_decision/minimal_research.py、固定内容的knowledge/printer_minimal_evidence_packs.json，必要时一个scripts/run_minimal_research_flow.py只编排普通入口/记录，不能在旁路重算判断冒充主程序。
- 测试：新增tests/test_minimal_research_flow.py；可改上述接点对应既有tests/test_dialogue_flow.py、test_chat_bridge.py、test_research_snapshot.py、test_selection_criteria.py、test_real_printer_case_research.py、test_real_printer_case_t1.py、test_printer_decision_plan.py。不得删除旧回归来过关。
- Java只允许desktop/ShoppingDecisionDesktop.java的必要文本展示；不改则不重跑GUI。若真改Java才编译/核现有桥接显示，不把程序化验证说成人试用。
- 本任务REPORT.md、RESEARCH_DELIVERY.md和evidence/可写；CONTRACT/材料/参考/检查器/测试器/计划/冻结清单/preparation均由评估者冻结，执行者不可改。

## 明确排除

新搜索/重复官方读取/业务或元数据API/Key/账号/付费/外发/设备代操作/交易/提交推送；海纳新数据、整页/第三方源码复制、训练/模型传输；扩品类/候选/平台、新GUI/数据库/通用规则框架、正式36题、为了美化重做已验r3。旧公开账搜索6/6、读取11/12保守保留，不自动动最多余1次。

## 验证计划与最终裁决

Validation plan file: handoffs/evaluator_executor/PRINTER-MIN-E2E-20261117/VALIDATION_PLAN.yaml

六项VP：冻结范围、检查器稀疏/安全自检、正常入口三种资料量、受影响新专项、一次必要全量、完整交付/评测记录。评估者命令对普通入口另写evaluator_flow目录，保留executor_flow和首轮原件。检查器只核可复现行为/绑定，来源含义、对照理由及实际行动收益须独立判读。

执行者用技能run_validation.py --mode executor生成L2，全部强制项通过后交REPORT；评估者同计划--mode evaluator产生L3并逐条裁决。若L2失败，仍先完成安全可做的后续环节并记录，再在合同/次数内集中修复；不得自签PASS，也不自动扩范围。

任务通过可以只是“最小真实资料的研究流程确实走通”；真实选购/用户效果仍可INCONCLUSIVE（尚无法判断）。若没有行动判断改善，记录NO_MEASURABLE_GAIN（未见可测改善），下一步根据实际断点选，不以同向加字段续包。

## 授权与真正停止条件

commit: false；push: false；history_rewrite: false；api_call: false。新外部调用/账号/付费/外发/交易0；本轮制定不执行产品改造，冻结后下一责任执行者。

只有以下情形中止全包并交已有结果：达到本包20有效工时或两轮集中纠错上限；安全/证据真实性无法守住且无法去掉该断言继续；正常入口仍完全不可用；必须越过明确授权边界。无真人、无设备、无有效价、无海纳许可、资料少、对照不可判、非关键样式问题均不构成全包停点。

首轮记录、失败和真实断点不覆盖。所有可安全完成的后续步骤先做完，最后一次集中交付；没有授权不擅自扩大任务，已有授权不重复请用户确认。
