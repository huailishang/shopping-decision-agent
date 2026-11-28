# 测量先行：只回答真正被问的问题

## 为什么更换测量

旧六组把已知oracle的每个字段依次提交，两组最终都获得相同完备答案，结构上很难检出引导是否帮助需求形成。持平不是认知假设已被否定，也不是已证明有效。新测量不声称合成用户学会，只测实际产品是否给出相关问题、正确保留未知并完成冻结任务目标。

## 三条基线和唯一主变量

B0=BASELINE记录的当前产品脏字节，runtime-baseline.zip可在临时目录重放；HEAD不是B0。A=当前完整指南与直接参数澄清路径，公平保留全部材料、澄清能力和安全约束。B=共同必要修复/同资料后的聚焦解释与问题选择。B1记录两臂共享的来源集、必要修复及SHA；将源升级、修复影响与组织影响分开。不得以A删安全功能、禁提澄清、缩预算制造差异。

初始任务、潜在偏好、回答能力、未知/暂缓策略、时点/地区、可得原始资料、来源状态和最大资源相同。专家可明确一次提供已知条件，两臂同待遇；普通脚本每次仅响应实际界面当前字段。不能“B看了指南所以假定回答更多/更准”。

## 24个开发配对任务

TASK_CASES.json冻结24个场景目标与关键条件族；先把语义回答与参考目标写到evidence/executor/replay-reference-v1.json并计算SHA，之后才改产品。允许细化合法表达，不改任务难度/目标/关键未知。每案保存参考来源和人工推导，不调用被测函数产生参考。任务分为路线选择、候选资格、具体补证三种终点，不能将“有输出”全算成功。

每案最多12轮用户回答、4次完整资料展开、30个产品读调用；单调用30秒。达到目标即停；无当前可回答问题但未达目标记stalled，不能跳过字段遍历答案补全。预算到记incomplete。不计系统等待为真人耗时。

## 事件原件和可重算量

evidence/executor/replays/<case>/<arm>.json包含case_id、arm、baseline_sha256、source_set_sha256、reference_sha256、as_of、goal、事件列表及terminal。事件类型response/answer/read/stop；response必须含实际request、argv、exit_code、stdout_sha256、response_path、response_sha256；原始stdin/stdout落同目录。answer必须紧随可回答response，字段等于response.prompt_field（专家预声明batch例外逐项核），答案逐项来自冻结语义表；一次只提交该字段。state变化必须对应真实请求前后，不得藏有额外apply_turn。

统一从原件重算：
- 目标完成、路线/资格/下一步正确性，引用有效性与安全关键错误。
- 必要因素遗漏、明确未知/暂缓/撤回保真，不能以全unknown逃避可判任务。
- 用户实际回答次数、已经明确后重复询问次数、与冻结目标无关的强制回答次数。
- 额外完整资料展开次数、可见解释量、本机耗时。只作代价描述，不能等价为真人理解/满意度。

每项定义和参考映射提前冻结到reference，不能看到B结果才改“必要”。同行为不同文案只算说明变化，不能当路线效用增益。原始材料可逐项供审，不能只交汇总布尔值。

## 前24小时必须通过的四类测量挑战

CH01 A/A同版本同输入应同任务结论及回答计数（本机耗时可不同）。
CH02 在隔离副本将一次关键问题替换为无关问题，检查器必须检出无效追问/目标不完成；不能仍全绿。
CH03 在首轮请求偷填一个尚未被问的关键答案，检查器必须拒绝该重放，不能将其算低交互收益。
CH04 一臂修改来源集或资源上限，比较必须报incomparable，而非改善/持平。
挑战只在测试副本/测试适配器，不改生产状态。四项均保留原始事件与预期/实际；测量灵敏度失败就不继续产品扩张。

## 效果裁定及阶段停止

## 冻结机器数据约定（先读再实现重放器）

comparisons.json顶层为reference_artifact(path/sha256)、pairs；每对含case_id、basis、a、b。basis精确含as_of、source_set_sha256、reference_sha256、limits，limits等于TASK_CASES.json.limits。a/b各含相同basis、replay(path/sha256)，实际产品源码SHA另记，不要求A/B产品字节相同。

reference文件cases逐项含case_id、initial_state、answer_table、relevant_fields、target。initial_state是本人已明确初始条件，不得含后续尚未被问答案；answer_table每字段为允许的明确答复字符串列表，禁止按实验臂改变答案；relevant_fields是独立目标所需字段。target可包含confirmed对象、deferred/withdrawn字段列表、route(id/status)、next_step_contains，至少一项；复杂候选正反证据仍须Evaluator语义核对，不能只用字符串宣称完整合格。

replay原件含case_id、basis、events、terminal，terminal为completed/stalled/incomplete。response事件字段为request（真实五字段输入）、exit_code、stdout_artifact(path/sha256)、response_artifact(path/sha256，解码后的返回字典)、argv；answer事件为field/answer；read事件记完整资料展开；stop记理由。每answer紧接可回答response，下一request.state应等于该response.state_json经唯一该字段明确答复的结果；脚本不得补额外答案。response本身只读，request.action限guide/create/refresh等当前读操作；恢复/换地区的前置受控步骤另有setup原件与独立参考，不偷偷混入回答计数。

VERIFY_MEASUREMENT从真实stdout复解码并核对response，重算当前问题答复纪律、目标完成与资源数。四类挑战原件还需人工语义核验，机器detected字段不自证。负责人应能从24对原件重算，不只看到硬编码汇总。

## 效果裁定补充

工程提交可如实包含无收益，不能要求24案都赢。项目层IMPROVED的建议证据门槛：安全关键错误0、正确完成不低于A、≥6对在有效目标完成前少至少一次无关/重复回答或补上独立关键遗漏；其余任务不新增强制步骤，所有额外阅读单列。达到该门槛也仅证明这24离线任务，不外推真人。最终由Evaluator按原件判断，不按此数自动签PASS。

48小时找不到至少一条同资料任务层信号时只允许一轮局部纠错，再无信号停；不做后续装饰。低样本/不独立/参考有争议时记INCONCLUSIVE，不用显著性或ROI假精确解释。另8个Evaluator独立留出与24对、12链分开。
