# 现有证据下把打印机判断交出来｜原长包r3执行合同

Task ID: HNA-RESEARCH-ADMISSION-20261116
Task name: 用现有事实给出条件化取舍和可执行下一步
Task kind: capability_experiment
Contract revision: r3-conditional-delivery / 2026-11-17
Contract state: CONTRACT_FROZEN
Baseline HEAD: ce34764ab7d803b06abbdbcea0afe32048096c0a
Branch: main
Risk: L1

这是同一原长包的r3有界修订；r2合同、旧准备报告、评审和全部失败原件保留。用户本轮要求“制定好新包”，本轮由评估者完成定稿及验收准备，不执行产品实现。执行者接手即可本地开工，无须等新资料、旧访问日志、设备、账号或新授权。

## 白话目标与这次必须交出来的东西

围绕已有河南家庭代理原案，把两款目前可研究的型号说清楚：已有依据是什么、哪些仍未知、如果微信是必须条件该做什么、如果只是偏好又可以继续做什么。它必须由正常程序输出，聊天结果里直接可见，不能只写一份人工报告或给审计JSON加字段。

交付：一个真实代理原案重跑、两个明确标为假设的分支重跑；一份给亲戚看的比较；同输入/同旧事实的前后对照；负向检查及一份集中报告。每条判断带适用条件、正反依据、出处、获取日期与有效范围。允许保留未知、两款并列和暂缓购买，不能为显示进展强行选冠军。

## 战略依据

Project map: docs/PROJECT_BOTTLENECK_MAP.md
Map revision: r27
Active bottleneck: B05
Hypothesis: H-RESEARCH-02
Measurement status: measured
Metric baseline: 本轮新鲜正常CLI重跑退出0；共享结果next_action=clarify_user_conditions，必要问题只有budget_scope，没有decision_plan；现有聊天已会追问wechat_required，但可见结果仍无两条有据条件分支。新相关材料0、海纳用途未知、目标身份0/2、有效地区价0。
Estimated affected scope: 仅已有河南代理原案、Brother HL-L1238W与HP M232dw，以及两个明确合成的微信条件分支；不扩品类、候选或来源。
Expected project impact: 不增加事实也能把未知变成有条件、有责任方的下一步；观察至少一个原案行动判断是否比旧输出具体且正确。B01外部事实缺口不因此消失。
Rollback condition: 把未知变成否定/成功、把假设变本人确认、首绑推复用、建议价当现价、无据淘汰/排名、跨来源许可、任何交易权限变化；保留失败并撤回相应确定结论。
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE
Expected material cost: 执行预计4—6有效工时、独立评估最多2小时，置信度中等；本包硬上限6+2，从原长包可核剩余额度内切出并取较小者，不叠加为新24+6。公网/搜索/业务调用预算均0，无新付费。
Bounded retry / iteration budget: 一次连续交付，合同内最多2轮集中修正；同一原因两轮不进展或工时上限先到即停，不通过改参考/改验收器凑收益。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 普通CLI与聊天可见输出均完成一个原案及两个假设的有据行动路径；新外部材料不作为本包必需输入；判例不足以支持真实用户效果时明确未知。
Max total attempts: 2
Max parallelism: 1
Max attempts per unit: 2
Retryable failure families: 本地同源输出、判断、格式和既有桥接缺陷；不重试外部入口或缺许可
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/HNA-RESEARCH-ADMISSION-20261116/r3/evidence/iterations.json
Expected value of another round if successful: 先交可用条件化研究，再由真正有行动价值的新事实推动后续原长包；输出加长或字段增多不自动值得下一轮。

**唯一主要改变：把现有证据和未答目标组织成来源绑定的条件分支与下一行动。** 不同时换模型、加检索、引入新数据、重建规则框架或界面。原B01事实与用途仍受限；因公开路线信息增量0且无可用新入口，本轮改投可本地验证的B05判断交付，不宣称B01已突破。

## 冻结输入与行为参考

- preparation/baseline.*、preparation/baseline_cases/：本轮真实运行原件；代理输入不是本人新确认。
- cases.json：原案保持预算1000、月0—50页、河南使用、首次设置可接受、希望后续微信；微信硬性程度保留未知。两个true/false分支均标假设。
- task_register.json：评估者已定稿的三个行动参考；不是新增专业测试/实机事实或正式未见评测。
- knowledge/printer_selection_criteria.json、knowledge/real_printer_case_comparison_20261115.json及既有M01材料判读：只沿已有少量归因研究范围，不批准海纳或新业务响应。旧来源日期/局限必须保留。
- FROZEN_INPUTS.json：绑定本合同、参考、输入、验收代码、基线及范围外产品文件；manifest SHA写入冻结验证命令。计划及manifest再绑定于preparation/READY.json。

