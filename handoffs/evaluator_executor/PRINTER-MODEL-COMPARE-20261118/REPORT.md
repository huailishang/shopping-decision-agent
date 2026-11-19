# PRINTER-MODEL-COMPARE-20261118｜执行者历史事实收口（补报 2026-11-19）

> 本文为执行者补交的失败报告，不是评估者验收通过。以历史冻结回执、`evidence/live/attempts.jsonl`、`evidence/paired.json` 和 `REVIEW.md` 为准；不修改冻结合同、输入或原始历史回执。

## 结果：FAIL / BLOCKED

- 冻结8例（C01—C08）；真实模型调用账本共 **6次**：C01-01、C01-02、C02-01、C03-01、C04-01、C08-01。C05、C06、C07未尝试。
- C01 已达历史单例上限 **2/2**；C08 为 **1/2**；原合同总预算 **6/10已用，剩余4次**。**本次补报没有新调用，不重置或挪用任何额度**。
- 有效合约输出 **0**：`evidence/paired.json` 的 `accepted={}`，历史记录 `actual_inference_completed_count=0`。模型比较增益未知，不能声称真实推理成功。
- 历史 CLI 已对 `gpt-5.5`、`gpt-5.4-mini`、`gpt-5.3-codex` 报 `model_not_found / unsupported with a ChatGPT account`。出现于本地模型列表不等于该账号有调用权限。未读取账号密钥、Token 或配置；模型调用费用与真实费率未知。
- C04-01发生中断、缺少原始回执；仍按一次尝试保守计入账本。不能补造回执，也不能按成功统计。
- C01-01旧 `meta.json` 将 `item.completed: error` 计为 `tool_event_count=1`，但对应事件仅能证实错误事件与 `turn.failed`，**没有真实工具调用的证据**。保留旧meta及其哈希不追改，在新适配器修复事件分类。
- 采集时间由各历史 `meta.json` / attempts账本记录；历史费用及有效用量未能确定，不虚构金额、统计和来源。

## 执行与验收区分

评估者在2026-11-19独立复核：专项 **13/13 PASS**、全量 **477/477 PASS**，但原包强制审计 VP-02 以 `model cases not attempted: C05,C06,C07` 退出 **1**（FAIL）。因此工程回归并不等于真实模型比较通过。原包整体仍 **FAIL / BLOCKED**；本报告不将旧状态修成PASS。

## 边界与交接

仅作为 `PRINTER-MODEL-ADAPTER-REPAIR-20261119` 的 AC-01 历史补报，**未执行任何新真实模型调用**；不修改旧 `CONTRACT.md`、`VALIDATION_PLAN.yaml`、`cases.json`、`FROZEN_INPUTS*`、`paired.json`、`evidence/live/**`、历史 `REVIEW.md`。本次需要的账号兼容性离线预检、错误事件分类、异常保护和回归属于新执行包，不会倒填旧账。
