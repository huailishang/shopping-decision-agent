# 最小产品接口与数据边界（冻结）

不替换现有聊天状态/工作单，只增加可复核的认知输出和引用绑定。Java不推导专业规则，模型不认证来源。

## 实际读取入口

继续使用 `python -m shopping_decision.chat_bridge --worksheet-stdin`，UTF-8 JSON五字段：

```json
{"schema_version":1,"action":"guide","state":{"此处":"现有合法聊天状态"},"worksheet":null,"payload":{}}
```

上例state是占位说明，实际使用既有new_dialogue/明确确认后的合法状态。至少品类已确认为printer、只给粗用途即可，不要求先建工作单或补扫描/成本。payload恰为{}，不能借guide请求注入自称已审的资料或新的用户答案。输入继续限制256KiB/深度/集合/重复键/版本，沿用旧tab/base64响应。

guide成功返回既有state_json/report_json/result_text/prompt等结果字段，另含三个UTF-8字符串：

1. guide_text：普通用户导览，不要求识别JSON字段/英文参数。
2. cognition_guide_json：可解析下述结构。
3. cognition_context_json：同一当前认知的最小模型消费视图，真实调用仍关闭。

guide是只读：不能改变state答案/版本、创建假成本、确认偏好或授权；不能为了显示指南强迫用户先答一长串专业参数。正常聊天/Java也消费这同一份结构，不是只有guide命令可看。

## cognition_guide_json

- schema_version=1，guide_id/version为非空字符串，category=printer。
- status为ready/partial/unavailable；资料不足时明确partial/unavailable，不得用外观完整代替真实性。
- decision_use=guidance_only，unknowns数组。
- sources数组：至少id/type/url/source_group/captured_on/review_status/limitations；原发布日未知可null但可见，不捏造。来源真实性由取证原件/审查核，不由此字段自证。
- claims数组：至少id/text/source_ids/conditions/exceptions/counter_evidence/evidence_status；evidence_status至少区分supported/pending/conflict，负向/撤回/过期可以更细。
- dimensions数组：至少id/label/why_it_matters/question_field/source_ids/evidence_status；question_field可以null，表示待研究维度而非已确认需求。受支持维度须能追到适用主张/来源，推荐值须有条件/单位，不能凭常识填数。
- routes数组：至少id/label/status/evidence_ids/conditions/limitations；evidence_ids指当前claims中的主张，缺证可为空但须说明unknown。候选路线及待核状态不等于推荐路线/真实型号资格。

至少一个有据正例能解释参数及其影响，不能全unknown刷安全；最终真实来源最小集另由AC-01核，不以本结构字段或数量代替。

## cognition_context_json

schema_version=1，guide_id/guide_version与当前guide一致；至少包含user_confirmed对象、cognition_claims数组、route_basis数组、candidate_facts数组、unknowns数组。本人确认值、品类依据、路线证据、型号事实分别存，不能把一个帖子变成用户要求或当前售价。

主张必须有来源引用和适用条件；未审/冲突/缺证不伪装成已核事实。候选尚未形成时candidate_facts可空；不能为给模型凑上下文编造型号。实际context_builder/ranking路径需按同一绑定消费可用依据，不仅导出一份未使用的JSON。无合法模型任务或必要信息超预算就明确不调用/回退；不得为达标关闭旧注入/回执边界。

## 需求确认与后续动作

继续使用既有显式发送/编辑/暂缓/撤回机制。参考选项只填草稿，本人发送才写确认。至少一个新增使用因素由执行者选定并在USAGE声明字段/类型/单位/未知/撤回语义及依据；复用一个权威状态，不另造第二答案系统。

指南浏览/展开、跳过、来源提案/关联及保存的其余协议由执行者在USAGE具体记录，不能擅改guide五字段或旧协议。用户导入材料默认待审；本机文件的review_status/哈希/作者名/点赞不构成批准。未知schema、旧版本、错绑定、恶意授权和缓存结论拒绝或隔离，保留当前有效会话。

## 保存与版本

可保存输入和必要的guide_id/version/来源引用；恢复必须重算。保存的guide_text、winner、权重、模型排序或授权若存在，不得成为可信结果。新资料版本只失效依赖结果，保留用户明确答案和其他独立事实。旧工作单迁移必须可见，不以清空旧数据解决兼容。
