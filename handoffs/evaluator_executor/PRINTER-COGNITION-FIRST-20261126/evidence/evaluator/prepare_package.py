"""Evaluator preparation only: preserve a real baseline and real missing targets."""
from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess,sys
from datetime import datetime,timezone
E=Path(__file__).resolve().parent;TASK=E.parents[1];ROOT=TASK.parents[2]
OUT=TASK/'preparation';OUT.mkdir(exist_ok=True)
if (OUT/'preflight.json').exists():raise SystemExit('preserve earlier preparation; choose a new explicit revision')
skill=Path('C:/Users/HuailiShang/.codex/skills/evaluator-executor-workflow')
spec=importlib.util.spec_from_file_location('plan_runner',skill/'scripts/run_validation.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
plans={mode:len(module.load_plan(ROOT,TASK/'VALIDATION_PLAN.yaml',mode=mode)[1]) for mode in ('executor','evaluator')}
assert plans=={'executor':13,'evaluator':13}
for f in TASK.glob('VERIFY_*.py'):ast.parse(f.read_text(encoding='utf8'),filename=str(f))
old=ROOT/'handoffs/evaluator_executor/PRINTER-DECISIVE-EVIDENCE-20261126'
baseline=json.loads((old/'BASELINE.R1.json').read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
product_unchanged=all(sha(ROOT/p)==h for p,h in baseline['product_sha256'].items())
assert product_unchanged,'Evaluator unexpectedly edited product'
rows=[]
checks=[('guide',TASK/'VERIFY_GUIDE.py',[]),('context',TASK/'VERIFY_CONTEXT.py',[]),('tests',TASK/'VERIFY_TESTS.py',[]),('carried_action',old/'VERIFY_ACTION.py',[]),('java',TASK/'VERIFY_JAVA.py',['--role','executor']),('delivery',TASK/'VERIFY_DELIVERY.py',[])]
for name,path,args in checks:
    argv=[sys.executable,'-X','utf8',str(path),*args];start=datetime.now(timezone.utc).isoformat()
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=180)
    (OUT/(name+'.stdout.txt')).write_bytes(p.stdout);(OUT/(name+'.stderr.txt')).write_bytes(p.stderr)
    rows.append({'id':name,'argv':argv,'start':start,'end':datetime.now(timezone.utc).isoformat(),'exit_code':p.returncode,'expected_preparation_exit_code':1,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest(),'meaning':'real missing/failing target, not completed feature'})
validator=subprocess.run([sys.executable,'-X','utf8',str(skill/'scripts/validate_workflow.py'),'--repo',str(ROOT),'--current','CURRENT.md'],cwd=ROOT,capture_output=True)
(E/'workflow-draft.stdout.txt').write_bytes(validator.stdout);(E/'workflow-draft.stderr.txt').write_bytes(validator.stderr)
result={'task_id':TASK.name,'at':datetime.now(timezone.utc).isoformat(),'status':'EXPECTED_FAILURES_CONFIRMED' if all(x['exit_code']==1 for x in rows) else 'PREPARATION_MISMATCH','plans':plans,'checks':rows,'workflow_draft_exit_code':validator.returncode,'product_bytes_unchanged_by_evaluator':product_unchanged,'real_public_reads':0,'real_model_api_cli_platform_calls':0,'no_predecessor_executor_directory_observed':not (old/'evidence/executor').exists(),'old_baseline_sha256':sha(old/'BASELINE.R1.json')}
(OUT/'preflight.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(int(result['status']!='EXPECTED_FAILURES_CONFIRMED' or validator.returncode!=0))
