# Frozen Task Contract

Task ID: PRINTER-SCENE-ROBUSTNESS-20261127
Task name: 普通说法也能沿同一链问到关键条件
Task kind: repair
Risk: L1
Contract state: CONTRACT_FROZEN
Branch: 当前分支，不建分支、不提交
Baseline HEAD: c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f
Pre-existing changes: BASELINE.json逐字节继承；原拒绝、执行者原件及未提交成果保留。

## Strategic basis

Project map: docs/PROJECT_BOTTLENECK_MAP_CURRENT.md
Map revision: r45
Active bottleneck: B05
Hypothesis: H-B05-SCENE-ROBUSTNESS-REPAIR-01
Measurement status: measured
Metric baseline: 原24离线任务24/24；新H07三改写0/3，四个无关问题后停止；原L3 13/14。
Estimated affected scope: 已有打印机本地用途到当前问题、本人确认、候选补证；仅原两型号和原已审核资料。
Expected project impact: 修复确定的场景遗漏，保持已证控制，不在本包声称真人或模型增益。
Rollback condition: 任一代确认、缺证造真、授权复活、原控制退化立即停产品扩张，保留失败原件交Evaluator。
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE
Expected material cost: ≤12有效小时/2集中纠错；模型/外部费用0；一次共同L2和独立L3，主要成本是变体与完整链验证。
Bounded retry / iteration budget: 12有效小时、2集中纠错；已知等待和有效时间分列，用可证墙钟上界保守扣除。旧240小时及项目累计未知不重置、不当0。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 冻结24新场景全过、原24控制全过、三披露完整链全过、旧安全回归及8后续独立留出。
Max total attempts: 2集中纠错
Max parallelism: 1
Max attempts per unit: 2高成本复验；便宜定位可汇总
Retryable failure families: 有明确原因的本机测试/实现缺陷；无网络重试
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/PRINTER-SCENE-ROBUSTNESS-20261127/evidence/executor/activity.jsonl
Expected value of another round if successful: 只为后续真人理解试验提供干净工程基础，不自动获得真人/模型/平台权限。

## Single objective

在同一现有会话中，使关键用途的生活化改写、否定干扰和歧义表达得到合适的当前确认问题；只提交本人实际回答，沿原路线/型号缺证链继续，来源和恢复仍同源。唯一主改变是本地用途到当前问题的选择规则；不另造语义引擎、用户状态或参数体系。

## Carried review corrections

| 来源 | 合并处置 | 验证 | 额度 |
|---|---|---|---|
| 上包AC-02/H07 | 先读冻结SCENARIOS，支持表达关系、否定与歧义，不只硬编码三句全文；不把推断当本人确认 | 新24场景/原24控制/三完整链/后续8独立留出 | 主工作≤10小时 |
| 上包AC-10 | 每个Python检查显式PYTHONPATH；旧验收器和旧FAIL不改 | 新完整L2/L3，无环境前提猜测 | ≤1小时 |
| 上包AC-11 | 首次工具同期捕获时间，首读CURRENT后立即落start，后续start/end；只控制未来区间，不追认旧上界 | VERIFY_PACKET delivery与审账 | ≤1小时 |

## Acceptance criteria

### AC-01
Type: 场景相关性与本人确认。
Given: 冻结SCENARIOS.json的12正向、6否定干扰、6歧义。
When: 真实stdin读当前问题及本人提交/暂缓。
Must observe: 24/24当前字段属于独立参考允许集；focus/prompt/context/note同源；读不改状态；确认或暂缓后不重复该字段；无源技术判断不得借user_choice发布。
Must not observe: 全文特判样例、从用途自动填偏好、否定词被当硬答案、为覆盖把所有问题预填。
Evidence required: VERIFY_SCENARIOS实际stdin/stdout/逐案结果，新测试至少覆盖正向/否定/歧义各3例。
Mandatory: yes

### AC-02
Type: 完整链与安全回归。
Given: 上包H07三例和冻结原24任务。
When: 只答真实当前问题，最多12回答、30读调用；未知保持暂缓。
Must observe: 三例分别明确扫描/自动双面/长间隔后到型号功能缺证/使用场景具体补证，改答/撤回/来源新版/恢复均重算；原24任务不低于既有24完成，目标与回答能力/来源不改。
Must not observe: 把首问通过冒充完整任务完成、方法替代型号、软成本复活硬失败、实时报价或授权造真。
Evidence required: 新CONTROL_REPLAY报告与实际原件、三例完整轨迹、旧行动与业务回归。
Mandatory: yes

