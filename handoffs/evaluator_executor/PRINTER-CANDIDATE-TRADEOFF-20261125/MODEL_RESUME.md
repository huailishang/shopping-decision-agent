# 模型支线续执行｜2026-11-25

负责人要求恢复连接后再次执行模型测试，再交评估者。CodexPro Funnel 已恢复项目访问、Bash 和工作区写权限；实际运行环境为 WSL Python 3.12.3。原合同及额度不变；商汤指定私有配置路径未见文件，未搜索其他凭据、未调用商汤。仅使用原魔搭 Responses 地址和本机既有配置，无工具调用或平台业务 API。

## 尝试账（本包 4/4，剩余 0）
| 尝试 | 场景 | HTTP | 结果 |
|---|---|---|---|
| 1（历史） | C01 原案 | 200 | JSONDecodeError |
| 2（历史） | C08 双硬约束 | 200 | JSONDecodeError |
| 3（本次） | C12 证据撤回 | 200 | JSONDecodeError，141.022秒 |
| 4（本次） | C12 同案纠正 | 200 | provider_not_completed，93.035秒 |

前三次原始响应均从 JSON 中间开始，不是完整 JSON；不拼接、不推测丢失内容。保留原 run_compare.py；另存 run_compare_response_retry.py，显式非流式请求、Accept JSON、identity 编码，输出上限从16384降至8192，记录响应类型、字节数、传输编码。仅针对已记录的同案 JSON 失败做一次纠正，原四次上限仍有效。多个请求参数同时变化，不能单独归因，也不能证明传输问题已永久解决。

第4次响应为完整 JSON（36595字节，application/json，chunked）；服务端确认实际 Qwen/Qwen3.8-Flash-Next，输入4757、输出8192、总12949 token；status=incomplete，incomplete_details.reason=max_output_tokens，output 仅 reasoning 项，未产生可供校验的最终业务答案。0/4通过模型输出验收，模型增益不可判；规则路径未修改。

四次原始响应 SHA-256 均与对应 meta.json 匹配。原始响应保留在 Git 忽略的 data/private/modelscope/ 内；本次新增 C12、C12-r1 两目录保存输入、规则结果及调用元数据。无密钥外发到报告。前两次历史及所有其他包预算不改、不清零。

## 工程复核
本次 WSL 全量 unittest discover -s tests -q 实跑564/564，退出0，55.367秒，日志 evidence/executor/model/resume-full-20261125.log。VERIFY_SCOPE.py --phase post 退出0，2017份保护件无变化，HEAD匹配，暂存区为空。本轮只增补本包模型证据及交接文档，不改产品逻辑。无 Git 提交或推送。

## 交接
本包模型尝试已执行完毕而非模型业务通过；按原合同允许模型支线失败交付。保持 READY_FOR_REVIEW / Evaluator，由评估者独立核对真实回执、原案候选取舍和厂家来源，裁定是否另立模型推理预算/机制。禁止继续消耗已用尽的本包模型额度。不得将 HTTP 200、完整 JSON 或 reasoning 项视为有效模型答案或业务增益。
