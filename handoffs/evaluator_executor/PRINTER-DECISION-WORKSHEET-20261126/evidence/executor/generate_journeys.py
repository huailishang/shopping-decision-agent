"""Replay product bridge and incorporate real native UI operation records."""
from pathlib import Path
import sys,json,hashlib,subprocess,base64
from datetime import datetime
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[5]
EX=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_decision_worksheet import ws,filled,change,req
from test_worksheet_bridge import bridge
from test_cost_scenario_binding import relaxed
from test_session_decision_contract import family,public,answer,first,bundle
from test_worksheet_evidence import source
from test_printer_decision_journey import hard_met_bundle
from shopping_decision.evidence_comparison import digest
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def cost(v):return public(v)['cost_comparison']
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
rawdir=EX/('journey-raw-'+datetime.now().strftime('%Y%m%dT%H%M%S%f'));rawdir.mkdir()
cases=[]
baseline=EX/'common-repaired-baseline.json'
expect=EX/'journey-expectations.json'
FIXTURE_ENTRY="""import sys,json
from unittest.mock import patch
from shopping_decision import chat_bridge
with open(sys.argv[1],encoding='utf8') as f:b=json.load(f)
sys.argv=['chat_bridge','--worksheet-stdin']
with patch('shopping_decision.chat_bridge._analysis',return_value={'recommendation':{'status':'research'},'verified_research_bundle':b}):
    chat_bridge.main()
"""
def run(id,expected,fn,lim=''):
    trace=[];fixtures=[]
    def i(s,a,w=None,p=None,fixture=None):
        item={'state':s,'action':a,'worksheet':w,'payload':p}
        if fixture is None:v=bridge(s,a,w,p)
        else:
            path=rawdir/(id+'-fixture-'+str(len(trace))+'.json');save(path,fixture);fixtures.append(ref(path))
            proc=subprocess.run([sys.executable,'-X','utf8','-c',FIXTURE_ENTRY,str(path)],input=json.dumps(req(s,a,w,p),ensure_ascii=False).encode(),capture_output=True,timeout=30,cwd=ROOT)
            if proc.returncode:raise RuntimeError(proc.stderr.decode(errors='replace'))
            v={k:base64.b64decode(v).decode() for k,v in (line.split('\t',1) for line in proc.stdout.decode().splitlines())}
            item['controlled_source_fixture']=ref(path);item['process_exit']=proc.returncode
        item['response']=v;trace.append(item);return v
    try:completed=bool(fn(i));error=None
    except Exception as exc:completed=False;error=repr(exc)
    p=rawdir/(id+'.json');save(p,{'trace':trace,'error':error})
    cases.append({'id':id,'expected':expected,'before':{'observation':'实际首个请求与回执','artifact':ref(p),'step':0},'after':{'observation':'实际最后请求与回执','artifact':ref(p),'step':len(trace)-1,'assertion':completed,'error':error},'completed':completed,'route':'bridge_process','raw_artifacts':[ref(p),ref(expect)]+fixtures,'limitations':lim})
def j1(i):
    s=family();a=i(s,'create');t=answer(s,'requires_scan','暂不确定');b=i(t,'rebind',ws(a));u=answer(t,'requires_scan','否');c=i(u,'rebind',ws(b))
    return a['prompt_field']=='requires_scan' and 'requires_scan' in ws(b)['deferred'] and c['prompt_field']!='requires_scan' and ws(c)['confirmed']['requires_scan'] is False
def j3(i):
    s=family();v=filled(s,i);t=i(s,'edit',ws(v),change('Brother HL-L1238W','starter',1500))
    return cost(v)['scenario_preference'] is None and cost(t)['scenario_preference'] is None and first(v)==first(t)