### AC-03
Type: 真实入口一致性。
Given: 同一Python、旧focus接口、现有Windows主屏。
When: 新用途变体从普通输入进入，来源撤回或新进程恢复。
Must observe: 至少三种变体各一次真实窗口确认链，另一次来源失效/恢复不复活；旧10原生链仍通过。可新增本包薄原生回归，不改旧Java回归/主屏协议。
Must not observe: 反射注入最终结果、SKIP冒充通过、增加第二应用或私密存档。
Evidence required: 本包原生原件与新专项。
Mandatory: yes

### AC-04
Type: 验收可复现。
Given: 显式WSL导入环境和现有Windows依赖。
When: 完整标准runner。
Must observe: 全量至少689、旧focus专项和安全回归通过；原24控制真实重放。L2全过才可交；Evaluator独立L3及另8未披露输入不混分母。
Must not observe: 修改旧门禁结果、跳过旧测试、隐藏加载异常、改变冻结参考迎合实现。
Evidence required: 完整L2/L3 meta/stdout/stderr；新专项异常完整呈现。
Mandatory: yes

### AC-05
Type: 范围与历史保护。
Given: BASELINE及继承未提交成果。
When: start/post及交付指纹检查。
Must observe: HEAD/索引/保护件一致；历史模型6安排结束0接受、C05/C06/C07未试不改；只允许精确当前候选兼容。
Must not observe: 删除旧失败/日志、通配放行、提交推送或新依赖。
Evidence required: VERIFY_PACKET scope、历史审计及专项。
Mandatory: yes

### AC-06
Type: 过程与交接。
Given: 上包工时不可证缺口永久保留。
When: 新包首个调用到交付。
Must observe: 同期start/end；未知段如实未知，缺可证上界即停扩张交Evaluator；机器时长和墙钟/有效时间不混同，预算≤12小时/2轮。REPORT逐AC、CONTROL_REPLAY、源和产品SHA可重算。
Must not observe: 自报请求时间代替独立日志、旧缺口改成0、擅自新模型/公开研究/平台/外发/交易。
Evidence required: activity.jsonl、process.json、REPORT、manifest和VERIFY_PACKET delivery；人工核时。
Mandatory: yes

## Allowed scope

可改shopping_decision/focus_guidance.py、chat_bridge.py；仅必要且接口语义不变时可改cognition_guide.py/context_builder.py/decision_note.py以保持同源。scripts/audit_model_history_readonly.py只允许追加当前精确SHA兼容候选。可新增tests/test_scene_robustness.py与desktop/SceneRobustnessRegression.java/SceneRobustnessSwingRegression.java。本包evidence/executor、REPORT、CONTROL_REPLAY、USAGE可写；CURRENT只能按交接状态维护。

本包CONTRACT/SCENARIOS/BASELINE/VERIFY_*/VALIDATION_PLAN为冻结只读；Evaluator只写本包REVIEW/evidence/evaluator、地图和治理文件。旧产品、知识和所有旧任务原件不得改；现有未提交成果继承。

## Exclusions and forbidden side effects

模型API/CLI、公开检索、平台API、账号/设备、安装/消息/上传/发布/交易、Git提交推送索引改写全0。只用合成资料。本包不扩地区/型号/品类、专业来源、成本引擎或新协议，不新增用户字段/第二权威状态。仅本机新路径合成保存。

## Validation plan

Validation plan file: handoffs/evaluator_executor/PRINTER-SCENE-ROBUSTNESS-20261127/VALIDATION_PLAN.yaml
原24控制及三完整链应由本包CONTROL_REPLAY产真实原件，冻结VERIFY_PACKET核其目标/答复纪律、产品指纹和实测结果。现有研究资料只读，无新来源收益。

## Authorization

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_existing_local_model_cli: false
authorization_platform_business_api: false
authorization_public_research: false

## Stop conditions

2小时内连三披露变体的真实问题选择都无信号，先诊断一次；两集中轮后无净进展、12小时到限、范围/接口/参考需变化、出现安全回归或需要未获权限即停，保留断点。不能不断扩同义词直至样例全绿；Evaluator另8留出失败如实回报。达标提前交，不为用满预算造工作。

## Amendments

None。
