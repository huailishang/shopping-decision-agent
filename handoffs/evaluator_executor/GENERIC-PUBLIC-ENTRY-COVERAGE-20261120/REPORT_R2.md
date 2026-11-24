# GENERIC-PUBLIC-ENTRY-COVERAGE-20261120｜R2 执行者交付

日期：2026-11-23。角色：Executor。授权：项目负责人在当前会话要求直接修复；仍执行零公网/零模型/零交易/零 Git 提交与推送约束。

**结论：R2 本地修复完成，原 R1 六项冻结命令均退出 0，已可交 Evaluator 独立复核；不自行签项目最终 PASS。**

## 修复内容与边界

1. `shopping_decision/chat_bridge.py`：当前已确认的用户预算为唯一权威上限。同一预算比较维度只要同时出现不同限额（如 1000 和 1500），整个结构化结论安全降为待核；不再拿 1500 元结果对外显示「满足」。有效单预算正例与实际超预算的「不满足」都保留。
2. 对 `live_quote` 价格证据，用**聊天进程本地当前日期**覆盖资料包自述的 `as_of` 进行结构化计算。11-19 到期、11-23 展示而包内日期仍为 11-18 的报价不能认定有效；未过期、结构合规的合成报价仍可条件比较。既有历史资料、模型回执未改。
3. 将**收货地区**和**设备使用地区**分开核验。有报价时需明确用户已确认的收货地、包地区及报价来源 `quote_region` 一致；缺收货地或不一致，则只在传给通用规则门禁的副本中撤销报价来源，产生有 ID 的 `unknown`（或安全待核），原始研究数据继续保存在 `report_json`。未改历史 `claim_gate.py` 语义。
4. `scripts/audit_model_history_readonly.py`：沿用 `chat_bridge.py` 旧例外，仅为 `tests/test_minimal_research_flow.py`、`tests/test_printer_decision_plan.py` 增加**已审核字节的固定 SHA-256**准入；每次审计要求两文件存在并逐字节匹配。不改变冻结清单/17 份保护件/模型事件账本，不全面关闭 drift 检测。
5. `tests/test_publication_entry.py` 增补四项真实 `render_chat`/历史审计负例：双预算、过期报价、收货地冲突/匹配正例、已审测试文件哈希变化/缺失。保留以前全部测试。

## 冻结计划实际执行（WSL Ubuntu / Python 3.12.3）

日志：`handoffs/evaluator_executor/GENERIC-PUBLIC-ENTRY-COVERAGE-20261120/evidence/r2/`。

| 检查 | 实际结果 | 退出码 | 原始日志 |
| --- | --- | --- | --- |
| R1-VP-01 最小研究流 | 21/21 PASS | 0 | `R1-VP-01.log` |
| R1-VP-02 决策路径 | 9/9 PASS | 0 | `R1-VP-02.log` |
| R1-VP-03 聊天发布 | 13/13 PASS | 0 | `R1-VP-03.log` |
| R1-VP-04 通用结论门禁 | 12/12 PASS | 0 | `R1-VP-04.log` |
| R1-VP-05 全量 `unittest discover -s tests -q` | 510/510 PASS | 0 | `R1-VP-05.log` |
| R1-VP-06 历史只读审计 | 正常核验通过，旧实验仍不完整 | 0 | `R1-VP-06.log` |

原评估者 `evidence/evaluator-r1/chat-fixtures.json` 的四组冻结重放也已用正常 `render_chat` 重新运行，输出见 `evidence/r2/evaluator_fixture_replay.json`：
- 合成合法正例：`met`（保留命题）。
- 冲突双预算：没有公开已验 claim，按待核降级。
- 资料包旧日期掩盖已到期报价：`unknown`。
- 全国报价与已确认河南收货地不符：`unknown`。
- 四组均无「1300 ≤ 1500」「立刻下单」「已验证河南现价」等高风险话术，`purchase_recommendation_approved=false`、`transactions_enabled=false`、`live_price_verified=false`。

审计回执：原清单 **1229** 个路径，允许当前源码变化仅为聊天模块及两份固定 SHA 测试；受保护 **17** 份哈希有效；原模型尝试 **6/10**、`C05/C06/C07` 未尝试、成功合约模型输出 **0**、旧包正式 `REJECTED` 保持。这是旧账完整性通过，不是模型实验成功。

## 待独立验收和不应扩大的结论

- R2-01 至 R2-04 的程序修复及冻结命令全部由 Executor 本地实跑；R2-05 含 Evaluator 的独立主入口、审计范围复核，**尚未由评估者独立签收**。
- 只有受控离线结构化输入；不代表河南当前真实到手价、准确在售 SKU、微信实机二次复用或真实用户受益已获证实。B01 继续未闭环，旧桌面/Web 出口不在本包修复范围。
- 评估者本轮新建的 `REVIEW.md`、`AMENDMENT_R2.md` 及 `evidence/evaluator-r1/` 保持原样。本次代码变更仅 `chat_bridge.py`、`test_publication_entry.py`、`audit_model_history_readonly.py`；另新增本报告、`evidence/r2/` 并调整 `CURRENT.md` 的执行路由。
- 未进行网络/模型/业务 API/账号/订单/付款/Git 提交推送，历史额度未重置。原任务累计有效小时缺乏可核对的完整时间账，因此不宣称已证实满足原 5 小时上限；本次为一轮集中修复与必要复验，不虚构剩余额度。

### 大白话

老的「已批准修改测试，却被审计误判违规」已经修好，并且仍按文件原样锁死，不是粗暴放开检查。评估者新发现的三个会误导选购的问题也一并堵住：预算不偷换、旧价不当现价、全国价不冒充河南价。510 项测试全绿，但这还只是执行者本地通过；评估者要独立复核后才算正式验收。真实商品采购证据仍需后续补齐。
