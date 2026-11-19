# 模型比较实验｜冻结执行包

Task ID: PRINTER-MODEL-COMPARE-20261118
Task kind: capability_experiment
Contract state: CONTRACT_FROZEN
Baseline HEAD: ce34764ab7d803b06abbdbcea0afe32048096c0a
Branch: main
Pre-existing changes: 继承现有未提交状态；范围外文件按FROZEN_INPUTS.json保护，不还原或清理。
Parent direction: PRINTER-WECHAT-DECISION-FACT-20261117（未执行，保留历史，不改成完成或失败）

## 战略依据

Project map: docs/PROJECT_BOTTLENECK_MAP.md
Map revision: r35
Active bottleneck: B05
Hypothesis: H-B05-MODEL-COMPARE-01
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE
Measurement status: measured
Metric baseline: 固定旧摘要入口没有真实模型路径；已确认微信必须，两款待核；旧规则全流程与条件传递已验证。cases.json固定8例，其中5例能由原最小研究入口同源重放，另3例仅作合成保护/结构扩展验证。
Estimated affected scope: 打印机代理样本及明确标注的工程改答，通用数据处理与模型协作的有限实验；不证明跨品类或真人收益。
Expected project impact: 程序能真实调用模型生成有引用的比较，程序检查约束/计算/输出；维度通过数据扩展。是否比规则更有用须另据证据裁定，不以文字流畅、自评分或测试数计增益。
Rollback condition: 模型失败/输出不合约即拒绝，保留原始失败和规则对照；不得用合成响应伪装真实集成。

项目选购仍有B01事实缺口；本轮按用户明确要求优先验证B05模型协作能力。使用同一份旧来源做规则/模型对比，不能一边给模型加新事实一边宣称算法改善。来源不足继续未知，真人效果不作为本次程序验收的假前提。

## 单一目标

一个连续包完成“固定需求/证据→规则基线→通用约束/证据处理→真实模型比较→程序检查→改答/负向→集中报告与统一复核”。唯一主要改变为增加可实际运行的模型比较路径；不扩品类、GUI、平台或真实商品事实。

模型负责有条件解释、取舍及问题建议；程序负责类型/单位、可复验条件与计算、证据引用和不越权状态。语义是否受原文支持仍须独立判读，结构校验不能自动证明事实正确。

## 原子验收条件

### AC-01 通用数据处理及实际产品入口
- 给定候选、任意维度、约束、带来源事实及时间范围，支持布尔/枚举/数值比较；未知、撤回、冲突、过期和单位不符不得当满足；金额运算不把布尔当数字。
- 新增first-setup相关维度仅修改C08数据，不新增打印机专用核心分支。程序核心不得写死型号、微信字段或固定三个资料包。
- 有实际可调用的模块入口，默认只读/离线；真实模型调用必须显式--live。模型失败明确标记，不静默替换为规则/夹具。
- Evidence required: VP-01、产品CLI回放与C08实际输出。
- Mandatory: yes

### AC-02 真实模型及输出检查
- 用本机已有Codex/ChatGPT身份，隔离临时目录、只读、关闭工具/插件/浏览/子代理/会话持久化，仅显式脱敏输入及公开短摘要。不得读取或复制任何Key/登录文件；不安装新服务或购买额度。
- 保存实际命令、输入/输出哈希、时戳、事件回执、退出码及可取得的用量；模型版本不可取得就unknown。真实调用与单测假响应分别标记。
- 模型每个候选/维度的状态、理由、引用、条件齐全，程序拒绝伪造引用、漏硬条件、错误状态、超范围字段或越权动作。文本语义另抽查。
- 8例均尝试并保留成功或失败，C01和C08至少各有一份通过程序检查的真实输出才算有限集成成立；其余拒绝不得隐去或宣称全通过。
- Evidence required: VP-01、VP-02、evidence/live/原始回执。
- Mandatory: yes

### AC-03 公平对照及评估边界
- C01—04及C07用相同代理需求/合成改答、同R7/R10选择在现有minimal_research入口重放。模型与通用规则共享同一个bundle SHA；原规则输出原样保存，不偷改为模型结论。
- C05来源冲突、C06过期价格为明确合成保护样本；C08维度扩展为结构验证。原入口不能消费它们，不将这3例计为旧规则质量输赢。
- 覆盖改答、撤回证据、无证据、来源冲突、过期价格、对抗内容/诱导下单。固定参考只判有限客观保护；模型自评不当真人效果或独立结论。
- 来源只有首次设置时，微信后续复用/当前服务/现价/长期可靠仍未知；交易/购买/真人反馈/实机标志false。至少抽查原案、冲突和维度扩展的解释引用是否符合原文。
- Evidence required: cases.json、两路径原件、paired.json及集中判读。
- Mandatory: yes

