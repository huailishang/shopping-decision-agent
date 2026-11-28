# 离线候选实跑交付 2026-11-26

独立候选，不修改旧任务 CURRENT、产品代码、冻结夹具与旧账。参考见 DESIGN.md。

最终独立命令：PYTHONPATH=. python3 -X utf8 handoffs/context-model-pilot-20261126/test_pilot.py
退出 0，8/8，测试运行 0.068 秒。初次 python 与 wsl 命令退出127；python3 可运行。另一次组合测试+Git状态命令测试已通过，但后续命令整体超时，不能将组合命令视为退出0。最终单独测试退出0。未独立完成全仓状态检查与全量回归。

| case | mode | old prompt bytes | new wire bytes |
|---|---|---:|---:|
| C01 | model_rank_actions | 15469 | 4134 |
| C08 | rules_only | 15469 | 0 |
| C12 | model_rank_actions | 14945 | 2847 |
| C08_SHORT | rules_only | 7645 | 0 |

旧为按现有 build_prompt + JSON Schema 重建的 UTF-8 字节，新为完整 payload canonical JSON 字节，不是厂商 tokenizer 统计。C08/C08_SHORT 直接寻找替代候选；C12 仅对尚未淘汰的 HP 生成行动候选。两份有请求的案例可选条目未被省略。fixture 模型容量是测试配置非真实厂商能力。

测试：action gate / all excluded / context budget / failures / protocols / report / success / withdrawn evidence。实际完成的是离线请求编译、两协议回执夹具归一、确定性行动候选及模型 action ID 校验；未实现实际 HTTP、模型质量/增益、生产聊天入口或第二消费者，未调用模型。原项目下一角色仍 Evaluator；建议一并检查候选并确定新冻结任务。零 Git 提交/推送。
