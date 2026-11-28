# 本地复现

在仓库根目录：`env PYTHONPATH=.:tests python3 -X utf8 handoffs/evaluator_executor/PRINTER-SCENE-ROBUSTNESS-20261127/VERIFY_SCENARIOS.py --role executor`。`VERIFY_PACKET.py controls` 核验已落盘重放；`VERIFY_NATIVE.py --role executor` 使用现有 Windows Python/JDK。冻结计划其余命令见 VALIDATION_PLAN.yaml。非最终交付，勿当作L2通过。
