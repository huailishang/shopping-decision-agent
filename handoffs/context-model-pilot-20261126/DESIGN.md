# 负责人方向验证：Context / Model Adapter / 程序与模型分工（2026-11-26）

状态：独立离线候选原型，非上一冻结任务的验收、续修或新正式执行合同；原 CURRENT 路由、旧预算和失败账不变。本目录是新增候选证据，不追认原范围检查。请 Evaluator 合并审查本候选及原任务，确认后再接产品入口。零新增模型 API，零账号操作、购买、提交推送。

## 参考对照（2026-11-26）
- 本机 agent-runtime-platform：AGENTS.md、docs/platform.md、backend/context/builder.py、packet.py、ledger.py。已有任务/会话/回忆/计划/记忆/工件/MCP/技能/运行上下文装配、遗漏登记及估算。现有 ledger 使用 chars/4 粗估；不能当精确厂商 tokenizer。采用现有 ContextPacket/ContextLedger 边界，不新建控制平面。Platform 至少两个真实消费者同构后才抽公共层。
- DeepSeek Harness 官方： https://deepseek-harness.github.io/deepseek-harness/en/reference/cookbook/adding-an-llm-adapter ，https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/llm/llm/README.md ，https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/compaction/compaction-basic/README.md 。参考 provider+model 路由、resolveModel 能力声明、单尝试 adapter、独立重试、按模型容量和预留输出管理上下文；不复制源码、不引入第二套 agent loop。参考为当日文档，未锁定上游 commit。
- 本仓 shopping_decision/evidence_comparison.py 已有 rule_comparison/validate_model_result，昨日完整案例要求 2*14=28 行模型复算；C12 实际 4757 输入、8192 输出、仅 reasoning。HTTP 400 无错误体，不能认定为超上下文。原短案仍失败，说明需要独立协议预检。

## 目标分层
1. Domain：用户确认需求、商品证据、资格、预算、单位、时效、冲突、成本公式及有效行动候选由本仓/权威来源决定；原始证据与绑定保持本地。
2. Context：按当前任务、候选资格、差异、缺失和风险选择数据。硬约束、决定性反证、授权不得静默删除；可选项整条省略并记录 ID、哈希、原因。保留版本/来源引用；需要长对话压缩时另行使用可追溯摘要，原始历史不删。最终 wire 请求也校验预算；超限 fail closed，不盲目重试。上下文窗口和输出预算从已核实的具体 route 解析；按需保留 reasoning 和最终答案空间。真实 tokenizer/厂商 usage 用于校准，当前 byte proxy 不是 token 数。
3. Model Adapter：逻辑入口 provider/model/protocol + capabilities（窗口、最大输出、支持的推理参数、结构化输出/流式/工具等）。映射协议、序列化、传输、响应解析、事件归一各自隔离。首版离线 payload 编译和 responses/chat_completions 非流式归一；参数必须是具体 route 经核实的配置，不猜厂商默认值。CLI/manual/streaming 是候选 adapter，非当前已实现。HTTP 状态、应用错误、finish_reason、实际模型、usage、attempt id 和原始响应哈希分别保全；完整文本后还要过业务 schema 与证据校验。401/403、400、明确 context limit、429、5xx、timeout、malformed、output_limit、no_final_answer 分开；429 不能一概称额度耗尽。重试/切模型由 Harness 决策，预先批准次数与总预算、每次记账；未知是否执行不得盲目重发。真实配置与凭据由本机管理，不进上下文/日志。
4. Model：开放性任务优先挑选下一项信息增益、比较取舍、解释用户适用条件，不再复算矩阵。当前候选只实现对允许的行动 ID 排序；不允许模型改变硬条件、事实、资格、权限。更开放的取舍建议可作为内部提案（带 fact/claim IDs、适用条件、反证），须独立验证语义及价值，未通过不公开。不可因候选被淘汰仍研究其扫描；两款均淘汰直接寻找替代，不调用模型。
5. Harness Gate：按输入 hash 和 context id 绑定，未知/重复 action ID、过期会话、额外自由文本拒绝，返回原程序持有的行动。正式接入需有规则回退、独立评估、审计、原正常聊天与公开门禁一致性验证。模型输出不直接发布或执行。

## 本地候选
- runtime_contract.py：通用 ModelRoute、最小上下文包、遗漏 ledger、两类非流式 payload、响应分类；无 HTTP transport/credential/retry。
- shopping_projection.py：消费原 rule_comparison，硬要求和资格不可变，候选行动仅来自未淘汰候选的未知/冲突，必要时优先硬约束；只接受 action IDs，未调用真实模型。全量矩阵留本地。所有候选淘汰或无开放行动不产生 payload。
- test_pilot.py：使用原冻结 C01/C08/C12/C08_SHORT 只读输入，另有合成异常夹具。执行：PYTHONPATH=. python3 -X utf8 handoffs/context-model-pilot-20261126/test_pilot.py
- 初始目标（实验）：以 4500 UTF-8 字节作保守 wire 上限，512 输出 token 配置，512 headroom；fixture route 16000 context/2048 output 仅为测试假设，不是魔搭真实容量。真实上线改用 adapter 提供的精确/校准 meter，并按模型推理预算配置，先短问答/JSON，后业务。

## 复核门槛
- 独立核查原四案输入、旧提示词 vs 新完整 wire 字节、是否丢决定性反证；字节与 token 区分。
- 新旧规则/普通入口与通用发布结果回归；确认原候选行动排序缺口是否在真实 render_chat 复现。
- 测无证据、冲突、撤回、改答、注入、输入超预算、输出耗尽、无最终文本、模型错配、非法 action ID。
- 真模型另立有限预算：先核对具体 provider/model/protocol、账户可用性与错误体，再短问答、短 JSON、代表性业务；不把结构成功当实际增益。按同输入比较规则路径和模型路径的高价值行动排序、有效答案率、实际 token、耗时及成本。
- 第二消费者（个人智能体等）确有同构契约后，将通用部分映射到既有 Platform ContextBuilder/ContextLedger、模型 registry 和 Harness budget/trace。购物专有规则、证据和动作门禁留领域。不得在正在修改的 Platform/Personal 仓库直接落新代码。

## 限制
这是一份可运行的局部候选而非产品修复完成。没有接真实 HTTP、现有 chat/public gate、真实模型 tokenizer、长期会话压缩、配置中心、正式评估或第二消费者。原任务 CURRENT 不改，避免破坏原待评审快照；请评估者明确将本目录纳入新授权范围后再冻结并迁移。未覆盖原历史失败。
