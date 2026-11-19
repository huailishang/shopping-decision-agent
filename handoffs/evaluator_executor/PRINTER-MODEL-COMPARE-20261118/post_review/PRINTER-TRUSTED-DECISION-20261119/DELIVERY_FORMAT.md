# 交付格式与取证核对（执行者使用，评估者冻结）

只需要一套可核事实材料 + 同案比较，**不新增业务平台或知识库框架**。缺资料时保留明确的unknown；不为了让文件变满而制造事实。

## 1. 研究尝试账 `evidence/attempts.jsonl`

每条请求先记 `scheduled`，结束再补 `completed`（不能覆盖原行），关键字段：
- `attempt_id`、`type`（`search` / `official_page_read` / `public_listing_read`）、`candidate_id`、`query_or_url`、`started_at_utc`、`finished_at_utc`、`status`、`final_url`、`content_sha256`、`error_family`、`source_timestamp_or_unknown`。
- 真实响应无法保留全文时，保留原始工具回执或可核的短原文定位/段落、URL和获取日期；**不复制网站大量原文**，也不伪造哈希。
- 失败、跳转到登录或验证码、页面打不开都计数。不主动跟随未知外站、账号登录或购买操作。
- 汇总单独列 `search_total<=4` / `page_reads_total<=8`、其中官方≤6、公开商城≤2。

## 2. 决策矩阵 `evidence/decision_matrix.json`

建议形状（字段示意，值须按真实证据填写，示意不是实际验证）：

```json
{
  "schema": "printer-evidence-decision/v1",
  "case_id": "henan_family_proxy",
  "input_sha256": "<digest computed from unchanged actual case input>",
  "as_of_utc": "<actual UTC>",
  "candidates": [
    {
      "model_id": "Brother HL-L1238W",
      "dimensions": {
        "wechat_initiation": {"status": "unknown", "source_ids": [], "scope": "CN", "limitations": "unverified"},
        "first_setup": {"status": "unknown", "source_ids": [], "scope": "CN", "limitations": "unverified"},
        "later_reuse": {"status": "unknown", "source_ids": [], "scope": "CN", "limitations": "unverified"},
        "listing_identity": {"status": "unknown", "source_ids": [], "scope": "CN", "limitations": "unverified"},
        "henan_effective_price": {"status": "unknown", "source_ids": [], "scope": "Henan CN", "limitations": "unverified"},
        "supply": {"status": "unknown", "source_ids": [], "scope": "Henan CN", "limitations": "unverified"}
      },
      "before_next_action": "<frozen baseline action>",
      "after_next_action": "<evidence-based action or unchanged>",
      "changed_reason_source_ids": []
    }
  ],
  "sources": [],
  "negative_cases": [],
  "real_device_test": false,
  "real_user_feedback": false,
  "real_transaction": false,
  "model_inference_performed": false,
  "decision_gain": "UNKNOWN"
}
```

另需完整列 HP M232dw。同款多来源冲突时 `status=conflict`，时间失效用 `stale`，无法证明用 `unknown`；不要把搜索结果页、帖子和商品详情页混成一种权威来源。

每个非unknown断言必须在 `sources[]` 内绑定唯一 `source_id`、准确型号映射、文档/店铺来源、已核短摘要/段落、URL、UTC采集时间、文档发布时间（若无写unknown）、大陆/河南适用前提、反面信息和有效期。商家商品身份必须有SKU/配置/商家名称的实际依据；价格须有当时地区和优惠条件，不能把指导价当到手价。

## 3. 人话比较 `COMPARISON.md`

按固定顺序：
1. 家庭需求（一句话；首次扫码接受、微信必须，不重问）；
2. 兄弟HL-L1238W目前支持/不支持/未知，证据来自哪；
3. 惠普M232dw目前支持/不支持/未知，证据来自哪；
4. 两条微信操作分支及适用条件；
5. 两款真实在售与河南价格是否可核，明确有没有资格说“≤1000元”；
6. 与取证前相比，下一行动改变了什么；如果没变，为什么；
7. 最多3个真正未答的本人问题；不声称已购机或已试机；
8. 一段白话总结：明确“建议下一步做什么、缺什么不能直接买”。

## 4. 执行报告 `REPORT.md`

须分栏报告：
- R1/R2各自代码、负向测试、真实运行命令、通过数与失败数；
- B01资料来源和用量账、两款矩阵、相同输入前后行动差分；
- 工程状态（PASS/FAIL）、证据状态（GROUNDED/UNKNOWN/CONFLICT）、行动改善（MEASURABLE/UNCHANGED/UNKNOWN）；
- 原冻结字节保护、历史模型6次调用未变化、模型新调用0、业务API调用0、交易0、Git提交推送0；
- 实际花费时长/时间窗口、未估得成本、停损原因、下一评估者需要核对的来源原文；
- 本包的最终白话翻译，不止堆任务术语。

## 5. 不得抢跑

若R1/R2修复后专项测试仍无法安全通过，停止Stage1取证，提交工程失败报告；如果Stage1没有得到新事实，也要交真实断点。新来源本身不会自动证明推荐更好，更不会推翻旧11/18模型实验的FAIL。
