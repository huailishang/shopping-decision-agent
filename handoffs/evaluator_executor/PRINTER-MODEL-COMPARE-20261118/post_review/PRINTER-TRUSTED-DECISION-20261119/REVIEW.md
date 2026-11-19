# PRINTER-TRUSTED-DECISION-20261119｜评估者独立复核：通用论据—结论门禁（2026-11-19）

**本轮裁定：NEEDS_REPAIR / 业务与通用证据门禁未通过。** Stage0 的离线回执修复可独立签工程子项 PASS；B01来源审计和“事实推出对外结论”的强制校验均不达总体交付门槛。**禁止将工程全绿、搜索来源可见、商品编号存在或研究路径缩窄升级为选购决策收益/已验证能力。**

## 一、具体复核结果

1. **AC-01（R1/R2本地代码）PASS，限定工程项**。评估者独立实跑 `python3 -X utf8 -m unittest discover -s tests -p test_model_comparison.py -q` → **21/21 PASS**；`python3 -X utf8 -m unittest discover -s tests -q` → **485/485 PASS**。历史模型审计 `--audit` 仍因 `model cases not attempted: C05,C06,C07` 退出1（旧失败未被洗成通过），并非真实模型可用。旧受保护文件SHA差异0；历史尝试账6/10、账SHA `dc0f8631caa98df123206ef751312f42998e3f55614ac81b730bd7dbfe372026` 保留。
2. **AC-02（外部事实）PARTIAL**。本轮独立复核HP中国官方商城HTML历史抓取内容：M232dw确实对应商品SKU **9YF97A**，展示价¥1199，但抓取缓存约5个月前、河南县区未选择，故可支持*官网目录商品标识*，**不能证明今天当地库存、实际在售配置或到手价**。Brother官网型号/FAQ搜索线索和官网直接打开403只证实*有线索*，不证实实际微信长期复用。当前 `decision_matrix.json` 中HP `first_setup=supported` 绑定的是M232-M237**系列级**PDF，其限制虽披露，但仍须将状态标为“系列资料有条件适用/需准确型号核查”，不可当准确机型已验证。
3. **AC-03（对行动改善的证据支撑）FAIL（未证明）**。报告 `MEASURABLE_NEXT_ACTION_NARROWING_ONLY` 只有执行者手写差分，缺独立的确定性行动推导器、事实置信级别门禁和前后观测效用指标。HP所售SKU定位可合理使“下一步核哪件东西”更具体；**这是研究线索/过程进展**，不是证明用户决策质量更高或商品已符合硬条件。应重定级`RESEARCH_ACTION_REFINED_NOT_USER_BENEFIT`；购买建议继续 `defer`。
4. **AC-04（负向保护）PARTIAL**：适配器负向模拟真实通过；本轮人工 `decision_matrix.json.negative_cases[12]` 的 `observed` 全为 `represented_conservatively_in_matrix`，没有逐案的可运行校验或独立判例，不能混记12/12自动门禁通过。
5. **AC-05（公共取证审计）FAIL**。执行者如实说明：4条检索、7次主动页面/PDF读取是**事后重建**的尝试账，无法证明先记录scheduled，5条sources的`full_content_sha256`全为null、`captured_at_utc`全非精确观察。没有倒填或隐瞒，不应伪造原件；但强制审计条件未满足。

## 二、架构级发现：存在“确定性算对，文字仍能说反”的漏洞

当前确有两套可复用/可部分复用的确定性基础：
- `shopping_decision/evidence_comparison.py`：`rule_comparison`按结构化候选、需求、维度、计量单位、地区、时间和冲突计算`met/failed/unknown/conflict`；`validate_model_result`检查候选、条件ID、状态和事实ID绑定。
- `selection_criteria.py`、`research_snapshot.py`、`sale_configuration_evidence.py`等有来源/条件/合成SKU审计逻辑；`minimal_research.py`仍只能选择冻结旧证据包，新B01 `evidence/decision_matrix.json`是执行者离线手工研究，不经过统一发布校验。

**但没有完整通用的“证据→命题→可发布文字/下一行动”确定性门禁：**

