# 模型横向补测交付（2026-11-25）

负责人新增授权，沿用原本机魔搭配置与 Responses 接口。原合同4/4次尝试不重置、不追认；另计本次3/3次，未购买、充值或扩大到其他凭据，未调用商汤（当前项目指定配置及环境中未发现）。模型目录只读查询HTTP 200，返回38项，未返回账户额度头；不能据此判断实际剩余额度或免费额度是否用完。

## 同输入结果
| 模型 | 结果 | 实际证据 |
|---|---|---|
| ZhipuAI/GLM-4.7-Flash | 拒绝 | 原始82字节JSON，应用code=500、success=false、无output；原始哈希匹配。初版脚本终态写入与排他创建冲突，HTTP状态和精确耗时未保存；按原始响应重建终态，非伪造原始回执。 |
| Qwen/Qwen3.5-27B | 拒绝 | transport TimeoutError，80.593秒，无完整响应；服务器是否完成推理及用量未知。 |
| deepseek-ai/DeepSeek-V4.1-Flash | 拒绝 | HTTP 400，0.717秒，未保存错误响应体，具体拒绝原因未知。 |

三份输入与提示词哈希一致：input a0910482b7e6f6c8cc8b33e71f620c816b1d6dc9f96a5c2408bb3bb7af1fbbd1；prompt 4e8d114601f03e479d2416f7902d998a6827cab609ad33114b3b99c1afdcdfbe。基于C08原冻结案例的扫描、彩印、小程序三个维度子集，非全量用例。规则在该控制案中正确将两款因明确彩印反证排除；HP扫描及小程序为met，Brother为unknown。此为既有输入内结论，不另作厂家核源。三次均无可进入结构校验的最终答案，不评模型决策增益。不能把这些失败定性为账户额度耗尽，也不能据单次失败判定模型永久不可用。原4次+新增3次=7次，0次合格业务输出。

## 证据和范围
各模型 request.json、request-payload.json、rule-result.json、rule-public.json、meta.json、terminal.json 在本目录各子目录，GLM原始响应在Git忽略的data/private/modelscope。保留run_supplement.py初版及run_supplement_v2.py修订版（终态另存terminal.json，处理应用错误）。未修改产品代码、冻结输入或冻结检查器。原564/564为上次实跑，本次未重跑全量。

本次 VERIFY_SCOPE.py --phase post 退出1：changed_protected_paths 仅包含 MODEL_RESUME.md 与 MODEL_SUPPLEMENT_SCOPE.md（均为负责人续执行的新增说明文件，冻结检查器把新增文件计作范围外）；其余2017份基线检查未列出原有保护文件变化，HEAD、索引、清单校验、必要产品文件均通过。不得写成本次范围检查PASS；请评估者独立核实两份新增文件及授权，裁定范围门禁。无提交推送。

## 建议交接
保持原READY_FOR_REVIEW，模型支线尚未达成。建议评估者区分连接/协议兼容性、模型推理资源及决策价值；如另立模型实验，先确认账户真实额度、模型支持的接口和短输出，再做代表性同输入验证；不把原失败尝试从账本删除。