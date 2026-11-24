# 以用户确认的条件核对商品｜打印机修复与水壶离线迁移

Task ID: GENERIC-CONFIRMED-REQUIREMENTS-20261124
Task kind: repair
Contract state: CONTRACT_FROZEN
Current role: Executor
Baseline HEAD: 4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf
Validation plan file: handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124/VALIDATION_PLAN.yaml

## 战略依据

项目已能确认打印机需求、处理改答并展示待核研究。B06 仍阻断正常聊天发布可信比较。上一包独立复跑 12 项冻结命令及 527 项全量回归通过，但补测发现资料可以反写或省略微信硬条件，也能用通用微信支持顶替指定的小程序方式。[独立裁定](../PRINTER-CHAT-CONTEXT-20261124/REVIEW.md)

本包接替尚未开工的 [打印机硬条件绑定包](../PRINTER-CHAT-REQUIREMENT-AUTHORITY-20261124/CONTRACT.md)，沿用同一实现快照、原案、三个失败和历史保护。在同一修复上增加一个验证：水壶场景只替换条件定义和证据样例，走正常打印机聊天也调用的比较入口。假设是由确认条件控制比较目标后，同一会话、同一事实中，省略、放宽或降为偏好的资料改动无法提高候选资格。打印机内部多功能回归与水壶迁移用来检验同一假设。

优先修这个出口再接 B01 真实材料。准确微信路径、河南应付价、真人收益仍待证。第二品类只用于离线工程证明，实际选购验证继续以打印机为先。

## 程序约定

1. 正常聊天从当前用户确认值生成比较条件，沿用现有打印机语义。包含条件维度、运算、值、单位和重要性。未完成映射的已确认硬条件须进入待核说明。用户改答、撤回和切品类按最新会话重算。“不要求”去掉硬性约束，只有明确禁止时才是反向条件。
2. 在 `shopping_decision/confirmed_comparison.py` 提供一个可直接验证的共用入口 `publish_confirmed_comparison(bundle, confirmed_requirements, *, as_of, deployment_region, delivery_region=None, budget_scope=None)`。`confirmed_requirements` 使用现有比较器的条件行结构，作为独立输入。商品资料的候选、事实和来源仍先做完整结构核验。旧包夹带的条件行可用于兼容原命题标识，比较含义、权重和资格以确认条件为准。对资料仍可审计并稳定降级。复用现有规则计算与受控文字；报价、功能、使用地、收货地和时间限制继续适用。
3. 对每个候选核查所有确认硬条件。有适用反证则排除，有缺项或冲突则待核，硬条件均满足时才标记可进入研究比较。继续分别展示有据的单项及待核项。沿用现有公开结果的命题、来源、候选资格和安全字段。候选的研究资格不构成购买授权。
4. 冻结的水壶样例把用户确认的高度上限和商品读数归一到毫米，保留机身、含底座的独立语义。它直接调用上述入口。打印机聊天应实际调用同一个入口，执行者在报告标出正常调用点。水壶样例不进入产品界面、研究后端或产品知识库。

## 强制验收

### AC-01 打印机硬条件准确绑定

- 已确认微信必须时，资料反写、漏项或降为偏好不能提高候选资格。具有适用反证时按真实条件判断；缺证显示待核。独立报价依然可以显示。
- 具体小程序和转 App 按各自适用证据核查。通用微信事实不足以证明具体路径。正例保留事实与来源引用和命题 ID。
- 微信改可选、撤回、切品类后，旧包不能恢复旧硬条件。新增专项同时覆盖扫描、自动双面或必须在家彩印至少一项，使用正常聊天入口验证缺证、正例或撤回语义。

### AC-02 共用入口可以迁移

