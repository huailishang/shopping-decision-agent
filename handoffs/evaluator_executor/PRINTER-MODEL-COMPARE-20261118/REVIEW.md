# PRINTER-MODEL-COMPARE-20261118｜评估者独立复核（2026-11-19）

- 角色：Evaluator
- 任务裁定：**FAIL / BLOCKED（不得签集成通过）**
- 项目能力影响：离线通用比较/规则路径已实现并能通过回归；真实模型比较增益 **UNKNOWN / NOT ESTABLISHED**。
- 依据：CONTRACT.md、VALIDATION_PLAN.yaml、cases.json、原始live账、paired.json、provider_discovery.json、L2-GATE.json和本轮独立命令；不调用新模型、不改旧回执。
- 基线：HEAD `ce34764ab7d803b06abbdbcea0afe32048096c0a`；工作树此前有大量未提交内容，均未清理、提交或推送。

## 独立检查

| 冻结项 | 评估者复跑（2026-11-19，本地WSL `python3 -X utf8`） | 结论 |
| --- | --- | --- |
| VP-01 `python3 -X utf8 -m unittest discover -s tests -p test_model_comparison.py -q` | Ran 13 tests；OK；退出0 | PASS（仅专项逻辑） |
| VP-02 `python3 -X utf8 scripts/run_model_comparison_experiment.py --audit --task handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118` | `model cases not attempted: C05,C06,C07`；退出1 | FAIL（强制项） |
| VP-03 `python3 -X utf8 -m unittest discover -s tests -q` | Ran 477 tests；OK；退出0 | PASS（工程回归） |

使用 `python3` 是因为此次WSL环境 `python` 不在PATH（第一次尝试退出127），并非跳过检查或转换测试标准。历史执行者L2记录亦为 VP-01 PASS / VP-02 FAIL / VP-03 PASS。

## 事实、缺口及不能越界的判断

1. 八个冻结用例C01—C08中，真实调用账本共6次、涉及C01/C02/C03/C04/C08五个用例；C05/C06/C07未尝试。C01已经尝试2次，C08尝试1次。总额10次，历史6次已消耗、剩余最多4次，不能清零或跨合同伪造新预算。
2. `paired.json` 的 `accepted={}`、`actual_inference_completed_count=0`（provider_discovery记录）、`comparison_quality_gain=not_determined_by_automated_checks`。C01/C08必须各至少有一次合约输出，现两者都不满足；由于C01已达到每用例2次上限，**在原冻结合同下即使继续消耗剩余4次也不能达标**。
3. 账号/运行时问题真实存在：历史Codex CLI回执对 `gpt-5.5`、`gpt-5.4-mini`、`gpt-5.3-codex`给出 `model_not_found/unsupported with a ChatGPT account`。本机枚举到的模型名称并不证明当前账号可用。不得推断其他型号可用或零成本。
4. **纠正一个误判**：`C01-01` 的旧 `meta.json`把 `item.completed: error` 记为1个“tool event”，实际 `stdout.events.jsonl`仅见技能预算报错、模型不支持及 `turn.failed`，没有证据表明模型调用了外部工具。需要区分“错误事件误分类”和“真正工具调用”；保留旧meta，不篡改历史。
5. `C04-01`中断且原始回执缺失；应按一次尝试计费/计额度，不能补写成功或自动忽略。
6. 审计脚本在当前原件上先因三个未尝试用例失败；补齐后仍将检查真实完成、工具权限、C01/C08合约输出等。本轮不把单测假响应、离线规则比较或完整度得分当成真实模型集成或认知收益。
7. 执行者指定的 `REPORT.md`缺失，故正式交付亦未收口。历史旧包/冻结输入须保留。
8. B01继续未消除：两准确型号的微信后续打印事实、平台销售身份、河南有效价格与真实使用反馈仍不足；B05的本次程序实验无法替代B01证据，更不能推导已可购买。

## 裁定与停止条件

- AC-01局部工程验证成立；AC-02/AC-03的真实模型与公平实测不成立；AC-04综合必选门禁未通过。**整体 NOT PASS**。
- 原包保留所有调用记录，不在旧合同下追加盲目模型请求，不改变 `CONTRACT.md`、`VALIDATION_PLAN.yaml`、`cases.json` 和旧live证据。
- 下一步只发一个小的 **PRINTER-MODEL-ADAPTER-REPAIR-20261119** 解阻包：先做账号支持性与事件分类的无推理预检、补报告、健全错误保护及离线验证。不得把原包“强行修到PASS”，不得擅自重置10次历史预算。
- 新包不授权API推理、外部商品采集、账号文件读取、付费、购买或Git提交/推送。若预检仍不能证实可用模型，明示外部阻塞，并建议下一评估回到B01少量高价值事实核验，而非再扩代码/GUI。
- 未来若负责人授权新的真实模型比较，应另定 **独立、可审计、不挪旧额** 的范围与次数，以及新的公平基线和验收目标；不得修改本次历史分母/失败原件。

下一包：`handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118/post_review/PRINTER-MODEL-ADAPTER-REPAIR-20261119/CONTRACT.md`。