不拿新“材料必须先到”作为开工条件。若后来有人自愿给新材料，先单列待核；本包默认不改变事实集、不因此扩大范围或重做对照。

## 执行顺序

1. 核冻结输入、保留既有未提交工作树，读取本轮基线和参考，不重复全库盘点或原网络。基线里已有事实处理、聊天追问和安全能力照实保留。
2. 在现有共享研究结果添加下述decision_plan。原案先保留微信硬性程度未知，以两条假设说明不同答案会怎样改变下一动作。显式已答true/false时切换当前路径且不重问；既有明确冲突仍优先处理。
3. 两款均保留研究状态；微信必须时要求准确型号后续使用条件/自愿二次输出的最小记录，并说明由谁提供。微信可选时允许继续按已有事实研究，不能宣称其他App已实测成功。预算口径、收货地、销售身份、实时价仍保留为购买阶段待核项。
4. 同一份判断进入CLI、聊天result_text和完整审计；沿用现有Java文本展示。结果改变/用户改答时更新，不新建页面或流程；只有实际必要的显示改动才触碰Java。
5. 跑三个冻结输入、五类必需负向及受影响回归，实际写CASE_COMPARISON.md、来源映射、影响对照和REPORT.md，一次交评估者。

## 最小输出接口

位置：real_printer_case_research.shared_research_snapshot.decision_plan；聊天审计相同位置。保留旧字段与旧安全门禁，不以新结构改签旧结论。

- schema_version=1；scope=conditional_model_research；reuse_verified=false；购买/交易标志false。
- current_path：原案clarify_wechat_requirement；明确必须微信verify_wechat_reuse；明确可选continue_model_research。冲突情形先阻断冲突，不套常规路径。
- primary_question：原案field=wechat_required/status=unconfirmed及白话原因；明确已答后为null。
- branches：恰好两条，when.wechat_required=true/false，basis=hypothetical_not_user_confirmation，candidate_model_ids均保留两个研究锚点。每条含source_ids（旧R7/R10）、explanation、limitations及next_step(action/owner_role/exact_item/blocks)。来源经共享source_registry绑定日期、URL及局限。
- true分支state=pending_reuse_evidence、blocks=wechat_reuse_claim；false分支state=research_can_continue、blocks=specific_unverified_claim_only。禁止把缺单条证明扩大为所有研究受阻。
- purchase_checks：budget_scope/delivery_region/sale_identity/live_price，stage=purchase、verified=false；保留待核，不把它们删掉或假装已验。
- text：一段足以读懂条件分支、型号依据与下一步的中文，直接进入聊天result_text。机器字段通过不代替独立事实与可读性裁定。

## 验收条件

### AC-01 现有依据与原案边界正确

Given 原代理输入、旧厂家材料；When 产生三个输出及来源映射；Must observe 代理/假设/本人确认分开，原案微信未知不硬化，两款资料仅限定研究，首绑与后续复用分开，每条有正反依据/来源/日期/有效范围；Must not observe 新资料/海纳许可/实机成功/耐用胜负或未知能力造假。Evidence required 普通输入输出、claim_source_map.json与人工逐条核源。Mandatory: yes

### AC-02 条件改变实际下一动作

Given 原案未知与显式true/false；When 正常入口逐一处理；Must observe 上述三个当前路径及两条条件分支，行动说明谁提供哪项材料以及会改变什么，不以购买阶段缺件阻断全部研究；已答不重问，明确冲突先处理。Must not observe 所有输入仍只是泛泛待核、未知等于否、假设写回本人回答或为凑差异排除型号。Evidence required 冻结三案前后输出、task_register逐题判读。Mandatory: yes

### AC-03 用户可见结果与审计一致

Given 同一代理/假设输入；When CLI和聊天桥接输出；Must observe 同一decision_plan，可见result_text含完整白话text；改答后结果/来源同步，首次设置与河南不重复问。Must not observe 新逻辑只在旁路脚本或审计JSON，用户结果不变。Evidence required check_delivery行为记录、聊天原件及改答回归。Mandatory: yes

### AC-04 五类负向与已有保护不退化

Given 缺证据/来源撤销、含推广或恶意指令的材料、过期价格、明确条件冲突、诱导加购下单；When 走受影响正常逻辑；Must observe 每类有具体反例、输出与断言，未准入内容不控制行动；过期/建议价不当预算通过，冲突优先，购买/交易false。原案不变而核价未到不得硬放行。Evidence required tests/test_printer_decision_plan.py实际运行、现有相关测试和一次必要全量；独立评估另核语义，不把这五类工程题当认知效果题。Mandatory: yes

### AC-05 前后对照诚实且交付可用