1. `validate_model_result`第182–231行明确只校验objective结构，未校验自由文本的语义蕴含，返回`semantic_entailment_verified=False`，仍带原始`model_output`。`explanation`、`tradeoffs.statement`和`next_actions.description`只验字符串/ID/动作类型，对内容反证没有阻断；`tradeoffs.fact_ids`仅要求ID在全局事实表，不要求支撑所述候选/维度。
2. **评估者独立反例实际通过（无真实模型调用）**：事实`effective_price=1300 CNY`、硬预算`lte 1000`，`rule_comparison`返回`failed`。给模型输出同一个正确的结构化`status=failed`和正确`fact_id`，但把`explanation`改成“1300元小于1000元，所以可以买”、把summary改成“价格符合预算，现在即可购买”、把next_actions的`kind`标`research`却写“建议现在下单”后，`validate_model_result`仍**正常返回accepted结构**，只将`semantic_entailment_verified`设False、`purchase_recommendation_approved`设False。机器安全标志没放开，但如果前端展示原文，用户仍可能被错误引导。
3. 本次新研究`sources.json`、`decision_matrix.json`及`COMPARISON.md`未接入上述规则比较/校验器。矩阵状态`supported`和顶层`decision_gain`由执行者人工写入，没有程序根据来源类型（搜索索引、厂家系列、官方准确型号、店铺目录、有效地区报价）、有效期和用户硬条件重算。**有引用 ≠ 引用能证明结论。**

这是**架构级P1阻断**；若将其作为正式购物推荐直接展示则应视为发布前P0。现阶段没有证据显示发生真实购买或交易；当前`purchase_recommendation_approved=false`、`transactions_enabled=false`，须保留。

## 三、独立证据及责任界限

- 代码：`shopping_decision/evidence_comparison.py`第113–142、182–231行；`shopping_decision/model_comparison.py`第151–163行。
- 现有任务：本目录`REPORT.md`、`COMPARISON.md`、`evidence/sources.json`、`evidence/decision_matrix.json`、`evidence/validation_summary.json`。本轮原件均保留，不改执行者历史自报。
- 官方独立交叉核对：`https://www.hpstore.cn/hp-laserjet-m232dw-9yf97a.html`（历史页面显示型号、SKU、未选择省市区），`https://www.brother.cn/minisite/bcnactivity/new-question07.html`（搜索索引可见、直接读取403）；不把此评估研究写成上轮执行者的额外已授权取证或事前回执。

## 四、评估决定与下一执行方向

**工程R1/R2通过，但本轮整体未通过；停止继续扩大打印机人工分析报告。**

下一包唯一主目标不是继续抓价格、堆网页来源或重新调LLM，而是**把已有通用比较规则变成所有可发布结论的共同门禁**，复用旧确定性计算，避免再做一个只适用打印机的规则分支。重点：
- 结构化小命题（`subject + dimension + relation/status + fact_ids + rule_id + source_grade + scope/time`）先由程序生成并校验，**可展示结论仅从已通过的命题和确定性模板产生**；无法程序证明的自由文本应明确`UNVERIFIED`并隔离展示/待审，不能与已验结果混排。
- 统一管控：规则比较、模型比较、人工研究矩阵都不能绕过同一发布门；对手工矩阵做来源级别/型号/区域/有效期审查，不把系列级或索引级材料升级为准确型号当前支持。
- 明确维度门禁：地区有效价无有效报价保持unknown；完成初次设置不推出微信持续复用；目录SKU存在不能推出河南现货；事实不变时用户购物收益不可自增。
- 通用性证明：打印机本案及**另一种合成非打印机商品**都用同一函数核验，拒绝语义矛盾、跨维度/跨SKU引用、过期价和诱导交易，正常结论不受影响；不能依赖关键字封堵“下单”一词充当逻辑校验。
- 不采买、不登录、不调用真实大模型、不新增公开取证；历史原件/预算及脏工作树都保护；先做离线可靠工程，再回B01补高质量来源。

详细实施合同：`post_review/GENERIC-EVIDENCE-CLAIM-GATE-20261119/CONTRACT.md`。本评估暂不宣告代码已修。下一责任：**Executor**。

**大白话**：现在有一把会算账的尺子，但模型或执行者仍能在答案里写相反的话。正确做法不是多加几句提示词，而是先让程序核准每个小结论，再自动拼成给用户看的话；没法核准的就写“待核”，绝不能当确定推荐。
