"""Freeze preparation and publish the sole next-task route, without product edits."""
from pathlib import Path
import hashlib,json,subprocess,sys,importlib.util
from datetime import datetime,timezone
E=Path(__file__).resolve().parent;TASK=E.parents[1];ROOT=TASK.parents[2];REL=TASK.relative_to(ROOT).as_posix()
old=ROOT/'handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126'
skill=Path('C:/Users/HuailiShang/.codex/skills/evaluator-executor-workflow')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((old/'evidence/evaluator/review-snapshot.json').read_text(encoding='utf8'))
unchanged=all((sha(ROOT/p) if (ROOT/p).is_file() else None)==h for p,h in before['product_sha256'].items())
if not unchanged:raise SystemExit('unexpected evaluator product edit')
plan_module=skill/'scripts/run_validation.py'
spec=importlib.util.spec_from_file_location('frozen_validation_runner',plan_module);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
plans={mode:len(module.load_plan(ROOT,TASK/'VALIDATION_PLAN.yaml',mode=mode)[1]) for mode in ('executor','evaluator')}
if plans!={'executor':12,'evaluator':12}:raise SystemExit('plan mismatch')
pre=json.loads((TASK/'preparation/preflight.json').read_text(encoding='utf8'))
if pre['status']!='EXPECTED_FAILURES_CONFIRMED':raise SystemExit('preflight not confirmed')
freeze=subprocess.run([sys.executable,'-X','utf8',str(TASK/'VERIFY_SCOPE.py'),'--phase','freeze'],cwd=ROOT,capture_output=True)
(E/'freeze.stdout.txt').write_bytes(freeze.stdout);(E/'freeze.stderr.txt').write_bytes(freeze.stderr)
if freeze.returncode:raise SystemExit('freeze failed; preserve original receipt')
digest=sha(TASK/'BASELINE.json')
router=f'''# 当前状态（2026-11-26，独立评估完成，下一长包已冻结）

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: PRINTER-DECISIVE-EVIDENCE-20261126
task_kind: capability_experiment
state: CONTRACT_FROZEN
current_role: Executor
next_role: Executor
mandatory_gate_status: NOT_RUN
preparation_status: EXPECTED_FAILURES_CONFIRMED
baseline_commit: c226f4e0c156e5d2bd1f6f19aaeb448e9979f73f
baseline_path: {REL}/BASELINE.json
baseline_sha256: {digest}
project_map_path: docs/PROJECT_BOTTLENECK_MAP_CURRENT.md
project_map_revision: r42
active_bottleneck_id: B05
hypothesis_id: H-B05-DECISIVE-EVIDENCE-01
contract_path: {REL}/CONTRACT.md
validation_plan_path: {REL}/VALIDATION_PLAN.yaml
executor_report_path: {REL}/REPORT.md
evaluator_review_path: {REL}/REVIEW.md
next_artifact_path: {REL}/REPORT.md
previous_task_reassessment_path: handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126/REVIEW.md
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_existing_local_model_cli: false
authorization_platform_business_api: false
authorization_public_research: true
public_query_limit: 10
public_read_limit_total: 32
public_read_limit_executor: 24
public_read_limit_evaluator: 8
new_model_inference_limit: 0
effective_hour_limit: 180
concentrated_repair_round_limit: 6
```

## 最新独立裁定

上包PRINTER-DECISION-WORKSHEET-20261126正式 **REJECTED**；本机任务能力 **IMPROVED**。独立原9项L3实际8通过1范围失败；全量657/657、工作单专项33/33、原12案例与历史审计通过。Windows6条实际事件链通过，编辑/翻转/保存/新进程恢复/取消/错误恢复/地区失效有实证，不等于真人收益。

独立复合留出4/5。反例：只把HP维护假设0改100，Brother/HP总额700/650变为700/750，偏好正确转Brother，但下一步固定核Brother随箱量/耗材，错过决定性HP维护。主动工时首轮缺口不可追补；原范围FAIL不追认。R4两文件精确差异及历史锚点独立10项通过，明确允许后续新包继承；原合同/基线/失败账不改。

正式[评审](handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126/REVIEW.md)、[独立门禁](handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126/evidence/evaluator/l3-independent/L3-GATE.md)、[关键反例](handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126/evidence/evaluator/holdouts-v2/maintenance-flip.json)。历史完整入口快照在上包evidence/evaluator/CURRENT.before-routing.md；旧模型6次安排/结束、0接受、3案缺测和所有旧拒绝保持。

## 唯一当前执行入口

Executor读取[START_HERE]({REL}/START_HERE.md)、[完整合同]({REL}/CONTRACT.md)、[独立验收]({REL}/EVALUATION.md)、[12项计划]({REL}/VALIDATION_PLAN.yaml)、[交付格式]({REL}/DELIVERY_FORMAT.md)及[r42地图](docs/PROJECT_BOTTLENECK_MAP_CURRENT.md)。先记录活动session start、核新BASELINE再开工，不清理全部未提交成果。

单一主改变：在现有工作单上做关键假设分析和同源最小补证行动，贯通精确翻转/条件范围、原生窗口、来源失效、保存恢复及本地决定说明。先合修维护/主机价行动，B0→B1纠错与B1→新闭环收益分开；不建第二引擎/应用，不扩真实品类。

连续上限 **180有效小时、6轮集中纠错**，累计8/24/48/72/104/136/164/180小时检查点；目标达到提前交，各阶段不等批准。固定16链≥14且12核心全过，至少8原生窗口链，维护/随箱阶跃/恢复/来源撤回必须窗口；评估者另6复合留出不混分母。单分析最多4096次成本求值，不能把端点抽样称全范围稳定。

[真实前测]({REL}/preparation/preflight.json)：承接行动3项1过2失败；新分析7组尚不满足、五组新测试/两份Java/交付缺失均实际exit1。它们是待做任务，不是实现完成。新范围明确包含最小当前Java精确版本审计兼容，旧历史锚点与原件继续保护。

匿名查询≤10、执行读取≤24、评估预留8；缺外部材料继续离线主线，保留未知。模型API/CLI、平台业务API、账号/设备/交易、安装/外发、Git提交推送/索引均0。真实微信持续使用、实际耗材/维护费用、河南有效价、真人/真实模型效果仍未证。交REPORT/COMPARISON/USAGE和真实原件后由Evaluator独立裁定。

## 历史冻结标识（只读历史，不代表新授权）

Frozen inputs SHA-256: 1aff6672167e01bd13d8b845097d3834f66c3868806543e7429fb24744fb60b5
'''
(ROOT/'CURRENT.md').write_text(router,encoding='utf8')
start=subprocess.run([sys.executable,'-X','utf8',str(TASK/'VERIFY_SCOPE.py'),'--phase','start'],cwd=ROOT,capture_output=True)
(E/'start.stdout.txt').write_bytes(start.stdout);(E/'start.stderr.txt').write_bytes(start.stderr)
validator=subprocess.run([sys.executable,'-X','utf8',str(skill/'scripts/validate_workflow.py'),'--repo',str(ROOT),'--current','CURRENT.md'],cwd=ROOT,capture_output=True)
(E/'workflow.stdout.txt').write_bytes(validator.stdout);(E/'workflow.stderr.txt').write_bytes(validator.stderr)
receipt={'at':datetime.now(timezone.utc).isoformat(),'baseline_sha256':digest,'protected_count':len(json.loads((TASK/'BASELINE.json').read_text())['protected_files_sha256']),'plans':plans,'preparation':pre['status'],'scope_start_exit_code':start.returncode,'workflow_exit_code':validator.returncode,'product_bytes_unchanged_by_evaluator':unchanged,'current_sha256':sha(ROOT/'CURRENT.md'),'previous_review_sha256':sha(old/'REVIEW.md'),'old_gate_result':'FAIL (preserved)','new_task_state':'CONTRACT_FROZEN / Executor','commit_push_model_api_transaction_calls':0}
(E/'freeze-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False,indent=2));print(validator.stdout.decode('utf8',errors='replace'))
raise SystemExit(int(bool(start.returncode or validator.returncode)))
