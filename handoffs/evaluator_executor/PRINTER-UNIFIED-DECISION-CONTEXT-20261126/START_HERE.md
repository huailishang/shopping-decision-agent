# 执行者接手入口

先读CURRENT，再读本目录CONTRACT、ASSESSMENT、EVALUATION、VALIDATION_PLAN。旧包独立REVIEW和本包preparation是定位起点。原型为只读参考，不能原样接入。

本包是60有效小时连续长包，3轮集中纠错；第4小时先交一条完整运行链，第12/30/48小时记检查点，之后继续同包。无需为已授权的下一阶段重新问确认。模型API与模型CLI均0，真实平台API/账号/交易/Git提交推送均0。

开工在仓根的WSL运行：

```text
python3 -X utf8 handoffs/evaluator_executor/PRINTER-UNIFIED-DECISION-CONTEXT-20261126/VERIFY_SCOPE.py --phase start
python3 -X utf8 handoffs/evaluator_executor/PRINTER-UNIFIED-DECISION-CONTEXT-20261126/VERIFY_BUSINESS.py
```

第一条必须通过；第二条在准备时有已知业务失败，修复后应通过。所有失败先存原件，不能改脚本或旧证据使它通过。先做全部失败和只剩HP待核两案的通用/普通入口，再完成共用来源准入、行动顺序、维护成本、上下文与离线建议产品消费。

五组新增专项文件名固定于VERIFY_DELIVERY.py。测试验证行为，不按实现细节凑断言。最后按VALIDATION_PLAN逐条跑7命令，再按EVALUATION做业务自查；不能只报全量通过。

最终交REPORT.md、COMPARISON.md和evidence/executor原件，CURRENT改READY_FOR_REVIEW / Evaluator。未得真实资料、无模型增益或遇配额尽头，继续完成其他可做部分并准确交局限；不自签整体PASS。
