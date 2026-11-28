# 最终交付约定

REPORT.md按工作流标准包含Task ID、Executor status、Baseline HEAD、Workspace snapshot、Changed files、L2 Task Gate、EV-01等原件索引、Impact comparison（Measurement evidence/Before/After/Delta/Guardrail result/Scope caveat）、Iteration ledger、Deviations and unresolved items。逐项对齐AC-01—10，明确完成/部分/未完成；L2未全过不能SUBMITTED_FOR_REVIEW。

COMPARISON.md逐S01—16列B0、B1、新路径、真实操作/观察、成功/失败、限制；不把缺失前测补成假操作，不把纠错收益算作全部新功能。USAGE.md给现有Windows环境的真实启动命令及普通用户操作，含范围/未知、取消、来源、保存恢复和决定说明导出。

evidence/executor/expectations.json在实现前登记16链期望。journeys.json结构schema_version=1、cases=[{id,core,completed,route,expected,before,after,raw_artifacts:[{path,sha256}]}]；route为java_event或bridge_process；核心S01—12。原件必须包含actual输入/请求、实际输出、操作事件和错误，不是只写completed=true。来源受控fixture明确标注，真实来源另账。

generate_summary.py从最终journeys生成summary.json：raw_sha256、generator_sha256、completed、core_completed、java_event_completed、safety_errors；安全错误必须0。固定14/16、12核心、8原生且S02/S03/S08/S09为原生。评估者留出另账不混分母；物料SHA和版本可复算，旧结果保留。

active-sessions.jsonl追加{id,event:start|end,at,label}：工作前记start，离开/结束记end，时区必需，同一ID成对，不能重叠；这是主动工作会话，命令秒数另列，未知缺口报告且当前过程项不通过。process.json含time_accounting_complete、unrecorded_segments、repair_rounds（每轮id/start/end/reason）；不得捏造补账。

operations.jsonl追加{id,event:start|finish,at,kind:public_query|public_read,url,purpose}，finish加result、artifact、sha256；失败同样消耗额度。无公开操作保留空文件并说明0。来源日期/定位/版本/型号地区/证据类型/使用范围在对应artifact，不保存凭证或真实个人资料。

scope、runner三件套、原生Java事件/请求/回执/显示和summary均保留。只在本人显式选择的本机新路径导出决定说明；不外发，不提交推送。最终报告把工程、合成任务、公开事实、真人/模型和交易状态分开。
