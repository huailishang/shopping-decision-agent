# 交付格式：不能只交一份指南或成本表

REPORT.md沿标准模板含Task ID、Executor status、Baseline HEAD、Workspace snapshot、Changed files、L2 Task Gate及EV原件索引、Impact comparison（Measurement evidence/Before/After/Delta/Guardrail result/Scope caveat）、Iteration ledger、Deviations and unresolved items。逐阶段/AC对账完成/部分/未完成；L2未过不能SUBMITTED_FOR_REVIEW。真实认知来源不足单列，不用工程绿代替。

USAGE.md给现有环境真实启动命令和新手实际操作：粗需求→指南→看来源/参数→确认/暂缓/撤回→路线/候选→补证/情景→保存恢复/决定说明。声明新增使用因素字段/类型和其依据、其余协议、跳过路径；用户不需要读JSON。COMPARISON.md给20链、至少6对公平A/B、B0/B1和新增资料/认知组织/纠错分账，无增益与退化均保留。

evidence/executor/expectations.json在实现前登记G01—20期望。journeys.json={schema_version:1,cases:[{id,core,completed,route,expected,before,after,raw_artifacts:[{path,sha256}]}]}。route仅java_event/bridge_process。核心G01—14，≥18/20、14核心全过、8原生；G01/G05/G13/G14必须原生。原件含实际事件/请求/回执/显示与错误，不能只写completed=true。独立留出另账。

generate_summary.py从最终journeys生成summary.json：raw_sha256、generator_sha256、completed、core_completed、java_event_completed、safety_errors（0）。每个raw_artifacts必须仓内真实路径与字节SHA，产品/生成器/资料版本可回溯；旧版保留。

source-claims.json={schema_version:1,claims:[{id,text,source_ids,conditions,exceptions,counter_evidence,evidence_status,raw_artifacts}],sources:[{id,type,source_group,url,published_on,captured_on,locator,limitations,raw_artifacts}]}。真实来源至少3条supported主张、2组，含技术/官方和独立专业比较方法/试验；每条supported均有对应原件。字段/数量是完整性检查，真实性/适用性/允许用途须独立核。合成资料不放入真实来源分母；必要摘录/本地受审引用可复用，不能伪造新获取日期。

该交付清单的source.type采用可审查的用途标签：技术/原始组可为standard、standard_register、technical_reference、manufacturer、manufacturer_document、official_exact_model_document或official_technical_document；专业方法/试验组可为professional_review、independent_test、independent_laboratory、independent_comparison_method、consumer_comparison、regional_comparison或independent_consumer_test_method。这只是归类，不自动升级真实性；原来源自己的类型/范围保留在原件。

comparisons.json={schema_version:1,pairs:[{id,basis:{initial_request_sha256,source_set_sha256,user_profile_sha256,as_of},a:{basis,output,raw_artifacts},b:{basis,output,raw_artifacts},reference_artifacts,outcome,limitations}]}。至少6对，两臂basis与共同basis相同；outcome为improved/equal/regressed/inconclusive。参考来自资料/独立判断，不能自评输出生成；合成回答脚本明确标注，至少有equal或无净收益记录，不能强迫制造退化来凑数。若观察到退化/故障须如实保留。

active-sessions.jsonl追加{id,event:start|end,at,label}，工作前start、结束/离开end、带时区、不重叠。process.json含time_accounting_complete、unrecorded_segments、repair_rounds每轮id/start/end/reason（≤6），consumed_predecessor_active_seconds（非负，按已发现实际记录；未发现0并说明核查）。完整主动≤180小时，命令时长另列；未知段保留且过程项不能通过。

operations.jsonl追加start/finish，含id/at/kind(public_read|public_query)/url/purpose，finish有result/artifact/sha256。失败也计次；无操作空文件写0说明。执行读≤32、查询≤12、同URL同定位失败≤2；来源记录标发表/获取日期、版本、型号/地区/样本、必要摘录和用途。不存凭证/真实个人资料。

决定说明从当前同源结构生成，本人预览后选择本机新路径，不上传/外发。原生Java事件证据、scope/runner三件套、来源原件、实际产品上下文必须有。把资料/规则、模拟回执、程序化窗口、真人理解、真实模型质量和交易状态分开报告。

新增CognitionGuideRegression/CognitionGuideSwingRegression接受args[0]=既有Python绝对路径、args[1]=本包证据输出目录；后者必须实际事件与断言全过才打印COGNITION_GUIDE_NATIVE_PASS，不可用SKIP。事件、请求/回执、显示和每条完整链证据写入该目录。旧四组桥/窗口回归也必须真实执行。
