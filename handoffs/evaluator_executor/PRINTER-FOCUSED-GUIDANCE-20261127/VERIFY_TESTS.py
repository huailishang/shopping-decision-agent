"""Require substantive four new suites, run without installing dependencies."""
import json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];names=["test_focus_guidance.py","test_focus_guidance_bridge.py","test_focus_guidance_lineage.py","test_guidance_replay.py"]
rows=[]
for name in names:
    if not (ROOT/"tests"/name).is_file():rows.append(dict(file=name,passed=False,reason="missing"));continue
    suite=unittest.TestLoader().discover(str(ROOT/"tests"),pattern=name)
    if suite.countTestCases()<3:rows.append(dict(file=name,passed=False,reason="need at least 3 behavioral cases"));continue
    p=subprocess.run([sys.executable,"-X","utf8","-m","unittest","discover","-s","tests","-p",name,"-v"],cwd=ROOT,capture_output=True,timeout=150)
    print(p.stdout.decode(errors="replace"));print(p.stderr.decode(errors="replace"),file=sys.stderr)
    rows.append(dict(file=name,passed=p.returncode==0))
print(json.dumps(rows,ensure_ascii=False));raise SystemExit(int(not all(r["passed"] for r in rows)))
