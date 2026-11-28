# 单一入口

先CURRENT，再CONTRACT/SCENARIOS/VALIDATION_PLAN。旧包REVIEW与recheck-20261127是纠偏依据，拒绝及原始失败不改。本轮Evaluator只完成复查和冻结，产品修复尚未执行。

首个工具调用先捕获系统时间，读取CURRENT后同期写本包activity.jsonl的start；首次读漏记就明确未知，不以自报分钟补上界。所有工作和机器等待分账，12小时/2轮是上限。

执行python3 -X utf8 本包/VERIFY_PACKET.py scope，预期通过；再执行env PYTHONPATH=. python3 -X utf8 本包/VERIFY_SCENARIOS.py --role executor，预期存在待修失败。保留前测，再改允许产品文件。SCENARIOS独立固定；H07已披露不再算新盲测。只改规则不足以交付，须完成原24真实重放和三完整链、窗口变体、统一最后L2，不逐小修重复全量。

CONTROL_REPLAY.json格式见VERIFY_PACKET注释：每案case_id、events、terminal_view_artifact，事件含request/response_artifact和answer字段；原24目标使用前包冻结replay-reference-v2，所有文件原始stdin/stdout保留。窗口新专项由本包原生验证器自动编译并运行，新增文件存在才允许通过。

旧PYTHONPATH缺口仅在新计划明示解决，旧VP-03及旧工时失败不重跑追认。无真实模型/平台/外部研究/Git索引操作。全部门禁通过后按标准逐AC报告交Evaluator独立复核，另8留出单独计算。
