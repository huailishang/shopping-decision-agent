"""Frozen black-box regression for the carried decisive-variable failure."""
from pathlib import Path
import base64,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from shopping_decision.chat_bridge import new_dialogue,submit_message

def req(s,a,w=None,p=None):return dict(schema_version=1,action=a,state=s,worksheet=w,payload=p or {})
def ws(v):return json.loads(v['worksheet_json'])
def change(cid,f,x):return dict(candidate=cid,field=f,value=x)
def public(v):
    r=json.loads(v['report_json'])
    return r['cognition_comparison']['public'] if r.get('cognition_comparison') else r['public_decision']
def family():
    s=new_dialogue()
    for f,a in [('category','打印机'),('usage','低频家庭打印'),('needs_color','否'),('accepts_outsourced_color','是'),('monthly_pages_range','0-50'),('budget_max_cny','1000'),('device_deployment_region','中国大陆河南省'),('wechat_required','必须'),('wechat_workflow','小程序'),('accepts_initial_setup','接受')]:s=submit_message(s,f,a)
    return s
def relaxed():
    s=family()
    for f,a in [('requires_scan','否'),('requires_auto_duplex','否'),('wechat_required','否'),('budget_max_cny','撤回')]:s=submit_message(s,f,a)
    return s

def bridge(s,a,w=None,p=None):
    r=subprocess.run([sys.executable,'-X','utf8','-m','shopping_decision.chat_bridge','--worksheet-stdin'],cwd=ROOT,input=json.dumps(req(s,a,w,p),ensure_ascii=False).encode(),capture_output=True,timeout=30)
    if r.returncode:raise AssertionError(r.stderr.decode(errors='replace'))
    return {k:base64.b64decode(v).decode() for k,v in (line.split('\t',1) for line in r.stdout.decode().splitlines())}
def filled(s):
    v=bridge(s,'create');changes=[change(None,'pages',1800),change(None,'months',36)]
    for cid,h,p in [('Brother HL-L1238W',500,100),('HP M232dw',550,50)]:
        changes += [change(cid,f,x) for f,x in dict(hardware=h,starter=0,toner_yield=1500,toner_price=p,separate_drum=False,maintenance=0).items()]
    return bridge(s,'edit_many',ws(v),{'changes':changes})
def main():
    s=relaxed();v=filled(s); rows=[]
    for cid,f,x,label in [('HP M232dw','maintenance',100,'维护'),('HP M232dw','hardware',650,'主机'),('Brother HL-L1238W','starter',300,'随箱')]:
        changed=bridge(s,'edit',ws(v),change(cid,f,x))
        p=public(changed); prompt=changed.get('prompt','')
        ok=p['cost_comparison']['scenario_preference']=='Brother HL-L1238W' and cid in prompt and label in prompt
        rows.append({'candidate':cid,'field':f,'value':x,'passed':ok,'prompt':prompt,'cost':p['cost_comparison'],'result_text':changed.get('result_text')})
    print(json.dumps({'cases':rows,'passed':sum(r['passed'] for r in rows),'total':len(rows),'external_calls':0},ensure_ascii=False,indent=2))
    return int(not all(r['passed'] for r in rows))
if __name__=='__main__':raise SystemExit(main())
