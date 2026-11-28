# Executor 执行报告｜PRINTER-SESSION-COST-EVIDENCE-20261126

Task ID: PRINTER-SESSION-COST-EVIDENCE-20261126

Baseline HEAD: c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f

Executor status: SUBMITTED_FOR_REVIEW

执行日期：2026-11-26（Asia/Shanghai）。本报告仅提交执行证据，整体裁定由 Evaluator 独立完成。

## 结果与验收项

| AC | 执行者结果 | 可定位证据与限制 |
|---|---|---|
| AC-01 | 工程通过，待独立业务复核 | decision_actions.apply_session_policy → confirmed_comparison → cognition_comparison / chat_bridge → public decision / rank_actions；明确 confirmed/unanswered/deferred/withdrawn、当前版本与确认值摘要。原案两入口未答先问扫描、暂缓先问双面、两项无需先查微信；彩印硬失败无候选复活。VP-01、专项7案、paired-observations-v1.json。全局澄清 candidate_id 仅为展示锚点，不是候选特有缺证。 |
| AC-02 | 工程通过，待独立复算 | lifecycle_cost 保留用量、周期、币种、费用范围、版本、假设谱系；同口径才能比较，不同比较任务返回不可比或拒绝。零/恰好耗尽/超一页、布尔/非有限/未知及既有硒鼓测试通过。旧无期间币种 helper 仅保留显式标记 legacy_unscoped_fixture 的兼容；正常业务入口拒绝缺口径。 |
| AC-03 | 工程通过，合成实际入口验证 | cost_scenario.evaluate_scenario / bind_cost 经 render_chat 两入口消费；原家庭受控硬条件满足时仅改兄弟随箱量，700→600，惠普650不变，优先方向翻转；真实硬缺证同变量不选赢家；0页 vs 1800页不可比；撤回维护来源、来源同ID新版本使依赖成本未知，预算改答使情景陈旧。全部合成价格，不是实时报价。成本入口是显式 Python 参数，未新增前端交互表单。 |
| AC-04 | 工程通过，离线回执 | model_adapter.normalize 拒绝未请求工具/函数、refusal、错误角色、多消息、异常类型；保留原字节及文本摘要，限制大小、列表并处理深层JSON。action_ranking 已有决策摘要校验与同级约束消费会话/成本绑定；两个聊天入口合法建议接受，工具混合与陈旧建议回原首项。VP-01、VP-02、VP-03、6组回放；未调用模型API/CLI。 |
| AC-05 | 执行者复证限范围，独立裁定待办 | HP c07148381.pdf 印刷62页（PDF零基67）维护文字，139页（零基144）型号表视觉映射；旧定位原样保留。必要摘录、事实绑定、哈希与版本见 hp-maintenance-snapshot.json；文档完整字节未获取，维护页截图两次失败（文字非表格），型号表截图视觉核验成功但未本地保存图像。9次读取逐操作结果已记录，精确起止未实时保留，记录时间窗不冒充逐次时点。不能证明实际寿命、费用、故障率、产量或整机保修。 |
| AC-06 | 离线功能对照完成，独立人审待办 | 26组配对、19组实际 render_chat；按状态/成本/来源/协议的不同干预计数，不把同一状态三种origin重复计数。用户正文默认路径去除命题哈希，审计保留；仍有较长的分维度证据与后端兼容审计文字，未证明真实用户满意或收益。见 COMPARISON.md。 |
| AC-07 | 机器7/7 | VP-01至07实际退出0；旧581+新增30=611，全部通过；历史审计原模型实验仍未完成（accepted_model_outputs=0），不是重新追认。2230保护文件未变化，HEAD和索引不变。 |
| AC-08 | 当前摘要可复算；过程账有限 | 由 generate_pairs.py 从当前运行原件生成 paired-summary-v1.json（含原件/生成器SHA及字节数）。旧包摘要不覆盖。本轮操作明细、首次失败、最终退出码及日志在 evidence/executor。精确逐操作时点与有效主动工时缺失，不能补造；执行起止墙钟约14:22–14:43，低于首个4小时检查点与72小时上限。 |

## 冻结计划最终执行（修完来源版本绑定后）

