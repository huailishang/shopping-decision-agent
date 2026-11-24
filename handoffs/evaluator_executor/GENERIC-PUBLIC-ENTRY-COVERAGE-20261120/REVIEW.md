# R1 独立评估｜须续修

2026-11-23 · Evaluator · 任务 `GENERIC-PUBLIC-ENTRY-COVERAGE-20261120` · 已评审 HEAD `4a2f3c5e79f47299d4e944b3bdafbf3b13767fcf`。

**裁定 `NEEDS_REPAIR / NOT PASS`。** R1 恢复了待核研究提示，旧自由文本隔离在实测案例中成立。全量测试仍报错，独立反例另证实结构化结论可以依据冲突预算、过期报价或不匹配的收货地区显示“条件满足”。只修审计白名单不足以结案。

## 冻结命令复跑

在 WSL Ubuntu、Python 3.12.3 下按冻结命令独立执行，保留原始输出。[命令与退出码](evidence/evaluator-r1/wsl/exit_codes.json)

| 检查 | 实测 | 退出码 |
| --- | --- | --- |
| R1-VP-01 最小研究流 | [21/21](evidence/evaluator-r1/wsl/R1-VP-01.txt) | 0 |
| R1-VP-02 打印机决策路径 | [9/9](evidence/evaluator-r1/wsl/R1-VP-02.txt) | 0 |
| R1-VP-03 聊天发布专项 | [8/9，1 项报错](evidence/evaluator-r1/wsl/R1-VP-03.txt) | 1 |
| R1-VP-04 通用门禁专项 | [12/12](evidence/evaluator-r1/wsl/R1-VP-04.txt) | 0 |
| R1-VP-05 全量 | [505/506，1 项报错](evidence/evaluator-r1/wsl/R1-VP-05.txt) | 1 |
| R1-VP-06 历史只读审计 | [拒绝 `tests/test_minimal_research_flow.py` 的变化](evidence/evaluator-r1/wsl/R1-VP-06.txt) | 1 |

原生 Windows 的首轮使用可用的 `python` 启动器。全量额外出现 3 项子进程输出编码错误，涉及门禁演示、京东与淘宝离线 CLI。上表采用 WSL 按原命令复跑的结果，原生 Windows 输出另存。[Windows 命令与退出码](evidence/evaluator-r1/exit_codes.json) · [Windows 全量输出](evidence/evaluator-r1/R1-VP-05.txt)

## 聊天入口和条件冲突

用 `render_chat` 重放正常会话。2／1／0 条待核记录有对应提示，微信须用、可选和撤回有不同待办，预算由 1000 改成 800 后显示新值，换品类后清除打印机研究提示。旧促单话术留在审计，合法合成比较仍可显示命题 ID。两份旧测试相对基线只改了合同允许的两个方法，研究计数、改答和决策路径断言均保留。[独立重放](evidence/evaluator-r1/chat-replays.json)

用同一个入口模拟后端提供结构化数据，实际得到三处阻断。当前正常后端未提供这样的资料包，以下是接入结构化数据后的可复现发布缺口。

| 输入 | 实际展示 | 定位 |
| --- | --- | --- |
| 用户上限 1000 元、事实 1300 元，资料包同一维度额外放入 1500 元上限 | 同时显示 `1300 ≤ 1000` 未满足和 `1300 ≤ 1500` 满足 | [聊天检查](../../../shopping_decision/chat_bridge.py#L263)只要求至少存在一条等于确认预算的比较 |
| 合成报价 11 月 19 日到期，显示日 11 月 23 日，资料包自报 `as_of=11-18` | 显示 `900 ≤ 1000` 满足；仅将同一包的日期改成 11 月 23 日则回到待核 | [时效计算](../../../shopping_decision/evidence_comparison.py#L79)以包内日期为基准，聊天没有当前时效检查 |
| 会话确认河南收货、中国大陆使用，合成报价只标中国大陆 | 显示 `900 ≤ 1000` 满足 | [聊天检查](../../../shopping_decision/chat_bridge.py#L263)核对使用地；报价未与收货地绑定 |

重放时读取 [会话和资料包夹具](evidence/evaluator-r1/chat-fixtures.json)，以 `patch("shopping_decision.chat_bridge._analysis", return_value=case["analysis"])` 替代后端，再调用 `render_chat(case["state"])`；查看 `result_text` 和 `report_json.public_decision.claims`。价格、型号和引证均为离线夹具。购买批准、交易和实时价格已核标志全为 false。

## 审计与续修裁定

历史清单 1229 个路径中，仅聊天模块和两份经 R1 授权的旧测试有差异，其余 1226 个路径的字节哈希一致。仅在内存临时放行这三条路径的诊断核验了 17 份固定保护件，账本为 6/10、C05/C06/C07 缺测、合约成功输出 0，且篡改样本被拒绝。正式审计仍退出 1，历史拒绝裁定保留。[审计诊断](evidence/evaluator-r1/history-diagnostic.json)

给新只读审计脚本增加两份测试的例外有据可依。固定为本次审核通过的测试字节并要求文件存在，可以避免把未来任意改写或删除也当作已授权。本次复核开始时 HEAD 已是同步提交，其中合并了已知前序改动及本包交付，因此不能从 Git 差分单独还原每轮操作或历史推送授权。本轮未做 Git 提交或推送，冻结地图、保护件及旧桌面／Web 出口均未修改。

R1 可用性与两份旧测试迁移认可。安全、强制回归和正式历史审计仍阻断验收。下一责任 Executor 读取 [R2 续修授权和验收条件](AMENDMENT_R2.md)，使用同任务剩余预算修复上述缺口。真实报价、准确型号微信复用和用户选购收益仍待实证。
