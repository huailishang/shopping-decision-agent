# 执行前准备格式纠正R1（Evaluator）

2026-11-26，本包尚未交Executor开工；未发生产品实现。

首次准备生成BASELINE.json后，标准工作流校验发现r42地图缺少三个可识别标题：端到端能力链、瓶颈清单、重新评估触发条件。原相关业务内容已存在，本次只拆分/补标题，不改假设、范围、判据、计划命令、预算和权限。Evaluator自身的准备失败不能当产品失败，也不能把原失败回执覆盖成通过。

保留原BASELINE.json/.sha256、首次freeze/start/workflow和freeze-receipt全部字节。正式执行基线改用新增BASELINE.R1.json及BASELINE.R1.sha256；VERIFY_SCOPE.py仅将默认manifest文件名改为R1，保护规则、白名单和阶段判据不变。CURRENT指向R1及其实际SHA。新R1基线同时保护原BASELINE/校验和、本增补和已修格式的r42地图；原件不重写。

准备时另将两个新黑盒检查的固定输入构造移入冻结脚本自身，移除对可编辑tests辅助函数的依赖；输入、oracle和验收意图不变。真实前测重新运行，旧版原件另存。START_HERE同步明确R1文件名。

先修格式、验证标准结构，再生成唯一正式R1基线并独立start复核。原准备快照不允许再用于当前Executor开工。此为首次开工前的有据准备修订，不重置180小时/6轮、不改旧WORKSHEET拒绝或其任何冻结原件，不新增产品权限。
