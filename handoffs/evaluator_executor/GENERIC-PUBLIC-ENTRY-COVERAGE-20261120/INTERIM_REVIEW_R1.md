# GENERIC-PUBLIC-ENTRY-COVERAGE-20261120｜评估者独立复核与续修裁定（R1）
日期：2026-11-20；角色：Evaluator；本文件为**受阻节点的中期评估**，不是最终 L3 PASS/结案 REVIEW。

## 项目位置与审查边界
项目目标：用户需求→有来源的商品证据→确定性比较→可信可读结论→反馈→购买前复核。
已有可复用需求对话、有限研究资料、规则比较和 claim_gate；目前核心 B06 是「正常用户出口不得绕过证据—结论门禁」，竞争瓶颈 B01 是准确在售SKU、微信二次复用、河南实时到手价/用户实用收益证据不足。
冻结地图 docs/PROJECT_BOTTLENECK_MAP.md r35 是历史基线，本评估不修改，B06 的后续裁定见 CURRENT 与本记录。

## 独立复查到的事实
- 检查本包 CONTRACT.md、VALIDATION_PLAN.yaml、REPORT.md、evidence/validation_summary.json，以及 tests/test_minimal_research_flow.py:105-120、tests/test_printer_decision_plan.py:97-109、shopping_decision/chat_bridge.py:262-359、tests/test_publication_entry.py。
- 独立在本地仓库运行：`python3 -X utf8 -m unittest discover -s tests -q`；**退出码 1，Ran 504 tests，failures=2**（执行输出显示执行用时 57.221s）。
- 失败精确落点：`test_chat_selected_pack_switch_and_answer` 第117行要求未核实的 `research_case.report_text` 原样包含在 `result_text`；`test_chat_result_contains_same_plan` 第107行要求 `decision_plan.text` 原样包含在 `result_text`。
- 实际 `result_text` 为统一「待核研究」「补齐可追溯事实」的降级文本；旧研究正文未直通。因此不能恢复两条旧断言对应的危险行为。执行者声称的 7/7、12/12、历史只读审计通过，此处为交付记录，**不冒充本次独立逐项重跑 L3**。
- **另一真实副作用**：即使存在本地2/1/0条有限研究记录，主聊天当前输出也几乎相同的笼统待核说明；用户看不到研究进度、已答「微信必须/可选」带来的下一研究行动分叉。不能只删除断言、不补等价可用性覆盖。

## 本轮结论与影响
- **验收结论：NEEDS_REPAIR / NOT PASS**。冻结 AC-05 要求全量退出0，现不成立；不得据局部正例直接签主入口闭环。
- **影响判断：B06的恶意自由文本直通风险局部缩小**（代码和现有专项支持），但用户有用研究引导出现回退；B01真实购买证据与用户收益未前移，历史模型实验6/10、C05/C06/C07缺测仍未通过，不追认历史 REJECTED。
- 范围判断：两项旧断言与新冻结安全规则不相容，允许**限定迁移**而非移除测试；必须保留研究输入2/1/0、已确认条件改答、研究路径随需求变化等原语义，新增负向门禁断言。
- 迭代选择：**CONTINUE_IN_SAME_TASK_WITH_EXPLICIT_R1_AMENDMENT**。问题可定位、修改窄、范围属原聊天发布同一假设；不创建第二个平行任务，也不重置历史预算。续修前必须冻结新增测试白名单与验证计划。
- 实施约束：不改父包、历史原件、模型尝试账、r35地图；不启用模型/外部网页/业务API/购买/交易；不commit/push。

## R1通过/失败决策
下一责任 Executor。只读 `AMENDMENT_R1.md` 和 `VALIDATION_PLAN.R1.yaml` 后进行一轮有界续修：
1. 用经界定的用户条件和结构化进度/有限枚举生成**未核研究提示**，与 claim_gate 的已验商品结论分栏，不直通任意旧文本；
2. 将两条测试迁移为“保留研究审计与需求改答语义＋原文不得越过门禁＋研究进度/下一步可解释”，增加恶意文字负例；
3. 独立全量应 exit 0，专项及历史审计不能回退。否则照实保持 NOT PASS。

### 大白话总结
现在聊天比以前安全，乱写的“立刻购买”不能直接展示，但研究到了哪一步也被挡住了。全量504条有2条旧测试不符合新规则。我不批准放回未经验证的推荐；让执行者把研究进度和下一步用安全模板显示出来，同时改好这2条旧测试，再完整复测。