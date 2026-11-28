"""Compile real Java sources and execute bridge plus native event-driven Swing checks."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2]
p=argparse.ArgumentParser();p.add_argument('--role',required=True,choices=['executor','evaluator']);role=p.parse_args().role
required=['DecisionWorksheetRegression.java','DecisionWorksheetSwingRegression.java']
missing=[name for name in required if not (ROOT/'desktop'/name).is_file()]
if missing:print(json.dumps({'missing':missing}));raise SystemExit(1)
if os.name!='nt':
    native=Path('/mnt/d/SoftWare/Anaconda/install/python.exe')
    if not native.is_file():raise SystemExit('现有Windows Python不可用；不安装、不将SKIP记通过。')
    winpath=subprocess.check_output(['wslpath','-w',str(Path(__file__).resolve())],text=True).strip()
    raise SystemExit(subprocess.run([str(native),'-X','utf8',winpath,'--role',role],cwd=ROOT).returncode)
out=TASK/'evidence'/role/('java-native-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
out.mkdir(parents=True);classes=out/'classes';classes.mkdir()
env=dict(os.environ,PYTHONUTF8='1')
commands=[]
def run(label,argv,timeout=180):
    start=datetime.now(timezone.utc).isoformat()
    try:
        r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=timeout)
        code=r.returncode;stdout=r.stdout;stderr=r.stderr
    except subprocess.TimeoutExpired as exc:code=124;stdout=str(exc.stdout or '');stderr='bounded timeout'
    (out/(label+'.stdout.txt')).write_text(stdout,encoding='utf8');(out/(label+'.stderr.txt')).write_text(stderr,encoding='utf8')
    commands.append({'label':label,'argv':argv,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'exit_code':code})
    print(label,code,stdout[-1500:]);return code,stdout,stderr
javac=shutil.which('javac');java=shutil.which('java')
if not java or not javac:raise SystemExit('既有JDK缺失，不能虚报Java通过。')
code,_,_=run('compile',[javac,'-encoding','UTF-8','--release','17','-d',str(classes),*[str(f) for f in sorted((ROOT/'desktop').glob('*.java'))]])
ok=code==0
if ok:
    for cls in ['ChatBridgeRegression','ChatSwingRegression','DecisionWorksheetRegression','DecisionWorksheetSwingRegression']:
        argv=[java,'-cp',str(classes),cls,sys.executable]
        if cls.startswith('DecisionWorksheet'):argv.append(str(out))
        code,stdout,stderr=run(cls,argv)
        passed=code==0 and 'SKIP' not in stdout and 'SKIP' not in stderr
        if cls=='DecisionWorksheetSwingRegression':passed=passed and 'WORKSHEET_NATIVE_PASS' in stdout
        ok=ok and passed
summary={'passed':ok,'role':role,'platform':sys.platform,'python':sys.executable,'commands':commands,'native_requirement':'new Swing check must execute events and print WORKSHEET_NATIVE_PASS only after actual assertions'}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False));raise SystemExit(0 if ok else 1)
