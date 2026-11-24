# 打印机聊天｜以用户确认的硬条件核对商品

Task ID: PRINTER-CHAT-REQUIREMENT-AUTHORITY-20261124
Task kind: repair
Contract state: CONTRACT_FROZEN
Current role: Executor
Baseline HEAD: 4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf
Validation plan file: handoffs/evaluator_executor/PRINTER-CHAT-REQUIREMENT-AUTHORITY-20261124/VALIDATION_PLAN.yaml

## 战略依据

普通聊天能收集、修改打印机需求并提供待核下一步。B06 仍卡在将资料变成用户可见判断的一步。上一包冻结的 12 条命令及 527 项回归通过，新独立重放 7 个检查中有 3 个失败。预算计算以用户确认值为准，微信条件仍可能被资料反写、遗漏或用通用功能替代具体方式。[上一包独立裁定](../PRINTER-CHAT-CONTEXT-20261124/REVIEW.md)

唯一主要改变是让当前会话决定打印机硬条件和候选的研究资格，商品资料只提供可比较的事实。假设是同一会话、同一事实下，改写资料包的条件或变更排列不能提高候选资格。合法独立价格与正确功能仍可分别展示。先修这个前提，避免把 B01 新资料接入仍会误报的出口。已有可复现反例与明确的修改边界，单包完成；待正确性通过后，优先投入能改变两款下一行动的准确型号微信证据。河南应付价还缺收货县区与预算费用范围。

## 执行

从同一工作区、仓库根目录运行，使用 WSL Python 3.12 与 PyYAML。先读 `CURRENT.md`、本合同和上一包裁定。核新基线哈希、HEAD 与范围。开始时保存范围校验退出 0、独立重放退出 1 及三个失败的原始输出。保持旧测试、报告和拒绝记录。

用现有会话字段和打印机条件语义核需求。对当前支持的硬功能，从用户已确认的字段确定角色、目标值和单位，处理包内漏行、冲突行或不完整证据。先检查全包结构，复用已通过的证据范围和规则计算。保护旧合成预算单项和通用微信单项。对具体现有微信路径按路径核证据，通用微信功能只支持它自己的比较项。不要按反例中的条件 ID、候选 ID、条数或固定顺序匹配。

```bash
task=handoffs/evaluator_executor/PRINTER-CHAT-REQUIREMENT-AUTHORITY-20261124
previous=handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124
workflow_skill=/mnt/c/Users/HuailiShang/.codex/skills/evaluator-executor-workflow/scripts
python3 -X utf8 "$task/VERIFY_SCOPE.py" --phase start
python3 -X utf8 "$previous/evidence/evaluator/replay_session_conditions.py"
python3 -X utf8 "$workflow_skill/run_validation.py" --repo . --plan "$task/VALIDATION_PLAN.yaml" --out "$task/evidence/executor/l2" --mode executor
python3 -X utf8 "$workflow_skill/validate_workflow.py" --repo . --current CURRENT.md
```

## 强制验收

### AC-01 用户确认硬条件不可由资料重写

微信必须时，用户确认的功能要求不能用资料包中 `eq false`、错误单位、较软的权重、重复或缺失行代替。没有能对应当前硬条件的有效结构化资料时，聊天明确该条件待核，候选保留待核资格。来自同型号、同使用地、有效期内的明确反证可以判不满足。完整正例继续显示命题 ID、来源和对应状态。合法独立报价仍可单项显示，预算通过与候选满足硬条件分别表达。覆盖已确认的扫描、自动双面及必须在家彩印三种同类硬条件中至少一个相邻测试，缺少有关资料时需保留硬条件；不把用户「不要求」转成必须缺少该功能。

### AC-02 微信具体路径、改答与撤回

硬条件指定小程序直接打印时，只有通用微信支持或转厂家 App 资料时，具体路径待核或有确证不满足，候选不得视为已满足其硬条件。保留当前适用地与准确路径匹配的合成正例和来源。微信从必须改可选、撤回或换品类后，仅根据当前确认值判断；原资料包被正确判过期，即使新包结构合格也不能沿用旧硬条件。无需增加新的用户问答字段。

### AC-03 继承普通聊天和原先保护

运行上一包 VP-01 至 VP-11，冻结的正常河南原案、两次改答、地区/时间/结构/预算正反例均通过；缺证据、对抗性资料、过期价、条件冲突、诱导下单回归保留。独立重放由 4/7 至 7/7，新专项实际运行至少 4 项，包含条件反写、遗漏、具体路径、变更或撤回。全量现有 527 项全部保留并纳入新增专项。下单、交易和实时价已核标志始终为 false；历史模型 6/10、C05/C06/C07 缺测、合约输出 0 保持。

### AC-04 可独立复核

保留修复前后普通入口文本、命题和候选资格、实际尝试次数、运行回执、工作区差分及保护文件验证。提交 `REPORT.md` 和 `evidence/executor/`，列出已绑定条件与缺证行动，逐条对应 AC。报告把本地规则修复与原案商品事实、真人收益分开。提交评估者后由其独立复跑，再给裁定。

## 允许改动范围

允许修改 `shopping_decision/chat_bridge.py`，新增 `tests/test_chat_requirement_authority.py`。允许在本包写 `REPORT.md` 和 `evidence/executor/`，按阶段更新 `CURRENT.md`。其余文件为保护件。

## 明确排除和授权

仅本地代码与离线验证。真实资料接线、联网、真实模型、平台 API、账号、凭据、设备、付费、外发及交易均超范围。Git 提交、推送和历史改写无授权。保持父包拒绝裁定、历史预算、共用门禁、旧测试、Web 与桌面入口。

## 停止条件

执行上限 3 有效小时、1 轮集中修正，评估者独立复核建议上限 1 小时。若强制项不能在上限内完成，保留失败回执，写清未完成条件和范围阻断。达标即报告送审。独立通过后停止扩大合成修复，将下一笔投入转向能改变原案下一行动的真实证据。
