# 最小研究条件传递｜集中修复合同

Task ID: PRINTER-MIN-CONDITIONS-REPAIR-20261117
Task name: 修复有限研究遗漏已确认硬条件、冲突与无线字段
Task kind: repair
Contract state: CONTRACT_FROZEN
Risk: L1
Branch: main
Baseline HEAD: ce34764ab7d803b06abbdbcea0afe32048096c0a
Parent task: PRINTER-MIN-E2E-20261117

## 战略依据

Project map: docs/PROJECT_BOTTLENECK_MAP.md
Map revision: r31
Active bottleneck: B01
Hypothesis: H-B01-MIN-FLOW-01
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE
Measurement status: measured
Metric baseline: 原包独立六项自动通过、457项通过，但11个独立入口反例仅3项符合，F1至F3使原包AC-02/AC-05不通过；原包AC-06历史工时未记录、无法补证。

这是已证实错误的修复，不是新能力实验。B01真实关键事实仍缺，先修B02内部条件传递，避免后续证据进入会漏条件的路径。继承现有脏工作树、两条旧摘要和所有历史成果/失败，不提交或清理。原包REVIEW.md及evidence/evaluator_counterexamples为权威失败依据。

## 单一目标与主要改变

让最小选包研究完整消费已有需求确认和规范化结果：明确冲突优先、硬要求不丢、未识别项保留未知，命令行/聊天/网页对共同输入得到一致的受限判断。只修这条条件传递，不新增事实或重建比较框架。

沿正常入口验证，保留两条/单条/零条资料贯通、来源日期、反馈缺失与购买关闭。不要求真人、设备、价格或海纳许可到齐才修，不拆成逐个小点的执行包。

## 原子验收条件

### AC-01 硬要求、冲突和未知完整进入可见研究

- Given：原话必须扫描/自动双面/无线，与相应确认false冲突；原话必须微信打印且可转App；原话必须A3打印。
- When：从正常命令行/聊天/网页进入所选包研究。
- Must observe：冲突保留并在正文解释，两款先待核；已识别的微信硬要求不再称未答；未知A3明确可见、待核，不猜支持性，不要求重复勾选；原话硬功能和结构化硬功能同义时得到相同的待核状态。
- Must not observe：只修特定句子的输出、将未知当不支持、用旧全量事实补包或一律全部拦截。
- Evidence required：冻结check_conditions.py全部实际入口检查、专项回归和正文原件。
- Mandatory: yes

### AC-02 入口同源与改答保护

- Given：相同明确requires_wireless=true，以及扫描/双面确认和原话条件。
- When：分别经过命令行与网页；聊天通过实际字段发送；撤销原话硬要求。
- Must observe：无线硬要求进入新研究，两款均待核；共同条件的冲突、状态和所选事实一致；撤销后冲突失效，正常原案仍可保留研究，不把false当true。
- Must not observe：网页规范化有无线必须而新报告遗漏；永远冲突或永远待核的过关补丁。
- Evidence required：冻结入口对照、正邻居/撤销反例、命令行和聊天三资料量回放。
- Mandatory: yes

### AC-03 保留已验能力、原件与诚实资源记录

- Given：原包已交付但被拒绝的快照，以及原包历史有效工时未知。
- When：在本包范围内集中修复并交接。
- Must observe：父包及范围外产品SHA不变、原14项专项保留、一次必要全量通过；所有购买/交易/新外部事实/真实效果标志关闭；本包从实际开工开始记录有时间戳的执行段和集中纠错次数，历史工时继续unknown。
- Must not observe：修改旧合同、原评审/日志/检查器，倒填历史工时、把本次回放说成真人/实机、新取证、真实效果或原包已通过。
- Evidence required：FROZEN_INPUTS.json、evidence/iterations.json、REPORT.md、完整L2及独立L3。
- Mandatory: yes

## 允许改动范围

- 可改：shopping_decision/minimal_research.py、shopping_decision/web.py、tests/test_minimal_research_flow.py。优先复用现有printer_conditions结果和完整输入，不能再建通用规则系统。
- 本包REPORT.md与evidence/可写；CURRENT.md仅按实际L2交接改路由。
- 本包CONTRACT.md、VALIDATION_PLAN.yaml、check_conditions.py、check_scope.py、FROZEN_INPUTS.json/.sha256及preparation/为评估者冻结输入，执行者不可改。
- 其他产品、旧包所有文件和真实资料注册表均不得改；若确需扩大接点，带具体断点退回评估者，不自行扩范围。

## 明确排除

新搜索/联网读取/API/Key/账号/付费/外发/设备代操作/登录/加购/订单/支付/Git提交推送全部0；不扩品类、型号、GUI、平台或框架，不复制第三方源码/业务数据，不启动正式36题，不造用户反馈/公平对照/历史成本。

## 验证计划

Validation plan file: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/VALIDATION_PLAN.yaml

VP-01冻结/范围；VP-02独立条件反例及正邻居；VP-03原三资料量正常命令行/聊天回放；VP-04保留并扩充原专项；VP-05一次必要全量；VP-06本包时间/纠错账。评估者VP-02/03写独立目录，不覆盖执行者。命令、预期退出码与映射见计划。

已知缺陷会使准备期VP-02失败；这就是修复基线，不是停止原因。其他基线失败须先记录和判断是否本包影响，不能删旧回归。旧包历史工时证据不足保留，不要求伪造材料或重跑全包。

## 成本、纠错和停止条件

Expected material cost: 估计最多4有效工时执行、独立评估1小时，置信度中等；仅本地计算和小范围维护成本，无新增付费/公网额度。
Bounded retry / iteration budget: 最多2轮集中纠错；有效执行4小时上限，不重置原包已用两轮账。
Attempt execution mode: SEQUENTIAL
Max total attempts: 2
Max parallelism: 1
Max attempts per unit: 2
Evidence sufficiency target: 冻结全部条件检查与原三案通过，不新增效果题凑数量。
Retryable failure families: 本包条件传递和本地复现错误
Stop-on-sufficiency: true
Attempt ledger: handoffs/evaluator_executor/PRINTER-MIN-CONDITIONS-REPAIR-20261117/evidence/iterations.json

开工即记录UTC起止执行段，可使用整段墙钟时间作为有效工时的保守上界；不可事后用文件修改时间推造。单支线45分钟后复盘，仍优先一次合修并集中交付。达到时间/两轮上限、需要越权或扩大范围则交已有结果；缺真人/价格不是停工理由。已通过后不反复扩大测试或顺手美化。

Expected value of another round if successful: 关闭实证条件错误，恢复本包受限判断的可信度；完成后不继续以加字段为收益续包，回到B01实际决策事实。

## 授权

commit: false
push: false
history_rewrite: false
api_call: false

无新增人工事实或权限前置；本合同只交给下一执行者，不表示评估者已实施修复。