### AC-04 范围、验证和诚实成本
- 仅修改下列允许路径；旧包原件不变。执行期最多2轮集中本地纠错，小修随主包收尾验证，不另派修复包。
- 最多10次真实模型尝试，串行，每次120秒，8例各最多2次且只重试失败例；本地门禁和独立复核只审已留存输出，不重复花模型额度。到上限交真实断点。
- 完成专项、一次必要全量及本包统一L2/L3；失败原件先归档，不能覆盖。记录调用用量/实际时段，底层计费未知不能写0。
- Evidence required: VP-01—03、调用账、REPORT及门禁原件。程序集成/资料事实/真人效果分别裁定。
- Mandatory: yes

## 允许改动范围
- 可新增shopping_decision/evidence_comparison.py、shopping_decision/model_comparison.py、scripts/run_model_comparison_experiment.py、tests/test_model_comparison.py。
- 可更新docs/01_核心能力与架构.md的实际分工说明；CURRENT.md仅按实际阶段/授权范围路由。本包REPORT.md、REVIEW.md、evidence/可写。
- 本合同、VALIDATION_PLAN.yaml、cases.json、FROZEN_INPUTS.json/.sha256及preparation/为冻结治理输入；其余既有产品/知识/测试/脚本/旧任务文件全部保护。任何必要扩范围由评估者显式修订，执行者不自行扩张。

## 合并的小修正
已有重复追问风险在模型提示/结果判读中处理：不再问微信是否必须、河南是否使用、首次设置是否接受；不修改旧入口文案。本包新路径的错误状态、失败误报等在同包纠错预算内修，不增加独立修复—复核轮次。它们不单列为能力增益。

## 明确排除
新商品联网取证、商城/供应商业务API、账号/Key读取、购机、加购、填单、订单/付款/退款、外发消息、设备代操作、Git提交推送、第三方源码/数据复制、正式36题、新品类和GUI均排除。除下述模型研究输入，不向外传输本机资料。

## 验证计划
Validation plan file: handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118/VALIDATION_PLAN.yaml

VP-01新模块有意义的行为专项；VP-02离线核真实回执、公平对照、预算和范围；VP-03一次全量。评估者以同计划独立复跑，仅离线审计模型回执，另外做原案/冲突/新维度语义判读。自动通过不等于比较更好。

## 授权、预算与停止条件
authorization basis: 用户本轮明确引用模型比较实验四项，并要求“怎么修正执行包，继续执行”；据此仅允许当前已登录Codex/ChatGPT的本次脱敏研究推理。此前业务API/账号/Key边界保留。
commit: false
push: false
history_rewrite: false
api_call: true

api_call=true仅指上述受限模型推理，不含供应商/商城API、凭证读取、新付费订购或其他账号。普通商品搜索/读取额度本包0；旧账与原包未用额度不挪用。只传本包脱敏需求和已允许短摘要，不传仓库、用户身份或秘密；不复制全文。

Expected material cost: 估计执行≤6有效小时、独立复核≤1小时；模型≤10次/单次120秒，实际tokens按回执记录、货币成本unknown；主要投入连续实现和比较，不扩审计平台。
Bounded retry / iteration budget: 2轮集中本地纠错；模型总额10、不刷新。
Attempt execution mode: SEQUENTIAL
Max parallelism: 1
Max total attempts: 10
Max attempts per unit: 2
Evidence sufficiency target: 8例已尝试，C01/C08真实合约输出成立，其他失败如实记录；不要求强选冠军。
Retryable failure families: 超时、临时服务错误、格式不合约；只重试失败例，不覆盖原件。
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118/evidence/live/attempts.jsonl
Expected value of another round if successful: 由可核的约束/引用表现、失败类型和实际复杂度决定；本轮不预先承诺扩品类或模型收益。

额度/时间耗尽、需要越权、无法取得真实模型回执时交已有实现与确切断点，不以手写输出或模型自评过关。若全部仍待核，保留这一合理结果；未知少不自动代表质量高。最终任务裁决由评估者在独立复核后给出，执行者不得自行签通过。
