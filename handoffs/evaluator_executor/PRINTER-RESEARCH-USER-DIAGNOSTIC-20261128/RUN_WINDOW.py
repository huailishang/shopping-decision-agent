from pathlib import Path
from PREP_BASELINE import HERE,OUT,now
import subprocess,sys,time,json
for arm in ('A','B'):
    cmd=[sys.executable,'-B','-X','utf8',str(HERE/'DIAGNOSTIC_GUI.py'),'--arm',arm,'--card','P1a','--smoke']
    start=now();tick=time.monotonic();name='window-'+arm
    try:
        p=subprocess.run(cmd,capture_output=True,timeout=40)
        out,err,rc=p.stdout,p.stderr,p.returncode
    except subprocess.TimeoutExpired as e:
        out,err,rc=e.stdout or b'',e.stderr or b'',124
    (OUT/(name+'.stdout')).write_bytes(out);(OUT/(name+'.stderr')).write_bytes(err);(OUT/(name+'.exit')).write_text(str(rc),encoding='utf8')
    (OUT/(name+'.timing.json')).write_text(json.dumps(dict(command=cmd,started=start,ended=now(),elapsed_seconds=time.monotonic()-tick,exit=rc,participant_seconds=None),indent=2),encoding='utf8')
    print(name,rc,err.decode('utf8',errors='replace')[:1000],flush=True)
    if rc:raise SystemExit(rc)
