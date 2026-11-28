from pathlib import Path
import os,sys,subprocess,shutil,json
root=Path(__file__).resolve().parents[5]
out=Path(__file__).resolve().parent/'native-slice-01'
out.mkdir(exist_ok=True)
classes=out/'classes';classes.mkdir(exist_ok=True)
def run(label,cmd):
    p=subprocess.run(cmd,cwd=root,env=dict(os.environ,PYTHONUTF8='1'),capture_output=True,timeout=90)
    (out/(label+'.stdout.txt')).write_bytes(p.stdout);(out/(label+'.stderr.txt')).write_bytes(p.stderr)
    print(label,p.returncode,p.stdout.decode('utf8',errors='replace'),p.stderr.decode('utf8',errors='replace'),flush=True)
    return p.returncode
code=run('compile',[shutil.which('javac'),'-encoding','UTF-8','--release','17','-d',str(classes),*[str(root/'desktop'/f) for f in ['DesktopBridgeClient.java','ShoppingDecisionDesktop.java','DecisionWorksheetSwingRegression.java','CognitionGuideSwingRegression.java']]])
if code==0:code=run('native',[shutil.which('java'),'-cp',str(classes),'CognitionGuideSwingRegression',sys.executable,str(out)])
raise SystemExit(code)
