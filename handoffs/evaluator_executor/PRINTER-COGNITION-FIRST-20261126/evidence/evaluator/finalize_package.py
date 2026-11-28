"""Validate first, then freeze once and route the complete cognition-first task."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
from datetime import datetime,timezone
E=Path(__file__).resolve().parent;TASK=E.parents[1];ROOT=TASK.parents[2];REL=TASK.relative_to(ROOT).as_posix()
skill=Path('C:/Users/HuailiShang/.codex/skills/evaluator-executor-workflow')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def run(label,argv):
    start=datetime.now(timezone.utc).isoformat();r=subprocess.run(argv,cwd=ROOT,capture_output=True)
    (E/(label+'.stdout.txt')).write_bytes(r.stdout);(E/(label+'.stderr.txt')).write_bytes(r.stderr)
    (E/(label+'.meta.json')).write_text(json.dumps({'argv':argv,'start':start,'end':datetime.now(timezone.utc).isoformat(),'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()},ensure_ascii=False,indent=2),encoding='utf8')
    if r.returncode:print(r.stdout.decode('utf8',errors='replace'));print(r.stderr.decode('utf8',errors='replace'));raise SystemExit(label+' failed; preserve receipts')
    return r
pre=json.loads((TASK/'preparation/preflight.json').read_text(encoding='utf8'))
assert pre['status']=='EXPECTED_FAILURES_CONFIRMED' and pre['workflow_draft_exit_code']==0
spec=importlib.util.spec_from_file_location('frozen_plan_runner',skill/'scripts/run_validation.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
plans={mode:len(m.load_plan(ROOT,TASK/'VALIDATION_PLAN.yaml',mode=mode)[1]) for mode in ('executor','evaluator')};assert plans=={'executor':13,'evaluator':13}
old=ROOT/'handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126'
oldbase=json.loads((old/'BASELINE.R1.json').read_text(encoding='utf8'))
unchanged=all(sha(ROOT/p)==h for p,h in oldbase['product_sha256'].items());assert unchanged,'product edit during evaluator planning'
snapshot={'at':datetime.now(timezone.utc).isoformat(),'product_sha256':{p:sha(ROOT/p) for p in oldbase['product_sha256']},'git_status':subprocess.check_output(['git','--no-optional-locks','status','--short'],cwd=ROOT).decode(),'predecessor_baseline_sha256':sha(old/'BASELINE.R1.json')}
(E/'product-inheritance.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf8')
run('workflow-before-freeze',[sys.executable,'-X','utf8',str(skill/'scripts/validate_workflow.py'),'--repo',str(ROOT),'--current','CURRENT.md'])
run('freeze',[sys.executable,'-X','utf8',str(TASK/'VERIFY_SCOPE.py'),'--phase','freeze'])
digest=sha(TASK/'BASELINE.json')
router=f'''# 当前状态（2026-11-26，认知优先执行包已重排并冻结）

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: PRINTER-COGNITION-FIRST-20261126
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
project_map_revision: r43
active_bottleneck_id: B05
hypothesis_id: H-B05-COGNITION-FIRST-01
contract_path: {REL}/CONTRACT.md
validation_plan_path: {REL}/VALIDATION_PLAN.yaml
executor_report_path: {REL}/REPORT.md
evaluator_review_path: {REL}/REVIEW.md
next_artifact_path: {REL}/REPORT.md
previous_task_reassessment_path: handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126/REVIEW.md
superseded_execution_task_id: PRINTER-DECISIVE-EVIDENCE-20261126
supersession_record_path: handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126/evidence/evaluator/SUPERSEDED_BY_COGNITION_FIRST.md
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_existing_local_model_cli: false
authorization_platform_business_api: false
authorization_public_research: true
public_query_limit: 12
public_read_limit_total: 44
public_read_limit_executor: 32
public_read_limit_evaluator: 12
new_model_inference_limit: 0
effective_hour_limit: 180
concentrated_repair_round_limit: 6
```

## 用户纠偏与唯一新入口

用户要求先把高质量资料转成小白可理解的品类认知和选购参数参考，再由本人确认需求，让模型/规则有依据地比较。原PRINTER-DECISIVE-EVIDENCE-20261126从既定维度/两型号开始，遗漏认知前置验收，已撤换执行入口；旧合同/BASELINE.R1/前测及全部证据保留，不判虚构执行失败、不追认PASS、不与本包180小时叠加。

Executor先读[START_HERE]({REL}/START_HERE.md)、[完整合同]({REL}/CONTRACT.md)、[接口]({REL}/INTERFACE.md)、[独立验收]({REL}/EVALUATION.md)、[13项计划]({REL}/VALIDATION_PLAN.yaml)、[交付]({REL}/DELIVERY_FORMAT.md)、[范围映射]({REL}/SCOPE_CROSSWALK.md)及[r43地图](docs/PROJECT_BOTTLENECK_MAP_CURRENT.md)。[重排判断]({REL}/ASSESSMENT.md)解释为何改变主线。先记活动start、核新BASELINE再开工，不清理已有未提交成果。

主线：**初步用途→适用高质量资料→技术路线/小白指南/参数参考→本人确认/暂缓/撤回→路线/适用候选比较→关键缺件/个人情景→来源失效/恢复重算→本地决定说明**。认知依据必须改变实际追问/路线/比较或研究任务，不是附加静态百科。专业/厂家/帖子/型号事实/实价/用户授权分层，不能靠热度、review_status或模型自评认证。

原维护/主机价/随箱行动反例合并到下游阶段F；通用多变量范围引擎和analyze_uncertainty独立协议暂缓，不再强制。已有两型号只作研究样本，不绑死所有用户；不新增真实品类/型号或第二应用/引擎。

## 长包边界与验收

替代总上限 **180有效小时、6轮集中纠错**；第8小时粗结果，累计16/40/64/88/108/132/152/172/180小时可接续检查点，阶段连续不等批准，目标达到提前交。真实认知至少3主张/2独立来源组，含技术/官方原始资料与专业比较方法/独立测试；不拿合成/广告/转载凑真实来源。无合格资料可交工程但来源业务项不能PASS。

固定20链≥18、14核心全过、8条Java实际事件链，G01/G05/G13/G14必须窗口；至少6对同资料公平A/B，另6独立复合留出不混分母。修复、资料增量、认知组织收益分开；合成回答不证明小白学会，受控回执不证明真实模型质量。

新增guide真实stdin和正常聊天同源，返回小白导览/参数参考及当前认知上下文；浏览不修改用户答案。模型消费必须含认知主张/来源/条件/反证、本人确认、路线/型号事实和未知，现有硬条件/回执护栏不放宽；真实模型API/CLI仍0。

## 真实准备与历史依据

[前测]({REL}/preparation/preflight.json)6类检查实际exit1：guide三项1过2失败、上下文两项0过、新五组测试缺失、承接行动3项1过2失败、新两份Java缺失、交付未实现。这些是待做目标，不是完成。标准工作流在冻结前已OK，两角色可解析13项计划；实际产品字节未由本轮Evaluator改变。

撤换前旧scope start的3588保护件/产品/HEAD/索引匹配，未见executor目录；发现实际消耗须扣除，不重置额度。旧WORKSHEET正式[REJECTED](handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126/REVIEW.md)及657/33专项/6原生工程成果按历史解释，旧L3 8/9、维护行动/主动工时缺口不抹。历史模型6次安排/结束、0接受、C05/C06/C07未尝试和所有旧拒绝保持。

公开查询≤12、执行读取≤32、独立预留12；失败实时计账，同URL同定位失败≤2。缺外部材料继续本机链，但不能伪造真实认知通过。模型/API、平台业务API、账号/设备/交易、安装/外发、Git提交推送/索引全0。微信持续复用、实际产量/维护费、河南有效价、真人/真实模型收益仍未证。

交REPORT/COMPARISON/USAGE、来源/20链/公平对照/真实上下文/窗口原件及完整活动/外部账，再由Evaluator独立裁定。未过完整L2保持EXECUTING，不自签PASS。

Frozen inputs SHA-256: 1aff6672167e01bd13d8b845097d3834f66c3868806543e7429fb24744fb60b5
'''
(ROOT/'CURRENT.md').write_text(router,encoding='utf8')
run('start',[sys.executable,'-X','utf8',str(TASK/'VERIFY_SCOPE.py'),'--phase','start'])
run('workflow-final',[sys.executable,'-X','utf8',str(skill/'scripts/validate_workflow.py'),'--repo',str(ROOT),'--current','CURRENT.md'])
assert all(sha(ROOT/p)==h for p,h in oldbase['product_sha256'].items())
receipt={'at':datetime.now(timezone.utc).isoformat(),'task_id':TASK.name,'baseline_sha256':digest,'protected_count':len(json.loads((TASK/'BASELINE.json').read_text(encoding='utf8'))['protected_files_sha256']),'plans':plans,'preparation':'EXPECTED_FAILURES_CONFIRMED','scope_start_exit_code':0,'workflow_exit_code':0,'product_bytes_unchanged_by_evaluator':True,'current_sha256':sha(ROOT/'CURRENT.md'),'state':'CONTRACT_FROZEN / Executor','superseded_task':old.name,'real_public_reads_model_api_cli_platform_transactions_git_commit_push':0}
(E/'freeze-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt,ensure_ascii=False,indent=2))
