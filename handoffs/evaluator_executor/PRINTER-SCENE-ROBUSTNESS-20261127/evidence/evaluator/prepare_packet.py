"""Evaluator preparation only: freeze references, plan and inherited byte scope."""
from pathlib import Path
import hashlib,json,subprocess
TASK=Path(__file__).resolve().parents[2];ROOT=TASK.parents[2];OLD=ROOT/'handoffs/evaluator_executor/PRINTER-FOCUSED-GUIDANCE-20261127'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
rows=[
 ('P01','把老人手写的旧家谱变成电脑文件','requires_scan'),
 ('P02','两面都要印，家人不会自己翻纸','requires_auto_duplex'),
 ('P03','暑假结束后收柜子里，到寒假才用','idle_weeks_pattern'),
 ('P04','想把纸质合同转成PDF，在电脑留一份','requires_scan'),
 ('P05','纸的正反两页都得印，不想中途拿出来重放','requires_auto_duplex'),
 ('P06','出差一两个月，回来才打几张','idle_weeks_pattern'),
 ('P07','手机微信里的文件要直接发给机器','wechat_required'),
 ('P08','预算只买机器，耗材以后另算','budget_scope'),
 ('P09','买机器的钱和后续耗材得一起考虑','budget_scope'),
 ('P10','手头没打印任务，先比较放着','monthly_pages_range'),
 ('P11','每月大约就十几张','monthly_pages_range'),
 ('P12','彩色部分拿到店里打，家里只印文字','needs_color'),
 ('N01','不用扫描，最在意纸的两面能由机器处理','requires_auto_duplex'),
 ('N02','不用自动双面，只想把老照片转成电子文件','requires_scan'),
 ('N03','不需要微信，小孩作业想让机器自己翻纸','requires_auto_duplex'),
 ('N04','不考虑预算范围，主要把纸质票据变成PDF','requires_scan'),
 ('N05','页数还不清楚，主要怕几个月不动后恢复困难','idle_weeks_pattern'),
 ('N06','我说的存档是打印纸放文件夹，不是转电子文件；必须自动翻纸','requires_auto_duplex'),
 ('A01','扫描或打印都可能，先看看能做什么','requires_scan'),
 ('A02','给家里用，没想好任务','needs_color'),
 ('A03','朋友说闲置坏得快但我还不知道用法','idle_weeks_pattern'),
 ('A04','主机和耗材怎样比较，我还没定预算','budget_scope'),
 ('A05','微信也许方便，但不一定非要','wechat_required'),
 ('A06','照片需要彩色吗，我还不确定是不是自己印','needs_color')]
save(TASK/'SCENARIOS.json',dict(schema_version=1,reference_basis='Evaluator independent user-goal interpretation, not product outputs. Negated topic must not displace affirmative purpose; no topic inference is a confirmed answer.',cases=[dict(id=i,kind='positive' if i[0]=='P' else 'negation' if i[0]=='N' else 'ambiguous',usage=u,allowed_fields=[f]) for i,u,f in rows],limitations=['disclosed regressions and development fixtures, not blind evaluation','A cases ask a clarification only; no requirement may be auto-confirmed','additional 8 Evaluator cases constructed after implementation']))
native=(OLD/'VERIFY_NATIVE.py').read_text(encoding='utf8')
native=native.replace("'FocusGuidanceSwingRegression.java']","'FocusGuidanceSwingRegression.java','SceneRobustnessRegression.java','SceneRobustnessSwingRegression.java']")
native=native.replace("'FocusGuidanceSwingRegression']:","'FocusGuidanceSwingRegression','SceneRobustnessRegression','SceneRobustnessSwingRegression']:")
native=native.replace("('Decision','Cognition','Focus')","('Decision','Cognition','Focus','Scene')")
native=native.replace("    commands.append(","    if label=='SceneRobustnessSwingRegression':passed=passed and b'SCENE_ROBUSTNESS_NATIVE_PASS' in stdout\n    commands.append(")
(TASK/'VERIFY_NATIVE.py').write_text(native,encoding='utf8')
prefix=['env','PYTHONPATH=.:tests','python3','-X','utf8'];rel=TASK.relative_to(ROOT).as_posix();old=OLD.relative_to(ROOT).as_posix()
specs=[
 ('VP-01',['AC-05'],[f'{rel}/VERIFY_PACKET.py','scope']),
 ('VP-02',['AC-01'],[f'{rel}/VERIFY_SCENARIOS.py','--role','executor']),
 ('VP-03',['AC-02'],[f'{rel}/VERIFY_PACKET.py','controls']),
 ('VP-04',['AC-01','AC-04'],['-m','unittest','discover','-s','tests','-p','test_scene_robustness.py','-v']),
 ('VP-05',['AC-04'],[f'{old}/VERIFY_TESTS.py']),
 ('VP-06',['AC-02','AC-04'],['handoffs/evaluator_executor/PRINTER-COGNITION-FIRST-20261126/VERIFY_GUIDE.py']),
 ('VP-07',['AC-02','AC-04'],['handoffs/evaluator_executor/PRINTER-COGNITION-FIRST-20261126/VERIFY_CONTEXT.py']),
 ('VP-08',['AC-02','AC-04'],['handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126/VERIFY_ACTION.py']),
 ('VP-09',['AC-02','AC-04'],['handoffs/evaluator_executor/PRINTER-DECISION-WORKSHEET-20261126/VERIFY_BUSINESS.py']),
 ('VP-10',['AC-04'],['-m','unittest','discover','-s','tests','-q']),
 ('VP-11',['AC-05'],['scripts/audit_model_history_readonly.py','--task','handoffs/evaluator_executor/PRINTER-MODEL-COMPARE-20261118']),
 ('VP-12',['AC-05'],['-m','unittest','discover','-s','tests','-p','test_history_audit_version_transition.py','-v']),
 ('VP-13',['AC-03','AC-04'],[f'{rel}/VERIFY_NATIVE.py','--role','executor']),
 ('VP-14',['AC-05','AC-06'],[f'{rel}/VERIFY_PACKET.py','delivery'])]
