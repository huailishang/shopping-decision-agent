# PRINTER-TRUSTED-DECISION-20261119｜执行者统一交付

**执行日期：2026-11-19；本包结论：工程R1/R2已修复并通过本地测试，业务证据局部有新增，购买推荐仍暂缓，公开取证账的事前登记/原文哈希未达完整审计要求。交 Evaluator 独立核对，不自签整体PASS。**

## 一、三条结果（禁止合并成“总体已通过”）

| 维度 | 执行者观察 | 边界 |
|---|---|---|
| **ENGINEERING_PASS（局部工程）** | R1/R2分类器及对应新增反例通过，专项 **21/21**、全量 **485/485**；旧模型审计退出 **1**，原因仍为 `model cases not attempted: C05,C06,C07`，符合历史不洗账要求 | 不代表模型实际接通；不代表真实购买建议可靠 |
| **EVIDENCE_MIXED_GROUNDED_AND_UNKNOWN** | HP中国官方商城网页明确 M232dw／SKU **9YF97A**；HP系列安装指南说明 HP Smart 的微信功能开启步骤；Brother中国官网检索索引出现 HL-L1238W 小程序线索，但直接网页访问403 | 两款准确型号后续复用均未验证，Brother官方正文不可直接阅读，河南有效价格/供应仍未知 |
| **DECISION_GAIN_ACTION_ONLY** | 对HP，下一行动由“寻找准确在售型号”缩小为“以 **9YF97A** 核具体河南县区送达及优惠后价格，同时验证微信实际发起”；Brother行动没有可靠改变 | **不等于选出优胜者**，真人帮助和购买收益没有实测 |
| **AUDIT_GAP** | 公共检索次数遵守数量上限，但浏览器外部调用先发生、本地账后补；真实调用起止UTC与来源全文SHA未能保留 | **VP-04/VP-05来源账完备性不能判全通过**，请评估者明确此缺口，不得事后伪装“事前scheduled” |

## 二、Stage 0：评估者遗留R1/R2最小修复

修改仅限 `shopping_decision/model_comparison.py`、`tests/test_model_comparison.py`：
- **R1：** 所有`turn.completed`的`input_tokens/output_tokens`要求`type(x) is int`且非负，拒绝`True/False`、浮点数、字符串、负数、缺失字段。若同时存在一条合法和一条非法完成事件，不允许合法一条掩盖非法一条。
- **R2：** `item.started / updated / completed / failed`的`item`丢失、字符串、空对象、缺少`type`、布尔或空白`type`均标为畸形并拒绝；真实工具类型、未知类型仍fail-closed；`item.type=error`不会被误计为工具。
- 新增2个测试方法及其多个子反例；保留正常离线合成响应的通过用例。只使用模拟子进程，**没有调用真实模型**。不重新解释或修改旧C01事件原件。

专项命令：`python3 -X utf8 -m unittest discover -s tests -p test_model_comparison.py -v` → **Ran 21 tests，OK，退出0**。原工具回执含完整测试列表，但该轮原始stdout/stderr未单独保存；本包 `evidence/validation_summary.json`准确注明此局限。另在本地直接进行8条分类器断言，全为`true`（验证概况见同文件）。

## 三、Stage 1：准确型号、公开网页及真实性

固定代理需求：Brother **HL-L1238W** 与 HP **M232dw**；河南家庭，人民币≤1000元，0–50页/月，黑白为主，**微信发起必须**，首次App扫码配置可以接受。直接小程序是否唯一可行、可否中途转App、复用是否可偶尔重绑、收货县区及耗材是否算入预算均未替用户决定。

**取证预算实际为 4 条搜索，7 次主动页面/PDF读取（官方5、公开商城2；包含失败）。** 具体查询、失败403、缓存未命中、索引引文，见：
- `evidence/attempts.jsonl`：11组查询/读取的回顾性对应记录；外部工具未给到完整原始网页字节，所以`content_sha256=null`，仅保存短事实的`excerpt_sha256`。
- `evidence/sources.json`：检索线索与已读取主要事实分层；不能把兄弟官方索引或京东分类页当成准确详情原文。
- `evidence/research_budget.json`：公开查询和读取上限独立计数，未挪用旧包或模型账。

**Brother HL-L1238W：** `https://www.brother.cn/printer/prt/hl-l1238w` 的索引显示微信小程序支持；`https://www.brother.cn/minisite/bcnactivity/new-question07.html` 的索引把HL-L1238W列在远程机型名单，提示Brother Mobile Connect及畅享印。两站直接读取都是403，故不能签完整原始操作链/复用；京东分类页检索到型号但主动打开失败，未获得具体在售SKU或河南结算价。

