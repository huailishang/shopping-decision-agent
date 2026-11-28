# R3：历史审计最小兼容修复建议（待独立授权/冻结，不是合同修订）
任务：PRINTER-DECISION-WORKSHEET-20261126。正式L2仍FAIL（7/9），VP-05/06同因。
## 事实
历史FROZEN_INPUTS清单的两份Java原始SHA，与当前工作单任务的开工BASELINE中product_sha256一致，且能从其固定Git提交 c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f 读取到完全一致的原始字节。原始历史审计脚本仍未改。
候选补丁将两个指定现行Java文件的合法漂移约束到精确SHA，并从固定开工提交读取历史字节校验旧SHA；若现行文件未漂移（仍等于历史SHA），旧历史审计行为不变，不能单靠该结果证明工作单仍存在，当前功能由原产品回归另证。没有增加通配例外，不改变既有chat_bridge允许漂移与两个已审测试例外，不改旧历史清单、账本或原判定。
## 可重放验证
运行：python3 -X utf8 handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126/evidence/executor/probe_audit_compatibility.py --full-suite
隔离候选（仅内存替换审计模块）12/12定向、647/647全量、3022/3022冻结保护件未变；正式审计器仍按原规则拒绝两份Java现行漂移，正式L2 FAIL不得改记。候选历史审计返回6次安排、6次结束、0接受、C05/C06/C07未尝试，原父VP04仍REJECTED。
## 提请评估者/负责人明确
1. 独立审阅两份Java差异及其候选新SHA；核对固定旧提交原件；独立跑正反例。
2. 仅授权 scripts/audit_model_history_readonly.py 的精确兼容修改，以及新增针对该修改的独立测试（建议 tests/test_history_audit_version_transition.py）；明确以新修复包或书面冻结增补承接当前旧BASELINE和失败L2，不能覆盖旧BASELINE、旧清单、旧验证脚本、旧报告原件。
3. 新验收须检验旧保护集合只出现经过批准的审计器变化及明确新增测试，并保留旧范围检查原件；重新真实跑全量、历史审计及安全回归，独立裁定后才能正式通过，不简单忽略所有旧源码漂移。
4. 不授权任何提交/推送、外部调用或交易；前轮工时缺口仍需独立评估，不能补造。
## 原件
- audit-compatibility-proposal.diff SHA256=8ee18a2f8660ce8ae044077c1d290d03ff5bd85fd8f56e172b20f6d3d65ff76b
- probe_audit_compatibility.py SHA256=3437ce2c14a3c73d282f24634e9cd3330f3d69ac74362b2ae8c1bcb15ace2a1a
- audit-compatibility-probe.json SHA256=66766131846948f4b5df80a94665b7cae9aad8b00b6386ab30f470423b464e1b
- audit-compatibility-full.stdout.txt SHA256=7a7d11b4dd0cfb05682ae2c147f79ad24ac2099e3b14cf5a2074407f55820f13
- audit-compatibility-full.stderr.txt SHA256=f4ad1f98d0c0d004162b36f044b5b4f5e4df64dd3b06fd1c4fe48778888bc986
- audit-compatibility-scope.stdout.txt SHA256=e71e9ac79a3658d74fa4e44ba7b4fa66178527cd1e9f797ffea3d297f5d28269
