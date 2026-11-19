# 最小真实研究准入｜原长包有界续办草案

Task ID: HNA-RESEARCH-ADMISSION-20261116
Task name: 在用途可查的前提下，将一份真实海纳材料薄接到既有研究链
Task kind: capability_experiment
Risk: L1
Contract state: DRAFT_CONTRACT
Branch: main
Baseline HEAD: ce34764ab7d803b06abbdbcea0afe32048096c0a
Pre-existing changes: 工作树有大量既有未提交源码、知识、测试、报告及class文件；不得清理/重置；冻结前绑定实际源码哈希与完整差异。参见上一评估evidence/workspace_snapshot.json。

本包承接唯一[原长包](../../真实打印机决策验证与通用接口_下一长执行包_20261116.md)的S1/S3，不是新增平行长包，不重启旧S0—S5。**目前缺材料，不能据此改真实入口或调用API。**

## 战略依据

Project map: docs/PROJECT_BOTTLENECK_MAP.md
Map revision: r21
Active bottleneck: B01
Hypothesis: H-RESEARCH-01
Measurement status: measured
Metric baseline: 已有18次真实调用摘要；正常研究链已批准真实导入0份；H2目标身份0/2，H3地区价0，购买/交易false。
Estimated affected scope: 仅河南代理打印机原案和最多两个已有目标型号；不主张覆盖其他用户/品类。
Expected project impact: 一份有用途依据和可查字段的真实材料进入正常研究链，能区分“已发现但身份待核”和“完全无材料”，为B05提供可复核输入；认知收益不预设。
Rollback condition: 无法对每个参与解释的字段追溯原值/用途/时间，或出现预算通过/购买放行/近形型号误合并，撤回本包入口并保留原件。
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE
Expected material cost: 无新增模型/API费用、业务/元数据/公开外网动作0；待冻结实现预计最多4有效工时，独立复核预计2小时，估计置信度中等；材料等待不计实现工时。必须受原包可核余额限制，草案不重领24+8或旧12动作/4查询。
Bounded retry / iteration budget: 冻结后最多2轮集中纠错；一次有效材料导入足以核通道后停止加样；余额无法核实则先退回评估者，不倒填。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 至少1个目标型号的一份获准原值材料通过正常入口、字段追溯及必要负向；最多2个型号，不强求有完整平台SKU。
Max total attempts: 2
Max parallelism: 1
Max attempts per unit: 2
Retryable failure families: 仅合同范围内本地实现/格式错误；缺许可、无法回查、需要外部权限不可重试
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/HNA-RESEARCH-ADMISSION-20261116/evidence/iterations.json
Expected value of another round if successful: 仅当本轮输入支撑一个可辨识选择/追问/下一动作任务，才考虑后续公平对照；否则停止加解释。

## 尚未冻结的精确依赖与责任

1. 材料权利人提供适用条款或可核答复，覆盖本机解析、本人展示、必要留证；逐项标允许/有条件/不允许/未知，并写原文锚点、适用主体/版本/期限、字段限制与删除办法。链接归因义务按实际使用核对。只做这些用途，第三方模型、再分发、训练、建库均关闭，不作为必须先取得的额外权利。
2. 材料持有者交付至少1个现有目标型号的最小离线原值/允许摘录及来源定位，含工具、查询、观察时刻、实体→规格组→商品的父子层级、实际字段锚点；缺字段就记缺失。无需为研究先补平台原生SKU、河南现价或完整评论库；若以评论支持结论，须额外说明其为聚合摘要及样本局限。
3. 评估者核用途、样本、来源/时间与允许保存方式，确定原值本机位置（Git外）、样本SHA、最小审计内容、到期/撤销检查及可核资源；写入evidence/admission_receipt.json。材料含个人信息/秘密时只保留获准最小字段，Key不得进入任何资料。
4. 在冻结时绑定工作树、材料SHA与验证程序；改变AC、样本边界或权限须明示修订。到此之前CURRENT保持草案/评估者，无代码执行授权。依赖缺失不再扫描旧资料或新造合成阳性。

## 单一目标与主要改变

单一目标：在不获得严格销售/价格/购买资格的前提下，让**一份获准且可回查的真实离线材料**通过既有CLI及Python桌面/对话共享入口，输出来源、时间、型号关联、正反限制及明确下一动作。

唯一主要改变：在既有海纳MCP研究适配与共享投影中增加**按单份材料用途记录约束的真实研究入口**。复用sale_leads等现有分层；不另建状态机、规则平台或GUI。真实来源始终标真实，不能改标签借用固定合成夹具。

## 验收条件

### AC-01 用途与样本绑定

- Given：评估者已核准admission_receipt.json所列用途、字段和材料SHA；未知范围不放行。
- When：读取指定材料；分别测试缺许可、过期、撤销、材料SHA不符、用途缺项。
- Must observe：仅匹配的本机材料按许可范围解析/本人展示/最小审计；撤销/到期后的重放不能保留旧有效断言。手填approved=true不是取得许可的证明。
- Must not observe：全局开关一开接纳任意真实文件、默认保存整包、模型上传、自动扩权。
- Evidence required：用途原文锚点＋本机原值SHA绑定＋正向实料记录＋五类拒绝原件。
- Mandatory: yes

### AC-02 分层保真与相邻负向

- Given：获准小样本；独立合成反例覆盖空ID、32字符供应商返回标识、M232dw/M232dwc、混合型号、配件/二手/套餐、未知时间或未来时刻、恶意评论指令。
- When：同一研究入口解析并形成比较投影。
- Must observe：可查标题等作为待核线索；供应商字段/价格/评论、厂家事实、专业评测分别标源；保留父子层级、原文锚点、时间、未知与冲突；供应商ID命名空间不明时按供应商域保存。
- Must not observe：按ID格式/标题直接填平台原生ID，或将广告/聚合评论当独立共识。无专业评价来源时明确未知。
- Evidence required：字段映射、逐条拒绝/隔离结果、来源追溯；合成分母与实料分开。
- Mandatory: yes