def j4(i):
    s=relaxed();v=filled(s,i);z=i(s,'edit',ws(v),change(None,'pages',0));u=i(s,'clear',ws(z),change(None,'pages',0));t=i(s,'edit',ws(u),change(None,'pages',1800))
    mixed=i(s,'edit',ws(t),change('HP M232dw','currency','USD'));again=i(s,'preview',ws(t))
    return ws(z)['basis']['pages']==0 and ws(u)['basis']['pages'] is None and cost(u)['scenario_preference'] is None and cost(t)['scenario_preference']=='HP M232dw' and 'error' in mixed and cost(again)==cost(t)
def j5(i):
    s=relaxed();v=filled(s,i);a=i(s,'import_source',ws(v),source());b=i(s,'import_source',ws(a),source(id='wrong',candidate='other'));c=i(s,'import_source',ws(b),source(status='approved'));d=i(s,'import_source',ws(b),source(id='conflict',excerpt='不同合成报价'))
    return '历史报价线索' in a['worksheet_sources'] and '型号不适用' in b['worksheet_sources'] and 'error' in c and '待核冲突' in d['worksheet_sources'] and public(d)['claims']==public(v)['claims']
def j6(i):
    s=relaxed();old_bundle=bundle(s)
    def before(st,a,w=None,p=None):return i(st,a,w,p,fixture=old_bundle)
    v=filled(s,before);c='HP M232dw';fid='hp-replace-on-quality';p={'candidate':c,'fact_id':fid};b=before(s,'bind_reference',ws(v),p)
    updated=deepcopy(old_bundle);src=next(x for x in updated['sources'] if x.get('snapshot'));src['snapshot']['body']['version']+='; controlled new edition';src['snapshot']['sha256']=digest(src['snapshot']['body'])
    n=i(s,'preview',ws(b),fixture=updated);r=before(s,'withdraw_reference',ws(b),p)
    assessments=lambda v:[(a['candidate_id'],a['research_status']) for a in public(v)['assessments']]
    return cost(b)['scenario_preference'] is not None and cost(n)['reasons'][c]=='dependency_version_changed' and cost(n)['scenario_preference'] is None and cost(r)['scenario_preference'] is None and public(r)['claims']==public(v)['claims'] and assessments(n)==assessments(b) and ws(r)['confirmed']==ws(v)['confirmed']==ws(n)['confirmed']
def j8(i):
    s=relaxed();v=filled(s,i);b=i(s,'edit',ws(v),change('HP M232dw','hardware','1e1000000'));t=i(s,'edit',ws(v),change('Brother HL-L1238W','starter',1500))
    return 'error' in b and cost(t)['scenario_preference']=='Brother HL-L1238W'
def j10(i):
    s=relaxed();v=filled(s,i);t=answer(s,'device_deployment_region','中国大陆北京市');a=i(t,'preview',ws(v));u=answer(s,'category','手机');b=i(u,'rebind',ws(v))
    return 'error' in a and not ws(b)['models'] and 'HL-L1238W' not in b['report_json']
def j11(i):
    s=relaxed();v=filled(s,i);t=i(s,'edit',ws(v),change('Brother HL-L1238W','hardware',450))
    one=answer(s,'requires_scan','是');fixture=hard_met_bundle(one)
    next(f for f in fixture['facts'] if f['candidate_id']=='Brother HL-L1238W' and f['dimension']=='scan')['value']=False
    single=filled(one,lambda st,a,w=None,p=None:i(st,a,w,p,fixture=fixture))
    u=answer(s,'needs_color','是');f=i(u,'rebind',ws(t))
    states=[a['research_status'] for a in public(single)['assessments']]
    return cost(t)['status']=='tie' and '平局' in t['result_text'] and states.count('excluded_for_research')==1 and states.count('eligible_for_research')==1 and cost(single)['scenario_preference'] is None and all(a['research_status']=='excluded_for_research' for a in public(f)['assessments']) and not public(f)['next_actions']
def j12(i):
    s=family();v=i(s,'create');r=relaxed();normal=filled(r,i);bad=i(r,'edit',ws(normal),change('HP M232dw','hardware','1e1000000'));again=i(r,'preview',ws(normal))
    def readable(a):return a['result_text'].count('下一步：')==1 and '命题ID' not in a['result_text'] and len(a['result_text'])<len(a['worksheet_detail_text']) and '未批准购买' in a['result_text']
    return all(readable(x) for x in (v,normal,again)) and bool(v['worksheet_sources']) and 'error' in bad and cost(again)==cost(normal)
