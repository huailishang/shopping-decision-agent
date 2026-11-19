# 主动取得关键资料并交付调查结果｜原长包前置任务

Task ID: HNA-EVIDENCE-REOPEN-20261116
Task name: 沿明确来源主动取证，交候选材料或有据的失败结果
Task kind: evaluator_design
Risk: L0
Contract state: CONTRACT_FROZEN
Contract revision: r2-acquisition / 2026-11-17
Branch: main
Baseline HEAD: ce34764ab7d803b06abbdbcea0afe32048096c0a
Pre-existing changes: 保留全部工作树及父包21份交付原件；120项产品源码/资料仍绑定父包planning_r2_baseline.json。本次只改取证/验收任务，产品规则不改。

## 一句话要做什么

**执行者现在就可以开始：先查仓内原文，再在剩余预算内沿官方链接取资料，最后提交“找到什么”或“为何找不到”。不再以外部材料先送到手上作为开始条件。**

本任务交的是调查结果，不能自动恢复产品改造、批准海纳数据使用或认定微信复用成功。原六步长包仍是后续主线；本任务是把它的取证前提实际做完。

## 战略依据

Project map: docs/PROJECT_BOTTLENECK_MAP.md
Map revision: r24
Active bottleneck: B01
Hypothesis: NONE
Measurement status: NOT_APPLICABLE
Metric baseline: 父包新增正常链材料0、可判新效果题0；旧CLI仍仅型号研究。前一任务只有“收到材料后核验”，缺主动取得路径。
Expected project impact: 减少取证和验收准备的循环等待；不宣称本任务带来选购能力增益。
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE
Expected material cost: 沿原前置任务2有效小时上限；查本地原文不耗公网数；厂家最多4次读取、海纳条款最多3次读取，合计最多7次。估计置信度中等，无新付费或新24+6工时。
Bounded retry / iteration budget: 外部入口每页最多1次，无自动重试；一次集中交付，合同内本地记录/格式错误最多2轮集中纠正。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 完成有界调查并形成可复核结果；取得1份相关候选事实已足够停止继续读。确实未取得也可交真实结果，不能伪造阳性。
Max total attempts: 7
Max parallelism: 1
Max attempts per unit: 1
Retryable failure families: 仅本地记录/格式错误；403、登录要求、无正文、超时不重试
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/HNA-EVIDENCE-REOPEN-20261116/evidence/acquisition_receipt.json
Expected value of another round if successful: 评估者核定材料能支持实际判断后，才恢复父长包；无有效材料则只交精确人工取证请求。

## 谁负责什么

| 责任 | 必须做的动作 | 不能推给别人等着做的部分 |
|---|---|---|
| 执行者 | 本地原文核查、预算内官方文档读取、保存允许的最小摘录/字段锚点和动作证据、形成调查回执与报告 | 不能一上来就说“请材料持有者提供”，跳过已允许的本地/公开路径 |
| 评估者 | 本轮已定稿路线、检查脚本和失败样例；提交后独立核原文、范围与行动意义，再决定父包是否恢复 | 执行者提交前不必先拿到独立评审结论；评估者不能把自己的核验工具缺件归为执行者产品故障 |
| 协议/设备材料持有者 | 仅当公开路径确实到受限或无对应内容时，按已写好的最小请求草稿补私人可见条款或自愿实测事实 | 不把“可能有人有设备/账号”写成已落实；本任务不自动发送消息、不登录其账号 |

## 取证路线：先A，必要时转B

确切来源、禁止重复入口和各自预算冻结在[acquisition_plan.json](acquisition_plan.json)。不猜URL、不再用搜索引擎；新链接只能来自已取得官方原文中真实出现的链接。旧来源也可能含此前未使用的相关事实，不强求换来源。

### A 厂家微信后续使用路径，执行者负责，最多4次公网读取

1. 先读仓内known sources：knowledge/real_printer_case_comparison_20261115.json中R7/R10；父包材料清单；已缓存Brother安装PDF。只查仓内这些指明资料及它们的已登记原文，不扫描用户目录或凭证。
2. 问题固定为：**准确型号第一次绑定后，后续打印需要哪些网络/权限/在线条件？哪些情况须重绑？** 不再为未确认的双面/扫描要求消耗本轮预算。
3. 现存Brother流程入口：
   https://support.brother.com/g/s/id/htmldoc/printer/cv_hll1230w/sch/html/GUID-849C5AB7-8304-49CC-90D6-7FE8C315EBBB_1.html
   HP系列安装原件入口：
   https://h10032.www1.hp.com/ctg/Manual/c07140981.pdf
   先用已有原文；无相应原值或有明确下一链接才扣预算读取，不把重复首次绑定说明当新增。
