# 通用证据—结论发布门禁｜执行者交付（2026-11-20）

Task: `GENERIC-EVIDENCE-CLAIM-GATE-20261119`  
角色：Executor  
结论：**核心离线实现及新旧全量测试完成；历史 VP-04 冻结基线审计存在阻断，不声明完整 L2 PASS 或独立验收 PASS。**

## 1. 实际完成

- 新增 `shopping_decision/claim_gate.py`，统一入口 `publish_checked_comparison(bundle, model_result=None, origin=rule|model|manual)`。结构化事实通过已存在的 `rule_comparison` 计算，附加来源级别、型号、区域、时点、精确报价维度门禁，生成 `VerifiedClaim` 和模板化 `PublicDecision`。
- 新增 `normalize_evidence_fact`，保留 `fact_id/source_id/candidate_id/dimension/value/unit/scope/observed_at/valid_until/grade/limitations` 等内部类型字段；不将原始 `statement/limitations` 或模型自由文字直接发布。
- `shopping_decision/model_comparison.py` 新增 `--verified-report` 的离线只读展示出口；真实模型路径如将来由负责人单独授权调用，标准输出只发布门禁生成的文字，模型原始文本只保留在本地审计 `validated.json`。本轮没有模型调用。
- 新增 `scripts/verify_claim_publication.py`，同一只读出口支持：规则格式 bundle、携带模型输出的 bundle、历史手工比较矩阵。
- 人工矩阵适配器 `validate_research_claims` 对本轮 `decision_matrix.json` 的手写 `supported` 不给予已验身份：缺少结构化数值事实、确切来源观察与目标地区报价时，全部退至 `unknown`。来源链接及旧手写状态只作为审计侧记录；`decision_gain` 无法成为程序证明。
- 数字例子：输入事实 1300、预算 `<=1000`，即使模型自由文字称“现在即可购买”，发布出口仍给出 `1300 ≤ 1000`、`failed` 和禁止购买的研究说明。输出交易/购买/实时价格标志均为 `false`。
- 新增 `tests/test_claim_gate.py`，覆盖预算反说、跨候选/维度引用、动作伪装、目录 SKU 和地区价混淆、系列/索引证据冒充准确型号、撤销/重算、冲突、非打印机合成空气净化器正常与反例、实际 CLI 输出。

## 2. 留存可重放证据

本任务 `evidence/` 目录：

- `gap_inventory.json`：同一恶意样本在修改前的实际复现（规则 `failed`、旧模型结构校验却接受自由文字、未做语义蕴含验证）。
- `adversarial_model.json`、`normal_bundle.json`：离线合成输入，非真实商品或模型调用原件。
- `replay_model.json` / `replay_rule.json` / `replay_manual.json`：旧恶意模型、正常规则、历史人工矩阵均经同一发布门实际走通；恶意模型原文未出现在公共结果。人工矩阵 12 条判断均为 `unknown`。
- `VP-01.log`：专项 12/12 PASS。
- `VP-02.log`：旧模型适配器 21/21 PASS。
- `VP-03.log`：全项目 497/497 PASS。
- `VP-04.log`：历史审计退出 1，原因不同于冻结计划期待值。
- `validation_summary.json`：各验收条件与 Git / 文件哈希检查细节。

## 3. 原子验收自检

| AC | 执行者本地结论 | 依据 / 限制 |
| --- | --- | --- |
| AC-01 | 本地 PASS | 恶意 `status=failed`、`summary=可买` 旧校验器可接收；新可发布输出不含反向文字；原 `rule_comparison` 未改 |
| AC-02 | 本地 PASS（结构与规则边界） | 来源类型、型号、地区、时间、报价要求降级；单纯 HTTPS/目录/系列不证实内容；**不等于验证真实互联网事实** |
| AC-03 | 本地 PASS（所列三入口） | 规则、模型、历史手工矩阵共用 `publish_checked_comparison`；历史 GUI、其它旧 CLI **未接线、不宣告已覆盖** |
| AC-04 | 本地 PASS | 12/12 专项、21/21 模型适配、497/497 全量；真实 CLI 离线重放 |
| AC-05 | **保护项 PASS、冻结审计 VP-04 阻断** | 17 个受保护文件 SHA 全部不变，BASELINE.sha256 正确；旧 6/10 次调用账未改；无真实模型/平台访问、交易、Git 提交或推送。详见下文 |

## 4. 必须交给评估者的真实阻断

`VP-04` 冻结命令要求在 `scripts/run_model_comparison_experiment.py --audit` 中观察“model cases not attempted: C05,C06,C07”。**实际本机运行：退出 1，返回 `{"status":"failed","reason":""}`。**

诊断已追到历史审计 `check_scope`：旧包 `FROZEN_INPUTS.json.baseline_head` 为 `ce34764...`，当前 Git HEAD 是后续已存在的 `53fa539...`，故在审计原本要判定 C05/C06/C07 前就被 `assert git rev-parse HEAD == baseline_head` 挡下。这不是对旧模型失败的修复，也不代表旧模型已通过。

为了独立了解旧账、**仅在内存中跳过历史 `check_scope` 作法证核查**，后续审计确实返回 `AssertionError('model cases not attempted: C05,C06,C07')`；这不是正式 VP-04 PASS，不修改正式审计脚本、不重置 HEAD、不重写冻结合同、不洗失败记录。旧账核算 6 次 scheduled、6 次 completed，仍有 C05/C06/C07 没执行。请 Evaluator 判定：旧审计基线与当前已同步 Git HEAD 的不兼容应作为冻结验收计划修订，还是保留为一个 BLOCKER。执行者不能擅自重冻结。

## 5. 严格范围与剩余问题

- 未调用任何新模型、网页、商业接口；未登陆、下单、支付；未 Git commit/push；原始历史证据未修改。
- 核心判断只保证“输入被准入的结构化事实 → 程序规则结论”，**不证明资料外部真实性、不证明商品现价/河南库存、不证明真人选购效果**。
- 历史 GUI、所有历史消费者未统一迁移；本轮纳入的发布出口和独立回放可信边界明确，其他出口不得宣称已改。
- 旧人工矩阵没有精确类型事实，所以其全部人工判断安全降级为待核；待后续 B01 获得准确型号、地区与可验证现价，才能把有效事实按协议导入。
- 单独的 `scripts/validate_workflow.py` 和 `scripts/run_validation.py` 不在本仓，使用冻结命令逐项重放并保存原始日志；未伪称已使用不存在的工作流验证器。

## 6. 本次范围内变更

新增：`shopping_decision/claim_gate.py`、`scripts/verify_claim_publication.py`、`tests/test_claim_gate.py`、本任务 `REPORT.md` 与 `evidence/`。  
修改：`shopping_decision/model_comparison.py` 的最小发布接线，以及 `CURRENT.md` 的当前交接说明。受保护的基线、父包研究矩阵、旧模型回执和源码均未改变。

## 大白话总结

过去程序明明算出“超预算”，模型还能写“可以买”，现在面向用户的已核结论改成由程序自己说，模型说反也不会混进去。打印机之外的合成空气净化器也跑通了，全量测试通过。不过历史审计卡在之前已经变化的 Git 提交版本，不能假装整包无条件通过；这项需要评估者处理基线冲突。河南真实价格、微信复用以及老 GUI 尚未验证，下一轮才能继续补。