lines=['schema: evaluator-executor-validation-plan/v1','task_id: PRINTER-SCENE-ROBUSTNESS-20261127','runtime: WSL Python3 explicit PYTHONPATH; existing Windows Python/JDK','checks:']
for vid,ac,args in specs:
    cmd=prefix+args
    lines+=['  - id: '+vid,'    ac: '+json.dumps(ac),'    cwd: .','    command: '+json.dumps(cmd),'    expected_exit_code: 0','    mandatory: true']
    if vid in ['VP-02','VP-13']:lines+=['    evaluator_command: '+json.dumps(cmd[:-1]+['evaluator'])]
(TASK/'VALIDATION_PLAN.yaml').write_text('\n'.join(lines)+'\n',encoding='utf8')
allowed=['shopping_decision/focus_guidance.py','shopping_decision/chat_bridge.py','shopping_decision/cognition_guide.py','shopping_decision/context_builder.py','shopping_decision/decision_note.py','scripts/audit_model_history_readonly.py','tests/test_scene_robustness.py','desktop/SceneRobustnessRegression.java','desktop/SceneRobustnessSwingRegression.java']
prior=json.loads((OLD/'BASELINE.json').read_text());protected=dict(prior['protected_sha256']);products={}
for group,glob in [('shopping_decision','*.py'),('knowledge','*.json'),('desktop','*.java'),('tests','*.py'),('scripts','*.py')]:
    for p in (ROOT/group).glob(glob):
        name=p.relative_to(ROOT).as_posix();products[name]=sha(p)
        if name not in allowed:protected[name]=sha(p)
for p in OLD.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts and 'recheck-20261127' not in p.parts and p.suffix!='.class':protected[p.relative_to(ROOT).as_posix()]=sha(p)
for p in TASK.iterdir():
    if p.is_file() and p.name!='BASELINE.json':protected[p.relative_to(ROOT).as_posix()]=sha(p)
for name in allowed:protected.pop(name,None)
for name in ['CURRENT.md','docs/PROJECT_BOTTLENECK_MAP_CURRENT.md']:protected.pop(name,None)
index=subprocess.check_output(['git','diff','--cached','--binary','--no-ext-diff'],cwd=ROOT)
baseline=dict(baseline_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),index_sha256=hashlib.sha256(index).hexdigest(),product_sha256=products,protected_sha256=protected,allowed_product=allowed,inherited_prior_unknown=True,baseline_scope='all inherited product/tests/knowledge and previous immutable handoffs; mutable evaluator review-session evidence excluded',prior_task='PRINTER-FOCUSED-GUIDANCE-20261127')
save(TASK/'BASELINE.json',baseline)
print(json.dumps(dict(task_id='PRINTER-SCENE-ROBUSTNESS-20261127',cases=24,checks=14,protected=len(protected),allowed=allowed),ensure_ascii=False))