### AC-03 正常入口同源

- Given：原河南代理条件版本、相同原值与许可；首设App/扫码可接受，微信软硬未知保持；预算1000元/月0—50页。
- When：CLI与Python桌面/聊天入口读取同一材料；修改已有明确条件再重算。
- Must observe：同一版本的研究资格、出处、必要问题、下一动作和审计一致；新结果可追溯真实材料，旧状态不能冒挂。无影响的微信问题不重复催答。
- Must not observe：只跑旁路解析却宣称正常链接通，模拟850元或微信必须替换代理原条件，非打印机误用本案材料。
- Evidence required：正常入口原始输入/输出与SHA；不要求改Java控件或重做原生GUI。
- Mandatory: yes

### AC-04 价格与交易保护

- Given：历史供应商报价、地区缺失、过期价格、需求条件冲突及诱导下单文字。
- When：研究、预算关系、审计及订单相关输出。
- Must observe：历史价仅为待核线索；当前预算能否满足仍未知；H2真实核验数与H3不因本包增长；购买、加购、填单、提交、支付、退款全部无授权且无动作。
- Must not observe：以供应商报价宣称河南当前到手价/预算可买，研究许可代替用户交易授权。
- Evidence required：负向输入与原始输出；无网络/账号/交易动作记录。
- Mandatory: yes

### AC-05 同基线前后比较与收益边界

- Given：冻结同一代理需求、候选/来源可用集合、时点、权限与软件基线。
- When：对比接入前与接入后逐字段出处、证据缺口、研究结果和下一动作，保留实际回答。
- Must observe：至少1份真实材料实际参与正常链，不以来源条数/说明条数冒充选购收益；说明哪些判断新增/不变及原因。新增事实即使不改排名，也不能删除相反证据。
- Must not observe：削弱旧基线、强制排名变化、把接入前后比较冒充已证认知因果收益、创建正式36条。
- Evidence required：前后实际输出、差异表、成本与失败账。无可辨别决策任务可交付“通道成立、收益未知”，独立评估再判是否继续。
- Mandatory: yes

## 允许改动范围

- May modify: shopping_decision/haina_mcp_ingest.py；必要时仅共享接线部分的shopping_decision/discovery_bridge.py、dialogue_flow.py、web.py、desktop_bridge.py、chat_bridge.py；tests/test_haina_mcp_ingest.py。
- May add: tests/test_haina_research_admission.py；本任务REPORT.md、evidence/内审计/验证程序和允许的最小用途/字段引用。
- docs/海纳商品检索离线导入与许可门禁.md仅按评估者已核用途范围修订；不得写成本轮不用的所有权利必须齐备。
- 不必修改全部列出的文件。素材与协议需本机保存时遵守核准留存范围；原始响应/个人数据/凭证不入Git。来源锚点与SHA按许可最小保留。
- 冻结前由评估者定稿evidence/verify_delivery.py的验收逻辑：检查receipt、原值绑定、真实入口回放与AC-01—05的实际证据；执行者不得自改验收器来通过。

## 明确排除与禁止副作用

- 不修改sale_configuration_evidence.py及REAL_SALE_EVIDENCE_ENABLED，不批量开启其他真实入口；不改既有合成夹具哈希来冒充真数据。
- 不新增品类、GUI、模型、平台账号自动化、持久登录、海纳业务/元数据调用、公网抓取、付费、询证发送、提交/推送。
- 不修改旧评分/失败/来源原值，不复刻第三方源码数据。
- 不把本包当生产可用、完整海纳集成、平台SKU或河南当前价验收。

## 验证计划

Validation plan file: handoffs/evaluator_executor/HNA-RESEARCH-ADMISSION-20261116/VALIDATION_PLAN.yaml

| VP | 动作 | 预期 | AC |
|---|---|---|---|
| VP-01 | 用途约束与分层专测 | 新正负向通过；真实来源与合成分开 | AC-01—04 |
| VP-02 | 现有MCP专项 | 固定合成与身份/报价保护保持 | AC-02、04 |
| VP-03 | 评估者冻结的交付核验器 | 核原值/receipt、正常入口实际回放及前后差异；缺材料应非0退出，不可跳过算通过 | AC-01—05 |
| VP-04 | 一次必要全量 | 涉及共享入口改动后无回归 | AC-03、04 |

草案计划已给出精确命令；verify_delivery.py及实料receipt尚不能冻结，未运行下一包验证。冻结后使用技能自带run_validation.py按--mode executor生成执行原件，评估者再按--mode evaluator独立重跑；不得以本轮16/16代替下一包。无Java/GUI代码改动不重做GUI；若必须改UI则超范围退回评估者。

## 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- 当前仅允许评估者制定/核材料；实现与真实数据使用须待冻结入口条件满足。外部材料的许可不能由本合同代为授予。

## 停止条件

- 未取得适用最小用途材料、可查原值或可核预算：停对应分支，不写新框架。
- 到时/到次数上限；两次无进展；需要新增API、权限、文件范围或改变假设/验收。
- 发现原值混型号但无法隔离、字段来源无法审计、实际许可不支持必要留证。
- 任一价格/身份/交易保护退化；保留失败并撤回本包真实入口。
- 来源或协议到期/撤销；重新取得材料前不得继续重放为有效结论。

## Amendments

None. 尚未冻结；下一责任评估者核精确缺件并绑定验证器，然后才转执行者。
