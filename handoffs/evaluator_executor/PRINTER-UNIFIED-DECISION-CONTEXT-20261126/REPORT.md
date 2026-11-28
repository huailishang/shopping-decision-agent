# 执行者交付｜2026-11-26

任务：PRINTER-UNIFIED-DECISION-CONTEXT-20261126。状态：机器强制验收7/7通过，业务交独立评估；不自签整体PASS。HEAD c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f；基线 SHA256 0fa49ba52efe61b9daf60f98824520cb01bcda6cb3cea1367e339809626e7630。

## 实际变更及调用链
- claim_gate/confirmed_comparison：来源准入、硬反证和候选资格统一；decision_actions 集中形成合法行动、过滤已淘汰候选、优先硬缺证。对缺观察时间、畸形型号范围及未来观察时间拒绝不适用事实。
- cognition_comparison/chat_bridge：普通聊天、合法绑定后台资料、通用发布入口与离线注入实际消费同一准入后的决定；全部淘汰停止两款比较；默认规则路径不发网络。后台不再用旧采购核查覆盖首步；非必要扫描、双面不作为首步。
- context_builder：由合法决定组装硬需求/事实及来源/资格/授权/行动，预算拒绝或整项省略并记账，绑定决策、最终包、route及预算的context ID；非同等先决的行动不交模型改序。长度是UTF-8字节代理，不是token。
- model_adapter/action_ranking：Responses、Chat Completions非流式离线协议；单次fake transport、身份/角色/终态/业务绑定分离；排序限同等候选的合法行动组，拒绝后返回规则。显式依赖注入进入默认与后台render_chat；非真实服务连接，不实现重试或跨仓平台。
- cognition_comparison及知识包：新增HP官方维护条件；低频三年情景及耗材/硒鼓去重、未知值、差价翻转的计算。五组新增测试共17项，无旧测试修改。

## AC执行自检（非独立业务裁定）
| 项 | 执行者证据、限制 |
|---|---|
| AC-01 | 冻结前测27条失败，最终失败列表空；C08/C08_SHORT均停止，C12仅HP彩印待核。候选探针5/5。 |
| AC-02 | VP01与VP04原12案；paired-replay.json中4个实际render_chat规则/注入对照及原家庭view。默认和后台注入可以改变同等行动候选顺序，异常回原首步；仍请独立比较每入口文字及决定。 |
| AC-03 | 删除观察时间保留待核而非淘汰；撤回、冲突、地区、畸形scope及注入回放；保留原564测试。合成干预不是商品事实。 |
| AC-04 | 本包真实新增材料：HP中文用户指南印刷页77–78、139，明确列M232dw，低碳粉警示本身不强制立即更换，质量不可接受才更换；严重不足时高级耗材保护保修结束，不是整机保修结论。接入维护更换条件、回撤测试；截图两次缓存未命中，独立复核待做。无实际售价、实机耗量、故障率或真实用户收益。 |
| AC-05 | 原四案0请求；14组中10组无需模型。4组fake wire分别8278/5890/7710/8278字节，对应旧prompt 15262/15486/15487/15262字节。口径不同，仅表示各自载荷，不是token或成本节省实测。省略账与绑定见paired-replay.json；必需超限、布尔预算等专项。 |
| AC-06 | 17项专项中的适配/排序组覆盖两协议与回退；实际聊天原件见回放。真实HTTP、新API、CLI均0；无实际模型身份/费用的新观测。 |
| AC-07 | 14个配对场景及4个产品入口回放，3个合成合法排序、1个异常回退，10个直接走规则。合法变化仅同等优先候选先后，尚不能证明减少研究成本或更好购买结果。非盲评、非真实推理，增益未证。 |
| AC-08 | 7/7、581/581、17/17；保护2154份内容未变、HEAD与索引匹配；旧失败历史未改。 |

## 冻结命令实际结果
均在仓根WSL Python3执行；路径相对本包：
| ID | 命令 | 退出 | 原件 |
|---|---|---:|---|
| VP01 | python3 -X utf8 本包/VERIFY_BUSINESS.py | 0 | evidence/executor/vp01-final.json |
| VP02 | python3 -X utf8 本包/VERIFY_DELIVERY.py | 0 | vp02-final.stdout.log、stderr.log；17项 |
| VP03 | python3 -X utf8 上包/VERIFY_CANDIDATES.py | 0 | vp03-final.json；5项 |
| VP04 | python3 -X utf8 20261124包/REPLAY_CASES.py | 0 | vp04-final.json；12案 |
| VP05 | python3 -X utf8 -m unittest discover -s tests -q | 0 | vp05-final.stdout.log、stderr.log；581项，51.596秒 |
| VP06 | python3 -X utf8 scripts/audit_model_history_readonly.py --task handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118 | 0 | vp06-final.json；历史6/10完成、3案未尝试、0合格模型输出，旧实验不补签 |
| VP07 | python3 -X utf8 本包/VERIFY_SCOPE.py --phase post | 0 | vp07-final.json；保护2154，变化0 |

原件均在evidence/executor，冻结命令、前测及旧包未修改。预检退出1后实现，phase-a-business/phase-b-business记录修复节点，初次全量581通过；最终优化可选上下文、绑定及首步显示后重跑全部冻结命令。没有删除、放宽或迁移旧断言。

## 预算与检查点
匿名公开查询6/6；读取12/12（含失败及截图），评估预留4次未动。source-attempts.jsonl为本次实际工具回执整理的次序账，未能保留逐次精确时刻，不补造；source-records.json记录新增实际材料及提取定位。官方指南文字可读取，截图不可取；商城精确SKU、随箱页数、其他维护资料仍缺。没有平台API、账号操作、设备操作、交易、模型API、模型CLI、安装、提交或推送。此前4+3失败及更旧模型账不变。

工时：本轮未精确分段计时；已保存命令实测耗时（初次全量60.523秒，最终51.596秒）；不能用墙钟补作有效工时。连续执行早于60小时上限结束，未到12/30/48小时节点；phase-a/phase-b与初版/最终回放作为可接续检查点。前测修复属计划内实现，初次全量通过后集中收敛1轮（上下文可选项、绑定和行动一致性），未启动额外纠错轮；未超3轮。

## 变更与下一责任
VP07列出14份产品变化：知识包1、产品8（claim_gate、confirmed_comparison、cognition_comparison、chat_bridge、decision_actions、context_builder、model_adapter、action_ranking）、新测试5。当前包报告、原件及CURRENT在允许范围内。无跨仓变更。尚待独立评估者复跑及新相邻干预、厂商原文复核、真实家庭效用裁定。真实模型增益、token、延迟、费用均未知。

未来真实模型最小试验候选（尚未授权、未执行）：对missing_time、source_withdrawal各选一个同等优先组，固定已验证provider/model/protocol与预算，每案一次、合计2次；与纯规则对照信息价值及接受/拒绝，禁止自动重试，需负责人另授API权限与具体额度，不能继承旧余额。本包不以此为阻塞。

下一责任唯一为Evaluator；独立按EVALUATION.md给出裁定。