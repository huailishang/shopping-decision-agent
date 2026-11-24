# 可复审交付格式

`evidence/executor/packet.json` 含 `mode`、`sources`、`models`、`open_questions`。模式为 `auditable_evidence` 或 `pending_source`。型号键固定为 `Brother HL-L1238W` 和 `HP M232dw`。

- 每个来源包含 `kind`（`manufacturer` 或 `owner_supplied_manufacturer`）、`url`（厂家原文）、`locator`、`obtained_at`（带时区）、`permitted_use`、`models`、`region`、`fragment_path`（相对于本包执行证据目录）、`fragment_sha256`、`anchor`（实际定位到的原文短句）。片段使用 UTF-8 留存最少原文，页图/PDF可附原件。作者摘要和搜索结果不能作为片段。选择有权提供的必要材料，并先脱敏。
- 每款写 `miniprogram`、`transfer_to_app`、`reuse`、`sales_identity`、`henan_payable`、`next_action` 和 `action_source_ids`。五项判断各写 `status`、`note`、`source_ids`。状态为 `documented_supported`、`documented_unsupported`、`conflict`、`historical_lead`、`unknown`。只有前三种微信路径状态可由可审原文支持进入聊天。实际应付价需有本人确认地、费用口径与真实凭据，未满足时为 unknown，暂不产品发布。
- `open_questions` 最多 3 组。行动单说明哪些由本人回答，哪些由材料持有者提供，哪些能在条件不全时先做。无新增证据时给出具体断点。

`evidence/executor/attempts.jsonl` 的公开查询和读页，与 [上一包取证账规范](../PRINTER-EVIDENCE-TO-DECISION-20261124/DELIVERY.md) 相同。每次先登记再执行。需提供空账对应的实际停止原因。机器验证检查文件哈希、定位、作用范围、资源计数、真实聊天开关和命题出处；人工复核作者来源与语义、有效性、合法用途、行为差分。
