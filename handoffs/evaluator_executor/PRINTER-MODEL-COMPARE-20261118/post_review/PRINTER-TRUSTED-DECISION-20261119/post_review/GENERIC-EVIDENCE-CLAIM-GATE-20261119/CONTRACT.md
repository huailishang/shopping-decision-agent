# 通用商品比较｜证据→结论的确定性发布门禁（下一执行包）

Task ID: GENERIC-EVIDENCE-CLAIM-GATE-20261119  
Task kind: architecture_blocker_repair / bounded_generic_validation  
Contract state: CONTRACT_FROZEN / READY_FOR_EXECUTOR  
Current role: Executor  
Parent review: `../../REVIEW.md`（PRINTER-TRUSTED-DECISION-20261119）  
Baseline HEAD: 以本目录`BASELINE.json/.sha256`为准；工作树已有大批未提交文件，禁止重置/删除/覆盖他人改动  
Project bottleneck: **B06通用证据—结论发布门缺失**（本评估发现；旧r35瓶颈地图保护，不在原地图里新增ID）；次级B05模型协作、B01真实商品事实不足  
Hypothesis: `H-GENERIC-CLAIM-PUBLISH-01`  
Authorization: local_code=true, offline_tests=true, live_model=false, public_research=false, business_api=false, login=false, purchase=false, commit=false, push=false

## 核心判断

项目已具备`rule_comparison`的条件计算和`validate_model_result`的结构/引用检查，`sale_configuration_evidence`等也有若干局部保护，但尚无**跨规则、模型、人工研究三路径统一的发布前确定性检查**。评估者能构造`1300>1000`已算`failed`，说明却谎称`1300<1000`且建议买，依然通过现有结构校验的负向反例；本轮人工 `decision_matrix` 也无统一入口审查，`MEASURABLE`等人工标志可随意写。模型不确定性不是让程序也放弃确定性边界的理由。

**唯一主目标：让任何宣称“已核”的商品结论必须由通用的结构化事实和确定性规则生成/批准；不具有充分依据的内容不能以“已证实”身份对外输出。** 不是让程序解决所有自然语言蕴含或凭空验证互联网真伪，不能承诺数学证明任意句子正确。

## Stage 0｜基线和独立反例

1. 阅读本目录`BASELINE.json`、父包`REVIEW.md`、`shopping_decision/evidence_comparison.py`、`research_snapshot.py`、`selection_criteria.py`和已有模型比较入口。原件的代码与历史数据不改、不伪造既往测试。
2. 离线复现并归档**三个核心负样本**：结构正确但`summary/explanation/tradeoffs/next_actions.description`说反；`tradeoffs.fact_ids`引用其它候选/维度；人工作成的矩阵用系列级来源宣称准确机型完全支持、把过期/未选地区报价变成现价并自称用户收益。
3. 用同一个正常数据集确认`rule_comparison`结构状态不需要重写，差异与可复用函数列到`evidence/gap_inventory.json`。

## Stage 1｜小型通用确定性结论协议

在可复用模块（建议`shopping_decision/claim_gate.py`）建立最小协议和API；尽量组合复用`evidence_comparison`的规则计算与来源验证，而非推倒重建。

- `EvidenceFact`至少包含`fact_id/source_id/candidate_id/dimension/value/unit/scope(model,region)/observed_at/valid_until/grade/limitations`；来源ID的存在只是结构条件，不是来源真实权威性。缺精确来源观察时间、只有索引或系列级来源，不能自动升级为“准确型号已验证/地区当前有效事实”。
- `VerifiedClaim`由程序重算的`candidate_id/requirement_id/status/rule_id/supporting_fact_ids/source_grade/scope/limit`组成。支持`met/failed/unknown/conflict`并允许“资料说明存在，但当前具体目标仍unknown”的层级，保证边界。数字预算用精确数字比较，布尔值不是数字；SKU/店铺/地区价格各是不同维度，不用同一ID替代。
- `PublicDecision`由`VerifiedClaim`和程序定义的文字模板/行动规则渲染。**不得直接把模型的原始summary/explanation/tradeoff/action文字或手工`decision_gain`当发布依据**。原始自由文本可以留审计侧字段，如`unverified_model_notes`，但不得出现在被标`verified`的对外字段。
- 给源证据/论点可核状态独立标签：`verified_structural`（仅字段结构）、`source_traceable`（来源可追溯）、`scope_applicable`（型号/地区/时间/配置匹配）、`entailed_by_rule`（结构命题由规则计算），四者不可互相替代。无法验证资料真实内容时标`unverified_external_fact`；不得把有HTTPS链接当已核真实功能。
- 对`next_action`用确定性门禁限制动作与凭据：`verify_price`仅能由价格缺证/需报价导出，`research`仅能用于资料缺口，`clarify`仅能用于未答需求；绝不能通过`kind=research`附带“立即下单”的自由文本。
- 保持`purchase_recommendation_approved=false`、`transactions_enabled=false`、`live_price_verified=false`等已有安全状态；本轮不是交易授权模块。

## Stage 2｜真正走通现有输入和出口

