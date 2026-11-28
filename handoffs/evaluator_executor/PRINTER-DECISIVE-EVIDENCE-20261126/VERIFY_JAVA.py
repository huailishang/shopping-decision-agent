"""Compile actual sources and run old plus new native event regressions."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--role',required=True,choices=['executor','evaluator']);role=ap.parse_args().role
missing=[x for x in ['DecisionEvidenceRegression.java','DecisionEvidenceSwingRegression.java'] if not (ROOT/'desktop'/x).is_file()]
if missing:print(json.dumps({'missing':missing}));raise SystemExit(1)
if os.name!='nt':
    native=Path('/mnt/d/SoftWare/Anaconda/install/python.exe')
    if not native.is_file():raise SystemExit('existing Windows Python unavailable; no install or SKIP-as-pass')
    path=subprocess.check_output(['wslpath','-w',str(Path(__file__).resolve())],text=True).strip()
    raise SystemExit(subprocess.run([str(native),'-X','utf8',path,'--role',role],cwd=ROOT).returncode)
out=TASK/'evidence'/role/('java-native-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'));out.mkdir(parents=True)
classes=out/'classes';classes.mkdir();rows=[];env=dict(os.environ,PYTHONUTF8='1')
def run(label,argv):
    start=datetime.now(timezone.utc).isoformat()
    try:
        p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,timeout=180);code=p.returncode;stdout=p.stdout;stderr=p.stderr
    except subprocess.TimeoutExpired as exc:code=124;stdout=exc.stdout or b'';stderr=(exc.stderr or b'')+b'\nbounded timeout'
    (out/(label+'.stdout.txt')).write_bytes(stdout);(out/(label+'.stderr.txt')).write_bytes(stderr)
    ok=code==0 and b'SKIP' not in stdout+stderr
    if label=='DecisionEvidenceSwingRegression':ok=ok and b'DECISIVE_EVIDENCE_NATIVE_PASS' in stdout
    rows.append({'label':label,'argv':argv,'start':start,'end':datetime.now(timezone.utc).isoformat(),'exit_code':code,'passed':ok})
    print(label,code,stdout.decode('utf8',errors='replace')[-1200:]);return ok
java=shutil.which('java');javac=shutil.which('javac')
if not java or not javac:raise SystemExit('existing JDK unavailable')
ok=run('compile',[javac,'-encoding','UTF-8','--release','17','-d',str(classes),*[str(p) for p in sorted((ROOT/'desktop').glob('*.java'))]])
if ok:
    for cls in ['ChatBridgeRegression','ChatSwingRegression','DecisionWorksheetRegression','DecisionWorksheetSwingRegression','DecisionEvidenceRegression','DecisionEvidenceSwingRegression']:
        args=[java,'-cp',str(classes),cls,sys.executable]
        if cls.startswith('Decision'):args.append(str(out))
        passed=run(cls,args);ok=ok and passed
summary={'passed':ok,'role':role,'platform':sys.platform,'commands':rows}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False));raise SystemExit(int(not ok))
