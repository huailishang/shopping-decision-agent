# 下一执行包：每次讲清一个会改变决定的问题

任务：PRINTER-FOCUSED-GUIDANCE-20261127。已冻结；交Executor连续执行。先读CURRENT→本入口→CONTRACT→INTERFACE→MEASUREMENT→EVALUATION→VALIDATION_PLAN→BUDGET→DELIVERY_FORMAT→r44地图。旧包REVIEW是纠偏依据，旧失败账不重写。

目标：现有打印机聊天/Windows窗口从粗需求开始，每次给出一个与当前决定有关、能说明理由的问题；本人提交/暂缓/撤回后重算，沿同一主链进入路线或适用候选比较。完整资料仍可按需展开。只加文案、不改变问题选择及后续判断，不能算完成。

**长包上限240有效小时、8轮集中纠错、12阶段连续推进；充分即交。** 8/24/48/72/96/120/144/168/192/216/232/240小时留可接续断点。不是240小时运行承诺。8小时有同口径测量原型，24小时完成测量灵敏度；48小时没有任务层信号只能再做一轮有明确理由的局部调整，再无信号即交断点。阶段不逐个等批准。

遵守仓库首读CURRENT的要求：可在第一次工具调用先捕获实时时钟，读取CURRENT后立即将捕获时刻写入本包evidence/executor/active-sessions.jsonl，再读其余材料；这是同期记录，不是事后估算。若首读已经发生且没有捕获时刻，立即记真实start，并将此前段标未知，按BUDGET处理，不补造。开工记录后执行：
```text
python -X utf8 handoffs/evaluator_executor/PRINTER-FOCUSED-GUIDANCE-20261127/VERIFY_SCOPE.py --phase start
python -X utf8 handoffs/evaluator_executor/PRINTER-FOCUSED-GUIDANCE-20261127/VERIFY_FOCUS.py
```
第二命令的冻结前失败是待做目标。旧包L2/L3失败是历史，不要求靠补造旧工时转绿。所有本轮失败和未完成均保留。不要清理现有未提交成果。

真实模型/API/平台业务API/账号/设备/交易/安装/外发/提交推送/索引均0。匿名补源另限8查询、执行24读取、独立8读取，失败计账；旧包已耗单列。测试只用合成个人资料。B0是本包冻结的当前脏工作区产品，不能用HEAD或旧657版本替代。A/B同资料、同目标、同回答能力；只回答真实界面当前问的问题，不再遍历oracle把所有答案直接注入。