- **规则路径**：`rule_comparison`返回的状态是事实判定的单一基础；生成对外的解释需绑定到同一规则结果和事实ID。
- **模型路径**：`validate_model_result`可保留原始响应作审计、兼容此前内部schema，但新增`publish_checked_comparison(...)`或同等统一发布入口；其返回“已验”的文字只能来自程序化结构。模型若提供相反文字，应隔离/拒绝，不以`semantic_entailment_verified=False`却继续显示为可信解释。
- **人工资料路径**：给本轮`evidence/decision_matrix.json`及未来同结构商品数据提供`validate_research_claims`或适配器，并通过相同的source/claim/action门；系列说明与准确型号、搜索摘录与原文、展示价与地区有效报价不可混级。真实内容无法确证时安全降级，保留未知与下一核查动作。
- **最少一个真实展示出口**：接线到目前本地模型比较CLI或一处只读展示/API出口，使实际显示文本不直接绕过发布门。不得在全项目每个历史输出塞分支或改GUI以应付本包；如现有旧CLI涉及不兼容格式，提供新只读`--verified-report`输出并测试，不声称所有历史入口已经完成接线。
- 限定为**通用数据驱动**：不把`M232dw`、`HL-L1238W`、微信、河南硬编码进核心判定，产品/品类规则通过来源类别、维度和契约输入表达。模型仅可建议候选解释，不能提升资格/证据等级。

## Stage 3｜必要负向、正常和跨品类测试

必须至少覆盖：
1. 硬预算事实1300>1000但文字声称符合/可买；**用户展示的已验文本绝不能含相反结论**。
2. 正确`status`+存在的事实ID但假`summary/tradeoff/next_action`；隔离不可信文字或拒绝发布。
3. 不相关候选/维度事实、伪来源、过期价格、目录SKU冒充实际销售SKU、未选河南区县展示价冒充到手价、系列说明冒充准确机型实测、旧截图或搜索摘录冒充完整来源。
4. `unknown`、`conflict`、新事实撤回、用户修改预算时必须重算并撤销失效结论。
5. 一份**合成非打印机品类**（例如空气净化器的CADR/面积/噪声约束或其它仅本地生成的事实），由同一模块验证，不得新增品类特化代码。
6. 正常干净数据生成正向/限制/下一查证事项；旧打印机必需功能、型号和用户需求保持`unknown`时不冒充PASS，不能将“完成取证任务”当用户收益。

## 原子验收（全部强制）

- **AC-01**：复现原失败，修复后同一个恶意合成样本不能被“已验出口”接受；已有规则结构判断不降级。
- **AC-02**：来源对象、等级、型号/维度/地区/有效期与结论/行动双向绑定；缺任一关键证据时自动降级/阻断。
- **AC-03**：规则、模型、人工矩阵至少在**被本包纳入的三条入口**共用同一门禁；不走两套冲突判定。父包旧未接线GUI须明示“未覆盖”，不伪报全系统完成。
- **AC-04**：负向和跨品类合成用例通过；`python3 -X utf8 -m unittest discover -s tests -q`全量退出0；不得用“运行通过”替代结论蕴含证明。至少一个入口真实重放，逐项断言展示字段。
- **AC-05**：原冻结材料、旧预算6/10、旧审计失败、父包来源和报告保留；无新模型/平台请求、业务API、登录、交易、Git提交推送；实际变更只在合同白名单。

## 允许改动与禁止改动

允许：
- `shopping_decision/claim_gate.py`（新增通用模块）；
- `shopping_decision/evidence_comparison.py`、`shopping_decision/model_comparison.py`（只作通用门禁的最小接线，不破坏原冻结实验回执）；
- `tests/test_claim_gate.py`、必要时`tests/test_model_comparison.py`；
- `scripts/verify_claim_publication.py`（新增可复现只读校验入口，可不另建网页/GUI）；
- 本包`REPORT.md`、`evidence/`、`CURRENT.md`状态/交接说明。若为现有CLI接线必须改额外一处文件，先在REPORT记录原因和对比，限单处、禁止顺带重构。

保护：
- 父包`REVIEW.md`、`CONTRACT.md`、`COMPARISON.md`、`evidence/**`，上轮`PRINTER-MODEL-ADAPTER-REPAIR`材料、`docs/PROJECT_BOTTLENECK_MAP.md` r35、原`FROZEN_INPUTS*`、历史live账本、用户既有未提交工作树。
- 禁止现场采购/登陆、打印机设备操控、额外网页检索、厂商业务API、新模型推理、提交、推送、洗账、制造假原文哈希。
- `BASELINE.json`、`BASELINE.sha256`、本`CONTRACT.md`和`VALIDATION_PLAN.yaml`为评估者冻结输入，执行者不可修改。

## 时间、纠错与停损

估计执行≤6有效小时：基线/复现≤45分钟、通用协议+最小接线≤3小时、反例及跨品类回归≤90分钟、集中报告≤45分钟；**最多两轮集中本地纠错**。纯离线，不新增真实调用额度，不承诺解决所有自由文本的语义校验。若无法做到统一发布边界，**禁止以打印机专属if或敏感词过滤假装通用**；报告`BLOCKED`与最小差异，交评估者。

成功定义仅是**通用发布门禁在受测三条路径上线并能拒绝错误结论**，并非当前商品已可买、真人收益、模型真实推理或全部历史GUI都已升级。后续优先B01补可信商品源及有效地区报价。

## 交付口语总结

最后用两段普通话说明：程序如何挡住“证据说一套、结论写另一套”；这个能力是否不依赖打印机型号、适用于另一个合成商品，以及还有哪些入口/原文真实性无法自动保证。