4. 沿原文明确标注的后续打印/远程/重绑官方链接核少量原值。记录准确型号/系列范围、适用地区、原文位置、获取日期、支持结论及相反限制。
5. 找到有行动意义的候选事实就停止增加读取，直接提交评估；不能由“Wi-Fi成功”“首次在线”推成二次打印成功，更不能推长期可靠。
6. 遇403、登录、无正文、超时，记原始工具结果并停该入口；不换代理、镜像、账号或相邻FAQ绕过。没有有效事实，A写终止原因，继续B，不能结束为泛泛等材料。

### B 海纳最小用途的公开正文路径，执行者负责，最多3次公网读取

1. 先读仓内supplier_haina_platform_public_20261109.json、supplier_haina_mcp_docs_20261109.json及Beta说明，检查协议实际可见位置，不再重盘18份业务摘要。
2. 公开入口为 https://ai.zhidemai.com/haina-platform 和 https://ai.zhidemai.com/haina-platform/haina_mcp 。只找实际显示的开发者合作协议/用户协议链接及最小用途正文；旧主页无正文的 https://ai.zhidemai.com/ 不重读。
3. 若条款可公开读到，只核本机解析、本人展示、必要留证和实际适用的归因/删除范围，记录主体、版本及出处；不以商品接口能调通代替许可。
4. 若条款在账号内或要求登录，停止公开路线，使用[OWNER_REQUESTS.md](OWNER_REQUESTS.md)中的海纳请求草稿。**先取得最小用途依据，再决定是否允许提供目标原值；不能先索取/保存新的业务响应。**
5. 本任务不取Key、不登录、不调用海纳业务/元数据、不向供应商发信。公开可读不等于已准许正式解析，执行者只标“待评估者核定”。

### 两路都不够时的替代交付

执行者须交：两路实际查过的路径/证据、哪一步受限或未发现相应事实、最小缺件、该找哪种材料持有者、对方应提供哪一页/哪条记录，以及可直接使用的请求草稿。草稿保持未发送。

已有设备测试只是一条人工补证选项：拥有准确型号的人自愿记录首次与二次输出、日期、是否重绑/变网；没有设备就不测试、不购机。尚无设备/人员事实时明确写未落实，不能把这条替代路线当已完成。

## 允许的两种任务结果

- candidate_found：取得至少一份有来源、日期、适用范围、原文绑定和行动意义的候选事实；只提交独立评估，**并非已准入产品**。
- no_actionable_evidence：两路已完成有据的调查停点，附最小人工请求草稿、具体责任角色及下一步；**不是认知收益为0，也不是程序完成**。

这两种调查结果都能形成完整提交。阳性不是完成取证任务的必选答案；“没有人先送来材料”不再是停止本任务的起点。

## 冻结验收条件

### AC-01 主动取得路径实际执行

- Given：路线与现有本地文件/公开只读余额已明确，无需先取得私人资料。
- When：执行者依A→必要时B操作。
- Must observe：每条未被充分证据提前终止的路线都有实际本地核查/读取记录和最终原因；新链接有原文出处；未调查不能写完成。
- Must not observe：跳过主动路径直接等用户补件；猜URL或重复受限入口。
- Evidence required：动作时间/路线/输入/结果＋相应最小证据绑定。
- Mandatory: yes

### AC-02 范围、出处与原值分清

- Given：候选事实或没有事实的实际记录。
- When：绑定来源、型号/主体范围、获取时刻及允许摘录SHA。
- Must observe：原文/允许摘录、工具结果与分析笔记分开；有反证与局限；旧资料里新事实可以被考虑，单纯改写不算新事实。
- Must not observe：本地笔记哈希冒充远端字节哈希；系列/Windows/首次在线替代准确型号二次微信成功。
- Evidence required：候选materials或有据的无候选说明；需独立评审才能认定真假/许可。
- Mandatory: yes

### AC-03 找不到也给出可用结论

- Given：两路终止而无候选。
- When：提交最小人工请求和调查结果。
- Must observe：准确的接收角色、确切缺件、为何需要、对方怎么提供、无设备/无账号时的停止方式；请求草稿未发送。
- Must not observe：只有“等材料”三个字，或把未联系的人/不存在的设备当成已经落实。
- Evidence required：OWNER_REQUESTS中的对应草稿最小定制摘录及其SHA；回执next_step。
- Mandatory: yes

### AC-04 预算与授权不增长

- Given：原账6/6搜索、5/12读取。
- When：新动作共同扣最多7读取（A≤4、B≤3）；PDF远端渲染也计1。
- Must observe：失败计数；旧账不覆盖；业务/元数据/Key/账号/付费/外发/交易0；产品120项未变。
- Must not observe：新搜索、重试403、自动打开购买/支付路径、新24+6或自动恢复父包。
- Evidence required：回执动作账、父账SHA、禁行计数、安全标志。
- Mandatory: yes

### AC-05 提交和独立评审不循环等待

