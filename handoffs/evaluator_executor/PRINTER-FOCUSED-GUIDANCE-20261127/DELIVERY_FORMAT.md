# 可复核交付

REPORT.md使用标准Executor Report结构：Task ID/Executor status/Baseline HEAD；Workspace snapshot；Changed files；L2 Task Gate；按EV编号引用meta/stdout/stderr并映射全部AC；Impact comparison；Iteration ledger；Deviations and unresolved items。SUBMITTED_FOR_REVIEW只在标准L2 PASS时可用，未过BLOCKED。不改旧REPORT格式来覆盖旧缺口。

COMPARISON.md：B0/B1/两臂源码和来源SHA、三种收益分账、24配对逐案结果、失败/持平/退化、完整回答/无效答复/重复/额外阅读计数和原件；不要只给均分。声明全部是离线合成重放，未测学习、满意度、真实模型或交易。

USAGE.md：现有Windows启动与普通聊天；从粗用途看短解释、展开全文、点参考只填草稿、本人提交/暂缓/撤回、改要求、来源失效、保存/新进程恢复、说明预览另存/取消。给负责人一条可复制启动命令和一个最小示例，避免实现术语进入主屏。

evidence/executor必须有：active-sessions.jsonl、operations.jsonl、process.json、source-audit.json、replay-reference-v1.json、challenge-results.json、comparisons.json、journeys.json、summary.json、generate_summary.py、B1-shared-baseline.json、全部原始桥接与窗口证据。summary含所有上游原件和生成器SHA；汇总脚本由原件重算，不硬编码绿表。process字段至少：known_active_seconds、unknown_segments、unknown_upper_bound_seconds、budget_debit_seconds、repair_rounds、inherited_prior_unknown=true、forbidden_operations（各项0）、source_reads/query计数。

comparisons每对case_id、a/b原件路径及SHA、同源baseline/reference/time/limits、outcome、边界；challenge-results至少CH01—04，各含实际输入/响应原件SHA、预期失败以及检查器如何检出。journeys含F01—12、core、completed、route、before/after、raw_artifacts；原生来源可按文件定位每条链，不能重复引用一张截图当10条完成。

所有本机artifact路径仓根相对且不可逃逸；每条raw_artifacts格式为path/sha256。只用合成个人输入，真实私有文件不入证据和Git。存在缺件照实列。最终完整runner：
```text
python3 /mnt/c/Users/HuailiShang/.codex/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan handoffs/evaluator_executor/PRINTER-FOCUSED-GUIDANCE-20261127/VALIDATION_PLAN.yaml --out handoffs/evaluator_executor/PRINTER-FOCUSED-GUIDANCE-20261127/evidence/executor/l2-final --mode executor
```
WSL仓根运行，原生Java自动转已有WindowsPython。之后标准validate_workflow；结构OK只是可交接，不是独立通过。保留最后断点/下一命令与剩余额度。
