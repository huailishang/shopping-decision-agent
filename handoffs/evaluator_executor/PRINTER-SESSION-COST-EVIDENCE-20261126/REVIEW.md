# 独立评估：会话与成本已有实质进展，完整业务验收不通过

Task ID: PRINTER-SESSION-COST-EVIDENCE-20261126
Task kind: one_off
Reviewed baseline HEAD: c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f
Final verdict: REJECTED
Project impact verdict: NOT_APPLICABLE
Observed bounded progress: 会话一致、成本口径和实际代码入口翻转已独立复现；不把 one_off 的局部进展冒充正式能力实验收益。
Continuation decision: CONTINUE
Business status: NEEDS_REPAIR

## 项目位置与评估范围

目标是让实际家庭按需求、专业知识及可核商品证据做出可解释、可改答的打印机决定。主链为需求→证据→候选去留→同口径比较→用户结果→反馈更新→购买前复核。本包前已建立来源门禁、硬失败淘汰、受控文字与离线建议；本包把未答/暂缓会话和成本实际重算继续向前推进。真实平台销售配置、河南有效价格、设备复用和真人收益仍未形成闭环，购买与交易授权保持 false。

依据 CURRENT 指向的 r40 判断，B05 为当前可自主推进的主瓶颈，B01 是现实证据依赖，B06 是回执与输入边界。本轮先核七项原计划，再构造独立反例并核原来源；未修改产品、旧合同、原验收器、执行报告或旧账。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/evidence/evaluator/independent-review/l3/L3-GATE.json
- Validation plan: handoffs/evaluator_executor/PRINTER-SESSION-COST-EVIDENCE-20261126/VALIDATION_PLAN.yaml

以本机技能原生 run_validation.py --mode evaluator，在 WSL 仓根独立执行。RV-EV-01 至 RV-EV-07 全部实际 exit 0。全量611/611，67.179秒；五组新专项30项，旧业务探针、原12案及只读历史审计均通过。2230份冻结保护文件内容无变化，HEAD/索引/manifest匹配；本轮未提交推送。七项通过只代表冻结机器检查通过。

| 独立证据 | 对应命令 |
|---|---|
| RV-EV-01 | 本包 VERIFY_BUSINESS |
| RV-EV-02 | 本包 VERIFY_DELIVERY，五组30项 |
| RV-EV-03 | 上包 VERIFY_BUSINESS |
| RV-EV-04 | 原12案 REPLAY_CASES |
| RV-EV-05 | 全量611项 |
| RV-EV-06 | 历史模型账只读审计 |
| RV-EV-07 | 本包范围 post，2230保护件不变 |

每项原始 stdout/stderr/meta 都在上述 l3 目录。独立新增输入、完整聊天结果及回执在同级 probe.py/probe-results.json 和 followup.py/followup-results.json。

## 逐项裁定

| 判据 | 裁定 | 独立依据及边界 |
|---|---|---|
| AC-01 会话与四消费者 | 通过 | 原未答、暂缓、无需及硬失败正例通过；新留出组合“扫描暂缓+双面必须+拒绝首次设置”两入口同样先查 Brother 双面；会话/公开行动同源，无硬失败复活。撤回彩印后本地认知前置缺失，安全返回待确认，没有继续发布旧彩印结论。 |
| AC-02 成本口径与数学 | 不通过 | 0/1800页、36/12月、CNY/USD不可比；不同费用范围拒绝；0/1500/1501/3000/3001与独立鼓计数复算成立。但是合法JSON中的有限数值字符串 `toner_price="1e1000000"` 可触发 decimal.Overflow，默认和合法后端 render_chat 均异常退出。应在成本输入边界明确拒绝不可处理数量级并返回当前规则结果。 |
| AC-03 正常代码入口成本变化 | 通过 | 同一受控硬条件满足包，仅改Brother随箱量0→1500，700/650变为600/650，公开情景优先及 result_text 确实翻转；硬缺证仍无赢家，旧需求/来源新版本会使情景失效。是显式Python参数的正常render_chat代码消费，未证明Java或日常聊天可录入成本。该产品入口缺口交下一包，不倒推本AC原约定失败。 |
| AC-04 回执/绑定/回退 | 不通过 | 普通混合工具、function_call/refusal、身份、角色及故障回退符合现有判据；允许普通供应商元数据。但 Responses `type=reasoning` 项的content被整体跳过，内部含function_call输出再附合法message时仍complete；实际聊天fake transport一次，建议business_accepted=true。未执行该工具、未联网；这是未支持混合内容被错误接纳，不是已发生误下单。 |
| AC-05 原文/版本/定位与影响 | 通过，限命题范围 | 独立公共读取5/6；从官方URL取得2600059字节PDF，154页，完整字节仅内存取SHA。印刷62页/PDF67维护段落及印刷139页/PDF144型号表均保存必要裁图并视觉核对。原摘句成立，M232dw在本手册型号表中。仅支持低/严重不足告警后的质量条件及耗材保护保修范围；不能证明寿命、产量、费用、故障率或整机保修。来源版本变化仅使依赖成本未知，确认条件及独立资格保留。 |
| AC-06 原家庭与离线效用 | 通过，限定离线 | 26组/19实际聊天代码回放核对，当前摘要与原件一致；独立选成本翻转、hard_pending无赢家和混合回执规则回退。原家庭有候选、硬条件、维护/成本未知和扫描首问；正文仍长。没有真实模型质量、token/费用/延迟或真人购买收益证据。 |
| AC-07 工程与范围历史 | 通过 | 原7/7、611/611、2230保护件、HEAD/索引一致；旧失败账、接受模型输出0与未完成旧实验均保留。后续新包建立后不能用原包范围脚本回头判新包文件越界；本结论对应RV-EV-07的实际快照。 |
| AC-08 当前版本与过程账 | 不通过 | 当前7362076字节原件SHA、生成器SHA及26/19计数均独立匹配，旧版本不覆盖。但执行者明确承认9次读取精确起止、主动工时未实时留存；时间窗不等于逐次记录。承认缺失是正确做法，仍不满足原冻结过程账要求，不能事后补成通过。 |

