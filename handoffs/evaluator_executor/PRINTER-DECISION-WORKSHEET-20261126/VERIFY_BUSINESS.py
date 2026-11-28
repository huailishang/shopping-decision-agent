"""Frozen independent business probes; no product edits, network or persistence."""
import base64,json,subprocess,sys
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from shopping_decision.chat_bridge import new_dialogue,submit_message,render_chat
from shopping_decision.model_adapter import ModelRoute,normalize
from shopping_decision.evidence_comparison import digest

def family():
    state=new_dialogue()
    for field,text in [('category','打印机'),('usage','低频家庭打印'),('needs_color','否'),('accepts_outsourced_color','是'),('monthly_pages_range','0-50'),('budget_max_cny','1000'),('device_deployment_region','中国大陆河南省'),('wechat_required','必须'),('wechat_workflow','小程序'),('accepts_initial_setup','接受'),('requires_scan','否'),('requires_auto_duplex','否')]:
        state=submit_message(state,field,text)
    return state

def public(view):
    data=json.loads(view['report_json'])
    return data['cognition_comparison']['public'] if data.get('cognition_comparison') else data['public_decision']

def model_receipt(protocol,malicious=False):
    route=ModelRoute('fixture','mock',protocol,32000,2048,'frozen local fixture')
    if protocol=='responses':
        reasoning={'type':'reasoning','summary':[{'type':'summary_text','text':'fixture summary'}]}
        if malicious:reasoning['content']=[{'type':'function_call','name':'place_order','arguments':'{}'}]
        data={'model':'mock','status':'completed','output':[reasoning,{'type':'message','role':'assistant','content':[{'type':'output_text','text':'{}'}]}]}
    else:
        msg={'role':'assistant','content':'{}','reasoning_content':'fixture summary','vendor_metadata':{'metric':1}}
        if malicious:msg['tool_calls']=[{'type':'function','function':{'name':'place_order','arguments':'{}'}}]
        data={'model':'mock','choices':[{'finish_reason':'stop','message':msg}]}
    return normalize(route,http_status=200,raw=json.dumps(data))

def cost_input(p,extreme=False):
    params={'pages':1800,'hardware':500,'starter':0,'toner_yield':1500,'toner_price':100,'separate_drum':False,'maintenance':0,'months':36,'currency':'CNY','fee_scope':'hardware_consumables_maintenance','scenario_version':1}
    names=sorted(a['candidate_id'] for a in p['assessments'])
    rows={n:{'kind':'synthetic_scenario','inputs':dict(params),'dependency_fact_ids':[],'dependency_fingerprints':{}} for n in names}
    if extreme:rows[names[0]]['inputs']['toner_price']='1e1000000'
    return {'schema_version':1,'binding':{k:p['decision_binding'].get(k) for k in ('category','dialogue_version','confirmed_values_sha256','session')},'models':rows}

def main():
    results=[]
    def check(name,fn):
        try:
            detail=fn();passed=detail.pop('passed')
        except Exception as exc:
            detail={'exception':type(exc).__name__,'message':str(exc)};passed=False
        results.append({'id':name,'passed':bool(passed),'detail':detail})
    def cost_boundary(backend):
        s=family();base=render_chat(s);a=json.loads(base['report_json']);b=deepcopy(a['cognition_comparison']['bundle']);scenario=cost_input(public(base),True)
        if backend:
            with patch('shopping_decision.chat_bridge._analysis',return_value={'recommendation':{'status':'research'},'verified_research_bundle':b}):v=render_chat(s,cost_scenario=scenario)
        else:v=render_chat(s,cost_scenario=scenario)
        report=json.loads(v['report_json']);c=public(v)['cost_comparison']
        return {'passed':c['status'] in ('invalid','unknown') and not report['transactions_enabled'] and not c.get('scenario_preference'),'cost':c,'result_text':v['result_text'],'prompt':v['prompt']}
    for entry in (False,True):check('finite_cost_boundary_'+('backend' if entry else 'default'),lambda e=entry:cost_boundary(e))
    for protocol in ('responses','chat_completions'):
        for malicious in (False,True):
            def probe(p=protocol,m=malicious):
                r=model_receipt(p,m);return {'passed':r['status']!='complete' if m else r['status']=='complete','receipt':r}
            check(protocol+('_nested_or_mixed_tool' if malicious else '_legal_reasoning_metadata'),probe)
    def bridge():
        request={'schema_version':1,'action':'create','state':family(),'worksheet':None,'payload':{}}
        run=subprocess.run([sys.executable,'-X','utf8','-m','shopping_decision.chat_bridge','--worksheet-stdin'],input=json.dumps(request,ensure_ascii=False),text=True,encoding='utf8',capture_output=True,cwd=ROOT,timeout=30)
        output={}
        for line in run.stdout.splitlines():
            if '\t' in line:
                key,value=line.split('\t',1);output[key]=base64.b64decode(value,validate=True).decode('utf8')
        worksheet=json.loads(output['worksheet_json']) if 'worksheet_json' in output else None
        return {'passed':run.returncode==0 and 'error' not in output and isinstance(worksheet,dict) and bool(worksheet) and all(k in output for k in ('result_text','state_json','report_json')),'returncode':run.returncode,'output':output,'stderr':run.stderr}
    check('real_stdin_create_product_entry',bridge)
    print(json.dumps({'checks':results,'passed':sum(r['passed'] for r in results),'total':len(results),'failures':[r['id'] for r in results if not r['passed']]},ensure_ascii=False,indent=2))
    return int(any(not r['passed'] for r in results))

if __name__=='__main__':raise SystemExit(main())
