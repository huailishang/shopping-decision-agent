# 打印机聊天证据绑定独立复核

Task ID: PRINTER-CHAT-CONTEXT-20261124
Baseline HEAD: 4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf

## 评估前检查

项目已能用普通聊天收集需求、处理改答并交付待核研究。需要再证明真实证据能改变两款打印机的取舍。当前先卡在 B06，聊天发布前必须确保资料包无法代写用户已确认的条件。B01 的准确型号微信证据、河南应付价和真人收益仍待证。瓶颈排序沿用本轮入口，历史地图 r35 保留。

评估者核对报告列出的五份 SHA-256，匹配送审时的 `CURRENT.md`、聊天代码、新专项、两款对照和差分。切换评估状态前，结构校验与冻结范围检查退出 0。独立重跑在同一工作区的 WSL Python 3.12.3 完成。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124/evidence/evaluator/l3/L3-GATE.json
- Validation plan: handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124/VALIDATION_PLAN.yaml
- Mandatory failures: 0

冻结命令 12/12 退出 0。新增专项 7/7、原专项 10/10、全量 527/527。原河南家庭样本及两次改答通过。旧审计核实 17 份历史原件、6/10 次模型尝试、C05/C06/C07 缺测、合约模型输出为 0。范围检查核实 1554 份保护件、HEAD 和索引。

## 独立补测

用真实聊天提交入口建立「微信必须、河南收货、日本使用、1000 元上限」的会话。替换分析层返回的合成资料，渲染真实聊天结果。独立重放 [脚本](evidence/evaluator/replay_session_conditions.py) 退出 1，[原始输出](evidence/evaluator/session-conditions.stdout.json) 保留会话、输入、命题和用户结果。

| 变化 | 应得结果 | 实际结果 |
|---|---|---|
| 调换顺序，加入第二候选和无关人民币报价 | 合格功能和预算仍适用，第二候选的越区功能待核 | 通过 |
| 资料把微信条件值改成 false，事实也为 false，保持会话版本和用户确认值的哈希 | 微信硬条件仍待核或不满足 | 公开结果显示「该条件在研究层面满足」，候选标为可继续研究。按同一会话的原条件作对照时，该事实被判不满足 |
| 资料省略微信硬条件，保留 900 元报价 | 报价可独立显示，微信须待核且候选不能被标为已满足全部硬条件 | 用户只看见预算满足，候选标为可继续研究 |
| 用户明确只接受微信小程序，资料只给通用微信支持 | 具体小程序条件应待核 | 结果未提示小程序缺证，候选标为可继续研究。加上准确的小程序条件及匹配合成事实的正例保留 |

预算有专门的会话绑定，而微信行仍直接采用资料包给出的比较目标。会话哈希可验证资料包声称对应的是哪次会话，目前覆盖不到包内是否遗漏或改变了硬条件。三条失败均以正常聊天渲染观测，全部为离线数据；购买、交易和实时核价标志始终为 false。

## AC 逐条裁决

| 条件 | 裁定 | 独立依据 |
|---|---|---|
| AC-01 | 通过 | 收货与使用地区分别计算，调整顺序和候选的独立组通过。RV-EV-01、02、04及独立重放 |
| AC-02 | 通过 | 重复标识、悬空引用、畸形来源和数量上限按结构回退。RV-EV-01、04 |
| AC-03 | 通过 | 预算取用户当前值，金额、费用范围与报价时间延续原门禁。RV-EV-01、02、04、05 |
| AC-04 | 通过 | 普通后端保持原案微信硬要求，微信改可选与预算改 800 后文案随之变化。人工两款对照符合历史证据边界。RV-EV-03、06、07 |
| AC-05 | 不通过 | 冻结命令、旧账和交易标志均通过。独立补测证明条件冲突与缺证仍可产生错误的研究资格，负向保护未满足 |
| AC-06 | 通过 | 送审与独立回执、原案对照和范围检查均可定位。执行报告里的有效工时按墙钟记录，保留分项主动工时缺口。RV-EV-12 |

存量来源逐项比对了历史 `evidence/sources.json` 与两款对照。Brother 正向材料仅限官方索引，历史访问正文 403。HP 的 9YF97A 缩窄核价对象，系列安装指南和地区未选的旧 1199 元记录各自保留限制。本轮无新增外部取证，原网页全文和精确观测时刻的缺失继续保留。

## RV-EV-03

- AC: AC-04, AC-05
- Meta: handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124/evidence/evaluator/l3/RV-EV-03.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124/evidence/evaluator/l3/RV-EV-03.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124/evidence/evaluator/l3/RV-EV-03.stderr.log

## RV-EV-12

- AC: AC-06
- Meta: handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124/evidence/evaluator/l3/RV-EV-12.meta.json
- Stdout: handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124/evidence/evaluator/l3/RV-EV-12.stdout.log
- Stderr: handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124/evidence/evaluator/l3/RV-EV-12.stderr.log

## Final verdict

REJECTED

## 项目影响裁决

Impact verdict: NOT_APPLICABLE

本包修复了已知的资料结构、地区和报价交叉干扰。B06 缩小到聊天对确认条件的覆盖与含义，依然阻断接入真实商品结论。现有材料使 HP 核价对象更清楚。两款河南有效应付价、准确微信流程及复用、用户收益继续待证。

## 下一步

Continuation decision: CONTINUE

下一包 [PRINTER-CHAT-REQUIREMENT-AUTHORITY-20261124](../PRINTER-CHAT-REQUIREMENT-AUTHORITY-20261124/CONTRACT.md) 单方向交执行者。只修正常聊天的硬条件权威，合并反写、遗漏和具体路径降格三个同源问题。预算 3 有效小时、一次集中修正。已见的地区与价格回归全部继承。优先修它，因为当前普通后端暂无可发布的真实结构化商品包，新增取证也无法验证正确的用户匹配，且真实核价缺收货县区和预算口径。修复后的下一次投入优先评估准确型号微信材料能否改变原案下一行动，暂停加码合成机制和扩品类。