Given 同输入、同旧事实、已固定基线与参考；When 比较旧新结果并写CASE_COMPARISON.md；Must observe 分别记录已有能力、真正变化和仍然未知；至少交当前条件/两款适用与未知/最关键分支/具体下一步。即便结论未变也给理由。Must not observe 把新字段、字数、10个合成检查、两个假设当真实用户收益或正式36条成绩。Evidence required impact_comparison.json、三个前后原件、来源映射与报告。Mandatory: yes

### AC-06 范围、留证与成本受控

Given 既有脏工作树、冻结范围与预算；When 本地实施/L2提交；Must observe 仅允许产品接点变化、冻结材料/旧交付原件不变、预算与失败据实记录；执行者不改验收器或参考，L2后独立L3。Must not observe 新联网/业务API/账号/Key/外发/付费/交易/提交推送、重发历史预算、扩候选或再拆准备包。Evidence required 冻结核对、前后diff/SHA、实际账、L2与REPORT。Mandatory: yes

## 允许改动范围

- 可改产品接点：shopping_decision/research_snapshot.py、real_printer_case.py、selection_criteria.py、dialogue_flow.py、chat_bridge.py、web.py；如确有数据传递必要，可在shopping_decision/contracts.py的现有PurchaseRequest或既有字段映射内最小补传原有目标，先记具体理由，不增新自动化或业务概念。
- 可新增：shopping_decision/printer_decision_plan.py（只有现有函数容纳不清才加单个小模块）、tests/test_printer_decision_plan.py；可改的旧测试限定test_research_snapshot.py、test_selection_criteria.py、test_chat_bridge.py、test_dialogue_flow.py、test_real_printer_case_research.py、test_real_printer_case_t1.py、test_printer_effect_development.py，不删除既有测试来通过。
- Java仅必要文本显示：desktop/ShoppingDecisionDesktop.java；无实际改动无需重跑GUI。改变可见结果时至少检查现有桥接文本输出，若修改Java则编译/既有桥接回归及实际显示留证，程序化与真人体验分开。
- 本r3目录可写REPORT.md、CASE_COMPARISON.md、evidence/；执行者不可改CONTRACT、VALIDATION_PLAN、cases、task_register、check_delivery、test_checker、FROZEN_INPUTS、preparation/或旧父包证据。超范围先说明，不自行把保护文件从快照删除。
- 产品源文件及基线范围以FROZEN_INPUTS的allowed_product_paths/protected_product_files为准，保留全部其他既有工作树差异。

## 明确排除

海纳新解析/响应、第三方账号或持久会话、搜索/网页/业务API、实时价格和销售系统、购买推荐/下单支付、日志追溯包、新GUI框架、新品类/平台、训练/模型传输、对外消息、正式36条。不能承诺任何准确型号实际微信复用或长期可靠。

## 验证计划与独立评估

Validation plan file: handoffs/evaluator_executor/HNA-RESEARCH-ADMISSION-20261116/r3/VALIDATION_PLAN.yaml

VP-01冻结范围；VP-02检查器10项合成保护；VP-03正常CLI/聊天三案与独立输出目录；VP-04新增业务负向/改答测试；VP-05一次受影响全量；VP-06提交/对照资料。所有命令已落实，不留未来不存在的验收器作为开工门槛；VP-04对应产品测试由执行者实施。

执行者用技能run_validation.py --mode executor写本r3/evidence的L2，之后交REPORT。评估者同一冻结计划用--mode evaluator写新L3；两种模式的行为原件分目录保存，不覆盖原件。最终还须逐条核对来源、白话是否能指导动作与前后变化，自动结构通过不签真实收益。

三个参考对象为一个代理原案＋两个合成分支，属于开放开发验证。只有独立判读至少一项实际行动改善且无严重退化，才可报告该原案的有限程序判断改善；如果只是结构化复述既有正确能力，项目影响应为NO_MEASURABLE_GAIN（未见可测改善），停同向迭代。真实用户选购收益继续未知。

## 授权、停止条件与交接

commit: false；push: false；history_rewrite: false；api_call: false。所有网络/账号/外发/付费/交易动作0；保留旧搜索6/6、读取11/12的保守账，本包不动最多余1次。

达到足够交付就停，不花满工时；同因两轮无进展、6有效工时/父包可核余额先到、必须越界或新业务事实才能证明某结论时，停受影响部分并交现有可用结果/确切未知；不得又退回整包等待外部资料。

本轮准备已证明原正常入口可运行、三个输入和旧材料可绑定、验收器可运行；冻结计划在当前未改产品上应因缺decision_plan失败，这是基线缺口，不冒充执行者L2失败。CURRENT切CONTRACT_FROZEN / Executor，下一交付为本r3/REPORT.md。本轮不提交Git或启动产品实现。
