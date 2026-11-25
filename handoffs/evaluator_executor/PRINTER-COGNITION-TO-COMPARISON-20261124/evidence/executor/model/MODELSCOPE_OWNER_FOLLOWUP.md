# 负责人新增模型渠道尝试（2026-11-25）

负责人明确授权尝试 ModelScope Qwen 两个配置，成功后续办原模型对照评测。此为新增渠道验证，不重置历史 Codex 4/4 或旧6/10账。

- 配置及最小探针位于 `data/private/modelscope/`，沿用 `.gitignore` 的 `data/private/` 规则；`git check-ignore` 两文件命中，`git ls-files -- data/private/modelscope` 无输出。未存储密钥，不修改全局 Codex 配置。
- qwen 为 Responses，qwen-chat 为补齐的同地址 Chat Completions 兼容候选，后者尚未获服务端验证；探针直接 HTTP，无工具、无业务数据、无自动重试，禁止重定向，单次45秒超时。
- WSL与Windows进程、Windows User/Machine变量及项目指定.env检查未发现密钥；只输出存在性。WSL双协议及Windows qwen前检均返回 blocked_missing_env_key、request_sent=false。真实请求0，未产生模型输出或验证结果。
- 后续本机注入环境变量后分别最小测试；成功才以非敏感原案、改答、缺证三组同证据复用原校验器对照。原有冻结业务验收及评估者预留额度不变。当前独立评审仍待进行，不提交、不推送。