**HP M232dw：** HP官方`https://kaas.hpcloud.hp.com/pdf-public/pdf_12826995_zh-CN-1.pdf` 的M232–M237系列安装指南写明先配置HP Smart、再启用“微信打印”；PDF文字已解析，截图抓取缓存失败。惠普中国官方商城`https://www.hpstore.cn/hp-laserjet-m232dw-9yf97a.html` 网页明示准确 **M232dw** 与 **SKU 9YF97A**，展示价 **¥1199**，但网页抓取有滞后、地区未选定，不能充当河南现价/适用优惠/县区配送或库存证明。绝不把M232dwc混作M232dw。

**价格与购买资格：** 两款 `henan_effective_price=unknown`、`supply=unknown`，不得判任何款符合≤1000元；`purchase_recommendation_approved=false`，交易功能继续关闭。

## 四、Stage 2：同输入、前后行动及安全反证

`evidence/decision_matrix.json`引用冻结`PRINTER-WECHAT-DECISION-FACT-20261117/INPUT_UPDATE.json`的真实SHA256 `9f8b28b5eaafa0e6161be5ba92dc2b79d1b274cdd5efa6d83788961e63904e8f`，并完整记载两型号各六维：`wechat_initiation`、`first_setup`、`later_reuse`、`listing_identity`、`henan_effective_price`、`supply`。

`COMPARISON.md` 对比相同输入资料前后可执行下一动作，区分微信小程序直接发起与微信分享后转厂商App，不猜用户偏好；同时有12条负向审查条目（错误型号后缀、Wi-Fi冒充微信、一次配网冒充复用、过期价格、分类页冒充SKU、互相矛盾、缺资料、外部指令注入、虚假引用、诱导交易、未读截图、地域库存）。这些业务负向条目为**人工决策核对**，不是12个自动测试通过。

**收敛处：** HP找到准确官方商店SKU 9YF97A → 下一步可针对该SKU查河南到手价。**未收敛处：** 微信真实发起与长期复用、兄弟准确销售项、河南价格、使用者反馈和选购结论。

## 五、Stage 3：回归结果、旧账及保护

- VP-01：专项21/21，退出0（Stage 0实跑）。
- VP-02：`python3 -X utf8 -m unittest discover -s tests -q` → **Ran 485 tests；OK；退出0**。实际原始stderr/stdout及元数据写入 `evidence/VP-02.*`。
- VP-03：`python3 -X utf8 scripts/run_model_comparison_experiment.py --audit --task handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118` → **退出1**，准确原因为`model cases not attempted: C05,C06,C07`。写入 `evidence/VP-03.*`。这是保留旧失败，不是修成绿。
- VP-04：公开来源矩阵已具备，但**事前scheduled和准确UTC及原文内容SHA不能证实**；评估者必须核原文。来源质量、微信复用不得凭本报告认定全面通过。
- VP-05：`BASELINE.json` SHA与`BASELINE.sha256`一致；**16个受保护文件均无哈希差异**；旧`attempts.jsonl` SHA一致、**scheduled6 / completed6**，历史模型调用预算 6/10，用剩4次，不消耗、不清零。本轮新增Git状态无越界文件，源报告和计划见 `evidence/validation_summary.json`、`evidence/changed_files.json`。

**实际花费与限制：** 本轮在2026-11-19本地执行，精确有效工时没有独立计时，不能虚报5小时完成或声称零成本；模型额外推理0，商家业务API0，账户登录/凭证读取0，真实订单/支付0，Git提交/推送/重写0；公开查询和官方/商城浏览只读。研究截图与浏览器工具未留完整内容原件，为真实交付限制。工作树其他历史未提交资料未清理。

## 六、执行者交评估者的重点

请独立查以下四件：① R1布尔用量与R2畸形item是否真的被拒、合法合成回执是否仍通过；② HP官网SKU 9YF97A与Brother官网索引能否在当前时间和地区重核，**不把网页索引或5个月前报价写成当前可买事实**；③ 新包公开调用数量与事前审计账缺口要单独裁定，严禁事后当作合规；④ 是否真收敛下一行动、是否值得将主线继续放在B01而非新的模型对比。

**下一角色：Evaluator。** 本轮执行者完成修复、有限取证、对照和回归，但鉴于取证证据审计缺口，**不请求总体PASS**。后续若验证SKU/微信仍不可用，优先做最少一次准确地区价格和设备体验核对，不能增发无收益的大包。

## 七、两段大白话

**程序方面：** 我把模型回执里两个容易误判的地方补严了：不能把“true个Token”当成数字，也不能把乱码的工具事件当成正常回执。专项21项、全量485项都通过了，过去6次模型失败记录也没有动。

**买打印机方面：** 惠普M232dw这次找到官网准确商品编号9YF97A，兄弟HL-L1238W找到了官方微信打印线索。但两款到底能不能按亲戚习惯从微信长期使用、河南当地拿到的实际到手价是多少，还没核实。所以不建议现在凭这些材料下单；先用准确型号查河南价格，再验证微信日常打印流程。
