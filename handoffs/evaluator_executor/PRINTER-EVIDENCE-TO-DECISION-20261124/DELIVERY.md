# 交付格式

## 原始取证账

`evidence/executor/attempts.jsonl` 每个调用两行，以唯一 `id` 配对。先写 `event=scheduled`，结束追加 `event=completed`。两行有明确时区的 `at`。发起行写 `kind=query|open` 和 `target`。结束行写 `status=ok|failed|blocked` 和本包内的 `receipt` 相对路径；检索摘要不能用作事实来源。确因能力不可用而零次尝试时，交空账和明确阻断回执。

## 决策记录

`evidence/executor/decision.json` 使用以下字段。

- `mode` 为 `integrated` 或 `blocked_no_admissible_fact`。`source_access_blocker` 在零次尝试时填写具体原因。
- `sources` 以稳定来源 ID 为键。各值包括 `attempt_id`、`url`、`locator`、`observed_at`（带时区）、`models`（准确型号列表）、`region`、`limitations` 和 `receipt_sha256`。对应成功的打开记录。出处摘录及用途边界需可独立核对。
- `models` 以 `Brother HL-L1238W` 和 `HP M232dw` 为键。各型号写 `miniprogram`、`transfer_to_app`、`reuse_conditions`、`sales_identity`、`henan_payable` 五个判断。每个判断写 `status`、`source_ids`、`reason`。`status` 可取 `documented_supported`、`documented_unsupported`、`conflict`、`unknown`。以当前未确认的县区和费用口径，`henan_payable` 保持 `unknown`。
- 每个型号另写 `before_action`、`after_action`、`action_changed`（布尔值）和 `action_source_ids`。发生改变须列事实出处，理由在行动单解释。
- 每项微信路径判断可标 `publish`（布尔值）。标为 true 时，该型号在相应路径变体中的命题须含该项的来源 ID，支持、反证或冲突状态与材料一致。存在至少一项发布才可选择 `integrated`。未准入的材料可用于交代待核理由。
- 记录 `purchase_recommendation_approved`、`transactions_enabled`、`live_price_verified`、`wechat_reuse_verified`、`real_user_effect_verified`，五项均为 false。

## 人工判断与回放

`DECISION_HANDOFF.md` 对两款逐一写文档支持、反证或未知、可追溯出处、前后行动、继续选择的前提及最多三组尚需本人回答的问题。表明原案来自负责人代理。执行报告另写实际工时、纠错次数、分支选择、未使用额度、已核范围。

在冻结计划中，普通聊天回放命令输出开关两侧真实文本、证据、版本和安全状态。机器检验核实结构、配额、哈希和证据引用。评估者还需阅读原始资料，独立确认合法性、准确适用范围和行动变化。自动验证通过仅代表可送审。
