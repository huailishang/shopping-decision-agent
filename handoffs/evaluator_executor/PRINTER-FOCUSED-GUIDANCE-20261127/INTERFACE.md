# 冻结接口：同一当前认知问题

保留现有--worksheet-stdin五字段请求（schema_version/action/state/worksheet/payload）与tab/base64返回；guide仍可worksheet=null、payload={}读取且不改state。普通render_chat、guide及Java消费同一个guidance_focus_json，不另设第二权威会话。仅向返回字典增加字段；旧客户端可忽略。

guidance_focus_json为UTF-8 JSON对象：
```json
{
  "schema_version": 1,
  "guide_id": "printer-cognition-guide",
  "guide_version": "当前指南摘要",
  "state_version": 2,
  "status": "ask",
  "field": "needs_color",
  "question": "必须在家打印彩色吗？",
  "explanation": "当前为什么先确认这一点",
  "claim_ids": [],
  "source_ids": [],
  "basis_kind": "user_choice",
  "if_unknown": "保持未知，并说明仍能做什么",
  "effect_if_yes": "适用路线如何变化",
  "effect_if_no": "适用路线如何变化",
  "next_step": "本人提交或暂缓",
  "purchase_recommendation_approved": false,
  "transactions_enabled": false
}
```

status精确枚举ask/research/wait/unsupported。ask时field必须是当前可提交的一个原有字段，等于prompt_field；question等于prompt。其它状态field为null，prompt_field为空，不能偷偷要求用户回答隐藏字段。state_version必须等于state.version。guide_version等于cognition_guide_json.version及context引用。若无适用品类仍提供status=unsupported，其guide_id/version可为null。

basis_kind精确枚举user_choice/logical_constraint/supported_claim/unknown。用户自己是否彩色、扫描是选择问题，不能伪造科学来源来认证偏好；某技术性能或路线倾向必须supported_claim且引用当前有效claim/source。无证据用unknown并说明待核，不能因没有source_id将用户选择误判为非法，也不能把真实技术判断全部标user_choice逃审。

explanation是当前一项理由；不得把完整指南复制过来。语义上需让新手知道问题与用途的联系，不以字数设硬门槛刷短。if_unknown总是非空；effect两字段仅布尔字段必须非空，其余可用非空描述替代yes/no的语义；用户回答不确定时不能假设否。

cognition_context_json增加guidance_focus对象，内容与返回focus同源；不得只在UI造显示字段。决定说明增加guidance_focus与为何选择当前问题的可审依据，继续包含来源日期/条件/正反证据/未知/授权false。工作单只能保存输入和guide_reference，不保存可信focus_text或winner。

Java复用现有选购前先看入口；普通主屏短解释与问题直接可见，完整指南与来源按需展开，参考仍只填草稿。取消/旧回执/新会话和schema边界沿用；不是增加新的模型协议。

为了公平测量，B0副本的旧返回可由**同一个测量适配器**读现有prompt_field/prompt/guide/context；适配器只规范字段，不能替A补答案/替B省动作。两臂均可打开相同完整资料。公开补源与共同必要修复须在B1同时供给两臂，不允许通过本包产品代码给A注入新的聚焦策略。
