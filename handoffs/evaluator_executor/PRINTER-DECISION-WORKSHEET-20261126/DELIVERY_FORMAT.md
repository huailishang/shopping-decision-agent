# 最小交付与可复算格式

所有相对路径以仓根为基准。执行者仅写本包evidence/executor及合同白名单，不覆盖旧包或评估者证据。字段是验收数据格式，不应出现在家庭主结果中。

## 三份交付说明

REPORT.md按AC-01至AC-09及合同阶段逐项核任务、完成/部分/未完成、实际原件及限制；包含标准Task ID、Baseline HEAD、Executor status、L2 Task Gate和每个EV引用。没有L2 PASS不能SUBMITTED_FOR_REVIEW。

COMPARISON.md给共同修复后的规则基线与工作单路径对照，12链分母、8核心、窗口与桥区别、未知/故障/翻转各一案；不把修复收益归给工作单主能力。USAGE.md给现有启动命令、正常界面的新操作、取消/恢复及错误解决；说明新stdin action/payload完整协议和文件schema，不能留下待填示例代替能用命令。

## 任务链原件

`evidence/executor/journeys.json`：

```json
{
  "schema_version": 1,
  "baseline_description": "共同修复后、主改变前的同输入规则路径及原件定位",
  "cases": [{
    "id": "J01",
    "expected": "在执行前登记的行为，最终保留登记原件及SHA",
    "before": {"input": {}, "observation": "实际前测"},
    "after": {"input": {}, "observation": "实际后测"},
    "completed": false,
    "route": "bridge_process",
    "raw_artifacts": [{"path": "仓根相对路径", "sha256": "原件SHA256"}],
    "limitations": "当前完成层次与未完成原因"
  }]
}
```

最终恰含J01—J12；route为bridge_process或java_event。至少6条完成java_event，J02/J07必须完成java_event；每条都要实际原件，不要求原件放进同一大JSON。before/after可以引用单独原件，不允许只写一个成功标签。缺条件时保留真正失败，不改预期来刷分。

`evidence/executor/generate_journeys.py`从原件生成当前摘要，交可重复命令；禁止覆盖旧版。`journey-summary.json`至少有raw_sha256、generator_sha256、completed、core_completed、java_event_completed。SHA按文件原字节。最终评估独立重算，不信任脚本自评或stdout计数。

## 外部操作实时追加账

`operations.jsonl`：每次开始前先写start行，结束追加finish行，不覆盖旧记录。0次也创建空文件并在报告说明0次。

```json
{"event":"start","id":"source-01","kind":"public_read","at":"带时区ISO8601","url":"官方URL","locator":"页/段或查询目标","purpose":"本案决定性缺件","remaining_before":24}
{"event":"finish","id":"source-01","at":"带时区ISO8601","result":"failed或取得内容的限范围结果","artifact":"本包原件路径","sha256":"文件SHA256"}
```

kind仅public_read/public_query；检索和主动读分账，失败仍计数；直接下载/截图/find也是read。每次finish有本地必要原件/失败响应及SHA。不得保存凭证/私人账号资料。具体取得内容的日期/版本/定位与许可限制仍在来源原件中，不用账本替代。

## 主动工时与集中修复

`active-time.json`包含segments（每段start/end/label，时区ISO8601，不重叠）和repair_rounds（id/start/end/reason）。实际主动段总和≤120小时，集中修复轮次≤5。工作中断不计主动时长；所有旧包缺失保持未知，不塞到本轮。阶段检查点记录实际达到位置，未到时可以提前交；不要求虚构整点检查。

## Java检查约定

两份新Java回归main都接收 `python-executable output-directory`。DecisionWorksheetRegression实际调用新桥/旧桥并核语义；DecisionWorksheetSwingRegression在现有窗口触发事件、桥和结果，至少翻转与保存/新进程恢复链，只有全部实际断言完成才打印 `WORKSHEET_NATIVE_PASS`。无显示/未执行返回非0，不能SKIP当PASS。

冻结VERIFY_JAVA先检查新类存在，再在已有Windows Python/JDK21编译全部desktop源码（目标17），依次跑旧桥、旧Swing和两份新回归。执行证据及独立证据分目录，原始输出、argv、精确起止与退出码保留。该标记不是人工/真人验收，评估者仍看原事件与输入/输出。
