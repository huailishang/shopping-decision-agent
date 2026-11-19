# 执行者从这里开始

先读CURRENT.md、本目录CONTRACT.md、DELIVERY_FORMAT.md。本包只交下一执行者；定稿轮未开始外部研究，没有REPORT或任务通过结论。保留全部未提交改动。

在项目根目录运行（PowerShell；均只读）：

```powershell
python -X utf8 handoffs/evaluator_executor/PRINTER-WECHAT-DECISION-FACT-20261117/check_package.py --check frozen
python -X utf8 handoffs/evaluator_executor/PRINTER-WECHAT-DECISION-FACT-20261117/check_package.py --check replay
```

成功后切CURRENT至EXECUTING（执行中）/Executor（执行者），立即记工作起点。按合同完成≤4条公开查询/≤6次官方读取、两款比较、反馈缺失和报告。本包不改产品/注册表；受限就交未知和真实断点，不自行扩型号或登录。

交付齐全后跑本地门禁。每次重跑前将已有EV、L2/L3及其他失败输出完整复制到evidence/batches/下唯一新目录，禁止覆盖失败原件：

```powershell
python -X utf8 C:/Users/HuailiShang/.codex/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan handoffs/evaluator_executor/PRINTER-WECHAT-DECISION-FACT-20261117/VALIDATION_PLAN.yaml --out handoffs/evaluator_executor/PRINTER-WECHAT-DECISION-FACT-20261117/evidence --mode executor
python -X utf8 C:/Users/HuailiShang/.codex/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

REPORT索引三个EV并标实际L2结果，未过不能提交待审。执行者提交仍保持EXECUTING；评估者接收快照后才切READY_FOR_REVIEW（待独立评审），复跑同计划`--mode evaluator`并完成逐源判读，不重复联网。不得宣称真人反馈、实机成功、当前有效价或购买批准。
