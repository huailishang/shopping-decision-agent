# 接手与验证

环境用本机 WSL Ubuntu、Python 3.12、已安装的 PyYAML。以下命令从仓库根目录运行。工作树包含已评过的未提交代码，使用同一工作区，勿切回裸 HEAD。

```bash
task=handoffs/evaluator_executor/PRINTER-CHAT-CONTEXT-20261124
prior=handoffs/evaluator_executor/CHAT-PUBLIC-CLAIM-BINDING-20261123
workflow_skill=/mnt/c/Users/HuailiShang/.codex/skills/evaluator-executor-workflow/scripts

python3 -X utf8 "$task/VERIFY_SCOPE.py" --phase start
python3 -X utf8 "$prior/evidence/evaluator/replay_extra.py"
python3 -X utf8 "$prior/VERIFY_FROZEN_REPLAYS.py"
python3 -X utf8 "$task/VERIFY_ORIGINAL_CASE.py"

python3 -X utf8 "$workflow_skill/run_validation.py" --repo . \
  --plan "$task/VALIDATION_PLAN.yaml" --out "$task/evidence/executor/l2" --mode executor
python3 -X utf8 "$workflow_skill/validate_workflow.py" --repo . --current CURRENT.md
```

开始时保留上述四条前测命令的原始输出和退出码。预期依次为 0、1、0、0；第二条五个已知失败、两个干净对照及安全检查通过。修完后第二条预期为 0。VP-04 要核实际运行测试数量大于零并覆盖合同用例；VP-10 要保留 520 项且包含新增测试。只跑出全量总数相等或只找到测试文件不能代替核用例。L2 失败时，将该批回执和原始输出移出下次的输出位置再复跑。

报告保持 `EXECUTING / Executor`，写 `Executor status: SUBMITTED_FOR_REVIEW`，引用 L2 门禁和逐项 EV。类型为修复，写本地前后差异与真实结果边界。评估者验原件后切 `READY_FOR_REVIEW`，使用 `--mode evaluator` 和独立输出目录 `evidence/evaluator/l3`，补独立样本、核手工来源，然后签 `REVIEW.md`。回执生成器检验执行结果，最终判断归评估者。

评估准备的原案及补测前值在 [preparation](preparation/) 和 [上一包原始补测](../CHAT-PUBLIC-CLAIM-BINDING-20261123/evidence/evaluator/chat-extra.stdout.txt)。可以复用旧资料定位，留存记录不会刷新观察时间。
