# 聚焦引导公平对照（执行者）

冻结参考：replay-reference-v2.json（产品编辑前更正Brother缺证语义，v1原件保留）。B0来自 evaluator ZIP，B1仅含T18硬件预算口径共同修复，无新增来源；两臂相同资料、时点、资源和用户回答语义。各组来源和产品SHA见comparisons.json，实际请求/回执/回答、setup原件按组保存。

| 案例 | A完成 | B完成 | A回答 | B回答 | A无关 | B无关 | 结果 |
|---|---:|---:|---:|---:|---:|---:|---|
| T01 | True | True | 1 | 1 | 0 | 0 | tie |
| T02 | True | True | 1 | 1 | 0 | 0 | tie |
| T03 | False | True | 5 | 4 | 3 | 0 | improved |
| T04 | True | True | 1 | 1 | 0 | 0 | tie |
| T05 | True | True | 1 | 1 | 0 | 0 | tie |
| T06 | True | True | 1 | 1 | 0 | 0 | tie |
| T07 | False | True | 5 | 4 | 3 | 0 | improved |
| T08 | False | True | 5 | 4 | 3 | 0 | improved |
| T09 | False | True | 5 | 4 | 3 | 0 | improved |
| T10 | False | True | 4 | 1 | 4 | 0 | improved |
| T11 | False | True | 4 | 1 | 4 | 0 | improved |
| T12 | False | True | 4 | 1 | 4 | 0 | improved |
| T13 | True | True | 3 | 1 | 2 | 0 | improved |
| T14 | True | True | 3 | 1 | 2 | 0 | improved |
| T15 | True | True | 0 | 0 | 0 | 0 | tie |
| T16 | True | True | 5 | 5 | 2 | 2 | tie |
| T17 | True | True | 4 | 4 | 1 | 1 | tie |
| T18 | False | True | 3 | 1 | 3 | 0 | improved |
| T19 | False | True | 3 | 1 | 3 | 0 | improved |
| T20 | False | True | 4 | 1 | 4 | 0 | improved |
| T21 | False | True | 4 | 1 | 4 | 0 | improved |
| T22 | False | True | 4 | 1 | 4 | 0 | improved |
| T23 | True | True | 3 | 3 | 2 | 2 | tie |
| T24 | True | True | 1 | 1 | 0 | 0 | tie |

合计：旧版12/24、新版24/24；改善14、持平10、退化0。74→44次回答，51→5次与冻结任务目标无关回答。重复及完整指南展开均0。复杂setup的工作单操作不混入答复次数。T16/T17/T23仍有无关问题；不能将全部研究任务简化为一次提问。

收益分账：来源新增0；共同修复T18仅硬件口径可被真实入口读回（不计为聚焦收益）；上表A/B是同B1基线下的聚焦组织差异。安全授权三项恒false的机械检查由summary.json重算。无真人、真实模型、实时报价、交易或专业全面性验证。独立评估者另8留出不混分母。