- Given：本轮已完成检查脚本和验证计划。
- When：执行者运行冻结验证、写REPORT提交；评估者之后独立复核。
- Must observe：L2只要求调查交付完整，不要求提交前先有REVIEW或已批准资料。评估者核候选事实后才能另行决定恢复父长包。
- Must not observe：执行者自批许可/来源/父包恢复，或把结构检查成功当成事实正确、认知有效。
- Evidence required：L2执行原件、报告和独立L3原件/判读，分别记录。
- Mandatory: yes

## 交付文件与结构

- evidence/acquisition_receipt.json：按evidence-acquisition-receipt/v2，记录actions、route_results、materials、owner_request（无候选时必需）、next_step、安全标志及prohibited_actions。
- 每个action有唯一id、route_id、kind(local/document/render)、recorded_at、outcome(readable/no_relevant_fact/new_fact/restricted/empty/owner_only/timeout)、evidence(path/sha256)；local另有input_path，document/render另有url，后续链接有discovered_from。
- 每份候选材料含action_id、model_or_subject_scope、supported_claim、limitations、action_relevance、observed_on、novelty=new_relevant_fact、review_status=pending_evaluator和证据绑定。
- route_results逐A/B写owner=Executor、state(candidate/no_relevant_fact/restricted/owner_only/budget_stop/skipped_sufficient)、reason及action_ids；只有已取得候选时才可跳过另一条路。
- 无候选时owner_request写recipient_role、exact_item、sent=false及具体请求草稿的证据绑定。它不要求已经有人答复。
- 允许保存的最小摘录/错误记录放evidence/collected/；取得范围不允许原文保存时只按允许范围留证，写明限制，不能伪装成远端完整响应。
- REPORT.md记录实际范围、候选或无候选结论、工时/额度、未发请求、偏差和L2原件；执行者不写最终PASS。
- [FROZEN_INPUTS.json](FROZEN_INPUTS.json)绑定本合同、路线、检查代码、父账及产品快照。它只保护本次任务，不授予任何新数据权利。

## 允许改动范围

May add: 本任务REPORT.md、evidence/中的新调查原件/回执及L2/L3文件；未获许可的整份业务响应、密钥或个人信息不得写入。
May modify: 本任务合同/路线/检查程序仅评估者明示修订可改；执行者可在范围内新增调查记录，不能为了通过而改检查器。
当前执行者不改CURRENT最终状态；准备/提交报告时遵守工作流，由评估者接受后切换角色。原长包合同/报告/旧失败不覆盖。

## 明确排除

产品代码、知识规则、旧评分/失败、真实价格/订单系统；新搜索、API、账号、付费、消息发送、设备代操作与所有交易；非本任务新功能。找不到材料的完整调查提交不会升级H1/H2/H3或认知收益。

## 验证计划

Validation plan file: handoffs/evaluator_executor/HNA-EVIDENCE-REOPEN-20261116/VALIDATION_PLAN.yaml

| VP | 检查 | AC |
|---|---|---|
| VP-01 | 冻结输入及120项产品未变 | AC-04、05 |
| VP-02 | 检查器的15个合成正负反例 | AC-01—05 |
| VP-03 | 本轮调查回执/出处/双路终止/人工草稿/预算 | AC-01—05 |

计划不发网络请求。完整来源、用途和行动意义仍由评估者看原文独立判断；结构成功只证明可提交。15个合成样例不计真实材料/实机/认知效果。

执行者：用技能run_validation.py --repo . --plan本计划 --out本任务evidence --mode executor；完成L2再写REPORT提交。评估者接受同一快照后用--mode evaluator重跑，无需重放网络或覆盖执行原件。输入/命令/hash被冻结，无须等待尚不存在的独立评审文件才提交。

## 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- 继承原长包已启动的公开只读余额，最多7读取，不新增搜索。用户本轮要求完善执行包；本轮只完善/冻结，未开展资料收集。

## 停止条件

- 取得一份相关候选事实即停止额外取证并交评估。
- 入口受限/登录/空页/超时即停该入口，转另一明确路线；两路都不足按无候选结果交付。
- 7读取或原2小时先到上限；不得为凑数花完额度。
- 需要新账号/API/付费/外发、修改产品或更换验收语义：停止对应动作并说明，不能扩大权限。
- 执行者报告能交，但父包只有评估者核事实后才可能恢复；短时打印记录不证明长期可靠。

## Amendments

r2-acquisition / 2026-11-17：按用户“按约定完善”修正r1只等材料的缺口。将“材料先到才能开始”改为执行者主动完成有界取证；允许有据的无候选结果；删除提交前必须先有独立REVIEW的循环条件；补齐检查脚本/失败样例并冻结。旧版保存在[CONTRACT.r1_仅核验草案.md](CONTRACT.r1_仅核验草案.md)，原长包研究/交易门槛不变。
