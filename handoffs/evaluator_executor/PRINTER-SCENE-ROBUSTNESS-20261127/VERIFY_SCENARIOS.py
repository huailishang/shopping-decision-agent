"""Frozen independent first-question checks; real product stdin, no model call."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,base64,hashlib,json,os,subprocess,sys
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2]
sys.path.insert(0,str(ROOT))
from shopping_decision.chat_bridge import submit_message,new_dialogue

def save(p,data):
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--role',choices=['executor','evaluator'],required=True);a=ap.parse_args()
    out=TASK/'evidence'/a.role/('scenarios-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'));out.mkdir(parents=True)
    rows=[]
    for case in json.loads((TASK/'SCENARIOS.json').read_text(encoding='utf8'))['cases']:
        folder=out/case['id'];folder.mkdir();s=submit_message(new_dialogue(),'category','打印机');s=submit_message(s,'usage',case['usage'])
        req=dict(schema_version=1,action='guide',state=s,worksheet=None,payload={});save(folder/'stdin.json',req)
        argv=[sys.executable,'-X','utf8','-m','shopping_decision.chat_bridge','--worksheet-stdin']
        p=subprocess.run(argv,cwd=ROOT,input=json.dumps(req,ensure_ascii=False).encode(),capture_output=True,timeout=30)
        (folder/'stdout.txt').write_bytes(p.stdout);(folder/'stderr.txt').write_bytes(p.stderr)
        checks={};details={}
        try:
            v={k:base64.b64decode(x).decode() for k,x in (ln.split('\t',1) for ln in p.stdout.decode().splitlines())};save(folder/'response.json',v)
            focus=json.loads(v['guidance_focus_json']);context=json.loads(v['cognition_context_json']);note=json.loads(v['decision_note_json']);report=json.loads(v['report_json'])
            checks=dict(exit_ok=p.returncode==0,relevant=v['prompt_field'] in case['allowed_fields'],
                no_auto_confirmation=json.loads(v['state_json'])==s,focus_same=focus==context['guidance_focus']==note['guidance_focus'],
                prompt_same=focus['field']==v['prompt_field'] and focus['question']==v['prompt'],
                safe=all(report[k] is False for k in ['purchase_recommendation_approved','transactions_enabled','live_price_verified']))
            details=dict(actual_field=v['prompt_field'],expected_fields=case['allowed_fields'])
        except Exception as e:checks['decoded']=False;details['error']=repr(e)
        rows.append(dict(id=case['id'],checks=checks,passed=bool(checks) and all(checks.values()),details=details))
    result=dict(cases=rows,passed=sum(r['passed'] for r in rows),total=24,fixture_sha256=hashlib.sha256((TASK/'SCENARIOS.json').read_bytes()).hexdigest())
    save(out/'results.json',result);print(json.dumps(result,ensure_ascii=False));return int(result['passed']!=24)
if __name__=='__main__':raise SystemExit(main())