最终 REJECTED 的实质原因是 AC-02、AC-04 与 AC-08 未完成；不能把机器PASS代替业务PASS。没有将“缺真人”当成本包拒绝理由，也没有因这次找到原文升级成真实商品推荐成立。

## 两个可复现新反例

1. followup-results.json 两入口 `toner_price="1e1000000"`：`render_chat→bind_cost→evaluate_scenario→lifecycle_cost`，乘法触发 `decimal.Overflow`，未受现有except覆盖。输入短、有限且不需要网络，不是用大文件耗尽内存。普通值、非有限值和未知的原正确行为应保留。
2. probe-results.json 的 `unsupported_output_inside_reasoning` 与 `reasoning_mixed_tool_actual_entry`：reasoning.content包含 `{type:function_call,name:place_order,arguments:{}}`，同回执附合法排序JSON；归一complete且实际入口接受排序。输出只被当数据解析，没有工具执行。修复须验证支持的reasoning结构，不能禁止所有reasoning或所有扩展元数据。

一条探针曾在“撤回彩印”后调用评估者public()辅助器产生NoneType错误；followup已澄清实际产品正常返回，故不列产品缺陷。保留原失败和澄清，不删除不利或误诊原件。

## 来源复证与审计限制

source-read-01至05逐次记录本轮真实开始/结束UTC，操作含打开、定点阅读、截图、find及一次公开PDF读取。第3次网页截图仅返回引用，未收到可观察像素，不当视觉通过；第5次用本机已有PyMuPDF在内存打开官方PDF并保存必要裁图，随后实际查看两图完成复核，无安装。公共来源5/6、查询0；余1未用，不要求耗尽。

完整PDF SHA-256：c8838368bc03fa693cc50fb354c36c37b03e25710ef64bc35b6f8ab826af59ff。原执行者取得的是网页缓存摘录，不能用这次PDF字节SHA伪装成其原始获取SHA。官方原文入口：https://h10032.www1.hp.com/ctg/Manual/c07148381.pdf。图片和必要摘录仅用于本机核验，不将手册大段复制到产品。

当前工作流格式校验独立退出1，复现缺标准标签与计划引用。冻结原合同中中文AC相邻导致工具正则未识别，原权限标题也不匹配。原件不改、冻结机器七项不改；在下一包用规范可识别字段消除，不通过修改旧合同追认本包通过。这与产品反例分别记录。

## 瓶颈变化、投入价值与下一责任

B05从“同状态两入口不同步、成本只在helper”缩小到“真实用户无法通过现有主界面管理这些输入和后续更新”。B01维护来源此次限范围复证，真实微信复用/耗材实际量/河南有效价仍缺。B06剩余发现可在主包先决修复阶段收敛，不值得再为两个小修另开短包；也不宜继续堆只有Python注入才能运行的情景。

下一包采用 SINGLE：PRINTER-DECISION-WORKSHEET-20261126，目录 handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126。单一主改变是把现有会话、证据与成本组织为现有聊天/Java桌面能编辑、保存、恢复和重新计算的一份决策工作单。先合并两条边界修复，再贯通输入、来源状态、结果、恢复与失效，保留原比较引擎及规则基线。120有效小时上限、最多5轮集中纠错，分七阶段连续执行，不要求耗满；独立复核建议12小时。

其价值高于再次拓模型、换框架或扩大品类：已有算术和证据门禁能复用，当前界面没有成本入口是可观测缺口，新增模型请求不会修好入口或得到真实价格。匿名必要来源研究有界进行；没有真实资料也完成可执行的未知/补证路径，不等家庭设备回传。所有真实收益仍另验，零模型API/CLI、业务API、账号、交易及Git提交推送。由Executor按新冻结包接手，本评估者未实现新包产品代码。