run('J01','扫描未答→暂缓→无需，同源首问',j1)
run('J03','硬缺证时修改成本不选冠军',j3)
run('J04','零页/未知/异口径请求拒绝后恢复共享口径',j4)
run('J05','未审/错型号/伪造状态/冲突隔离且合法邻居保留',j5)
run('J06','实际证据门禁的同ID新版本/撤回导致依赖失效',j6,'离线受控来源样本，非重新取得厂家材料；同一生产桥及原证据门禁重算。')
run('J08','超界错误后保留已提交工作单并继续有效修改',j8)
run('J10','需求地区或品类变更不回流',j10)
run('J11','平局/单候选/全部失败',j11,'单候选使用明确合成反证，不是实际产品事实。')
run('J12','来源审计与首问可见、首屏不被代码编号淹没',j12,'程序化首屏检查；真人可读性待独立审查。')
native=sorted(EX.glob('java-native-*'))[-1]
native_log=native/'DecisionWorksheetSwingRegression.stdout.txt'
log=native_log.read_text(encoding='utf8')
for id,expected,files,lim in [
 ('J02','窗口改单变量成本和行动翻转',['J02-before.txt','J02-after.txt'],'真实事件→桥→结果；合成硬条件，无真人/实时价'),
 ('J07','窗口显式保存→新空白会话和Python子进程恢复重算',['J07-saved.json','J07-restored.txt'],'实际窗口保存和恢复'),
 ('J09','草稿/文件选择取消及失败保全',['J02-before.txt','J09-after.txt'],'真实窗口取消和既有文件拒绝覆盖'),
 ('J04','零页/未知/异口径请求拒绝后恢复共享口径',['J04-before.txt','J04-after.txt'],'异口径拒绝由本案真实子进程补充'),
 ('J08','超界错误后继续有效修改',['J08-before.txt','J08-after.txt'],'真实窗口错误弹框及后续合法提交'),
 ('J10','地区或品类变更旧成本不回流',['J10-before.txt','J10-after.txt'],'窗口地区变更和真实桥品类变更')]:
    paths=[native/f for f in files]+[native_log];ok=all(p.is_file() for p in paths) and ('PASS '+id) in log and 'WORKSHEET_NATIVE_PASS' in log
    previous=next((c for c in cases if c['id']==id),None)
    if previous:cases.remove(previous);ok=ok and previous['completed']
    if id=='J02' and ok:
        before=paths[0].read_text(encoding='utf8').split('完整来源')[0];after=paths[1].read_text(encoding='utf8').split('完整来源')[0]
        ok='下一步：核实HP M232dw' in before and '下一步：核实Brother HL-L1238W' in after
    cases.append({'id':id,'expected':expected,'before':{'artifact':ref(paths[0]),'observation':'原生实际操作原件'},'after':{'artifacts':[ref(p) for p in paths[1:]],'observation':'见原生回执和断言'},'completed':ok,'route':'java_event','raw_artifacts':[ref(p) for p in paths if p.is_file()]+[ref(expect)]+(previous['raw_artifacts'] if previous else []),'limitations':lim})
cases.sort(key=lambda x:x['id'])
data={'schema_version':1,'baseline_description':'共同修复后的直接规则入口原件 '+baseline.name+' SHA='+sha(baseline),'cases':cases}
raw=EX/'journeys.json';save(raw,data)
summary={'raw_sha256':sha(raw),'generator_sha256':sha(Path(__file__)),'completed':sum(c['completed'] for c in cases),'core_completed':sum(c['completed'] and c['id']<='J08' for c in cases),'java_event_completed':sum(c['completed'] and c['route']=='java_event' for c in cases)}
save(EX/'journey-summary.json',summary)
print(summary)
for c in cases:print(c['id'],c['completed'],c['route'],c['after'].get('error'))
