from REPAIR_CHECK import P,save,now
from PREP_BASELINE import HERE
import sys,subprocess,time
mode=sys.argv[1]
if mode=='scoring':
    cmd=[sys.executable,'-B','-X','utf8','-c',"import VERIFY_DIAGNOSTIC as v; from REPAIR_CHECK import save; v.save=save; v.scoring()"]
elif mode in ('A','B'):
    cmd=[sys.executable,'-B','-X','utf8',str(HERE/'DIAGNOSTIC_GUI.py'),'--arm',mode,'--card','P1a','--smoke']
else:raise ValueError(mode)
t=time.monotonic();start=now()
p=subprocess.run(cmd,cwd=HERE,capture_output=True,timeout=45)
for ext,data in [('stdout',p.stdout),('stderr',p.stderr),('exit',str(p.returncode).encode())]:
    with (P/(mode+'.'+ext)).open('xb') as f:f.write(data)
save(mode+'.timing.json',dict(command=cmd,started=start,ended=now(),elapsed=time.monotonic()-t,exit=p.returncode))
print(mode,p.returncode,p.stderr.decode('utf8',errors='replace')[:2000])
if mode=='scoring':print(p.stdout.decode('utf8',errors='replace'))
else:
    import json
    print(json.loads(p.stdout)['errors'] if p.stdout else 'no trace')
raise SystemExit(p.returncode)