| 命令 | 实际退出码 | 记录 |
|---|---:|---|
| VP-01 VERIFY_BUSINESS | 0 | 18项，0失败 |
| VP-02 VERIFY_DELIVERY | 0 | 五组发现7+7+5+5+6=30项，全部通过 |
| VP-03 上一包 VERIFY_BUSINESS | 0 | VP-03.log |
| VP-04 原 REPLAY_CASES | 0 | VP-04.log |
| VP-05 全量 unittest discover | 0 | 611项，48.561秒，OK |
| VP-06 历史模型账只读审计 | 0 | 历史回执完整、实验仍未完成 |
| VP-07 VERIFY_SCOPE post | 0 | 2230保护件、HEAD/索引/manifest均一致 |

完整原始输出见 evidence/executor/VP-01.log 至 VP-07.log、final-exit-codes.txt。开工 start 检查通过；实际前测 exit1、5项反例失败见 pre-repair-business.json。第一次集中修复会话/口径/回执后冻结反例全过、旧581全过；第二阶段完成成本/证据/配对与29项专项，初轮全量610过；第三阶段来源版本绑定首次专项失败7项（集合与dict比较错误），保留 version-binding-specialized.log，集中修复后30项过，最终611/611。未更改冻结检查器或历史断言；第一版七项输出保存在 pre-version-binding-gate。未另起包重置额度。

## 权限及剩余

匿名查询0，公共资料读取9/14（评估者独立6次完整预留），详见 source-operations.json；新增模型API、模型CLI、真实平台业务API、账号操作、设备操作、交易、安装、Git commit/push均0；旧包、冻结基线及原型未修改。源核验只使用公开缓存文字和型号表，未下载完整PDF。没有新真实模型、实际成交价、实际耗材成本、真人收益证据。独立评估应复算来源指纹变更、交叉入口未参与组合、原案条件和用户正文、核源及过程时点限制。工程通过不等同整体业务PASS。交接下一角色 Evaluator。


## 工作区快照
HEAD/索引/基线保持一致，2230保护件无变化。产品改动清单见 native-l2/EV-07.stdout.log；无提交/推送。

## 改动文件
8个产品代码文件、1份知识包、5个新增测试组；以最终范围报告的逐文件清单为准。未改变旧断言。

## 影响对比
- 测量证据：pre-repair-business.json、VP-01.log、native-l2/L2-GATE.json、paired-summary-v1.json。
- 修改前：冻结18项中5项失败；原581项全量。
- 修改后：冻结18项全过；611项全量通过；26组对照。
- 变化量：冻结失败减少5，测试新增30，19组真实聊天代码回放；不是模型或真人效果测量。
- 护栏结果：无交易、无模型调用、无平台API、无提交推送；2230保护文件不变。
- 范围限制：合成成本、离线建议；外部来源原PDF完整字节及精确逐操作时点缺失，独立业务验收未裁定。

## 偏差与未解决项
另行调用工作流路由校验器发现冻结合同缺标准标题及校验计划引用等格式字段；不在执行者可修改范围内，原合同未改。任务冻结的7命令和标准 L2 原生运行器均实际通过；路由文档格式问题交评估者处理。来源原件/过程账与真实购买效用限制见 AC-05/06/08。

## L2 Task Gate
- Gate result: PASS
- Gate summary: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/L2-GATE.json
- Validation plan: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/VALIDATION_PLAN.yaml

## EV-01
- AC: AC-01, AC-02, AC-04
- Meta: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-01.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-01.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-01.stderr.log

## EV-02
- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06
- Meta: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-02.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-02.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-02.stderr.log

## EV-03
- AC: AC-01, AC-04, AC-07
- Meta: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-03.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-03.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-03.stderr.log

## EV-04
- AC: AC-01, AC-03, AC-06
- Meta: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-04.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-04.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-04.stderr.log

## EV-05
- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-07
- Meta: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-05.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-05.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-05.stderr.log

## EV-06
- AC: AC-07
- Meta: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-06.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-06.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-06.stderr.log

## EV-07
- AC: AC-07, AC-08
- Meta: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-07.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-07.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/executor/native-l2/EV-07.stderr.log