- 打印机正常聊天调用共用入口。水壶离线样例只改变条件和证据输入，调用同一函数。共用入口按条件的类型与范围判断，水壶型号与尺寸字段只应出现在样例中。
- 通过全部冻结水壶用例，覆盖含底座 230 mm 边界满足、240 mm 明确超限、只有 210 mm 壶身时待核、漏项、擅放宽、硬条件降为偏好、过期、事实冲突和确认上限改为 210 mm。要求保留可独立验证的容量结论、证据引用和候选总状态。
- 独立复核时再从型号、字段、单位、顺序和候选中改动至少一个因素，另做一组保持有效邻项的反例。该结果只支持离线迁移判断。

### AC-03 继承回归与边界

- 上一轮 11 项行为及历史检查原样继承，河南家庭原案及改答、结构/地区/价格时效、合成正反例和旧命题标识继续通过。至少新增 4 项真实入口专项，全量运行不少于原 527 项加新增用例。
- 缺证据、对抗资料、过期价、条件冲突、误下单负向覆盖保留。购买、交易、实时报价已核标志均为 false。旧账仍为 6/10，C05/C06/C07 缺测，合约成功输出为 0。冻结历史裁定继续保留。

### AC-04 可独立复核

- 交 `REPORT.md` 与 `evidence/executor/`，附开始快照、前后命题和资格、全部冻结命令与原始回执、差分与哈希、实际用时和轮次。
- 报告说明哪些条件来自确认值、如何保留报价单项及缺证行动、如何从打印机正常入口进入共用比较。分别记录打印机修复、离线迁移、尚待真实验证的商品事实和用户收益。

## 执行顺序

使用当前同一工作区，仓库根目录，WSL Python 3.12 与 PyYAML。先核基线及准备回执。开始范围检查预期退出 0。评估者已记录 [打印机前测](preparation/printer.stdout.json) 4/7 和 [水壶前测](preparation/kettle.stdout.json) 5/9，两条命令均退出 1，stderr 为空。水壶对照走现有比较器，后测使用同一份数据和同一判断标准，再加一条实际打印机聊天共用入口检查，合计 10 项。

```bash
task=handoffs/evaluator_executor/GENERIC-CONFIRMED-REQUIREMENTS-20261124
prior=handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124
workflow_skill=/mnt/c/Users/HuailiShang/.codex/skills/evaluator-executor-workflow/scripts
python3 -X utf8 "$task/VERIFY_SCOPE.py" --phase start
python3 -X utf8 "$prior/evidence/evaluator/replay_session_conditions.py"
python3 -X utf8 "$task/VERIFY_TRANSFER.py" --baseline
python3 -X utf8 "$workflow_skill/run_validation.py" --repo . --plan "$task/VALIDATION_PLAN.yaml" --out "$task/evidence/executor/l2" --mode executor
python3 -X utf8 "$workflow_skill/validate_workflow.py" --repo . --current CURRENT.md
```

## 允许改动范围

- 修改 `shopping_decision/chat_bridge.py`，新增 `shopping_decision/confirmed_comparison.py` 及 `tests/test_chat_requirement_authority.py`。复用 `printer_conditions.py` 和现有比较器、规则门禁，无需修改其旧调用约定。
- 仅本包的 `REPORT.md`、`evidence/executor/` 及正常阶段更新 `CURRENT.md`。冻结检查、水壶样例、旧测试、旧交接、地图、通用门禁、Web 和桌面入口为保护件。

## 明确排除和授权

仅离线代码、合成验证与交付。联网、真实商品接线、平台接口、模型、账号、设备、外发、付费和交易无授权。Git 提交、推送及历史改写无授权。

## 停止条件

本包总上限 4 有效小时、1 轮集中修正，包含接替原 3 小时包的打印机补修和新增迁移验证。评估者独立复跑建议上限 1 小时。验证不符先保留原始失败，再在额度内集中修正。若须改共享门禁、交易边界或引入第二品类业务，停止该扩展并回报具体现象。通过后停止扩大合成验证，下一笔投入回到能改变打印机原案下一行动的真实证据。
