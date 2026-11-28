from PREP_BASELINE import HERE,OUT,now
import sys,subprocess,time,json
def run(mode):
    cmd=[sys.executable,'-B','-X','utf8',str(HERE/'VERIFY_DIAGNOSTIC.py'),mode]
    name=mode if not (OUT/(mode+'.exit')).exists() else mode+'.r2'
    if (OUT/(name+'.exit')).exists(): raise ValueError('refuse overwriting evidence')
    start=now();t=time.monotonic()
    p=subprocess.run(cmd,capture_output=True,timeout=180)
    (OUT/(name+'.stdout')).write_bytes(p.stdout)
    (OUT/(name+'.stderr')).write_bytes(p.stderr)
    (OUT/(name+'.exit')).write_text(str(p.returncode),encoding='utf8')
    d=dict(command=cmd,started=start,ended=now(),elapsed_seconds=time.monotonic()-t,exit=p.returncode,participant_seconds=None)
    (OUT/(name+'.timing.json')).write_text(json.dumps(d,indent=2),encoding='utf8')
    print(mode,p.returncode,p.stdout.decode('utf8',errors='replace'),p.stderr.decode('utf8',errors='replace'),flush=True)
    return p.returncode
if __name__=='__main__':
    raise SystemExit(run(sys.argv[1]))
