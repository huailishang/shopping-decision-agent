"""Replay remaining journeys through the actual stdin subprocess; native records are separate."""
from pathlib import Path
import sys,json,hashlib
from datetime import datetime
ROOT=Path(__file__).resolve().parents[4]
# script is evidence/executor -> evidence -> task -> evaluator_executor -> handoffs -> repository
ROOT=Path(__file__).resolve().parents[5]
EX=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_decision_worksheet import ws,filled,change
from test_worksheet_bridge import bridge
from test_cost_scenario_binding import relaxed,scenario
from test_session_decision_contract import family,public,answer,first,render_chat
from test_worksheet_evidence import source
from shopping_decision.cost_scenario import dependency_fingerprints
from shopping_decision.chat_bridge import new_dialogue

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def cost(v):return public(v)['cost_comparison']
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
rawdir=EX/('journey-raw-'+datetime.now().strftime('%Y%m%dT%H%M%S'));rawdir.mkdir()
cases=[]
baseline=EX/'common-repaired-baseline.json'
expect=EX/'journey-expectations.json'
def run(id,expected,fn,lim=''):
    trace=[]
    def invoke(s,a,w=None,p=None):
        v=bridge(s,a,w,p);trace.append({'state':s,'action':a,'worksheet':w,'payload':p,'response':v});return v
    try:completed=bool(fn(invoke));error=None
    except Exception as exc:completed=False;error=repr(exc)
    p=rawdir/(id+'.json');save(p,{'trace':trace,'error':error})
    cases.append({'id':id,'expected':expected,'before':{'observation':'见真实首个请求与回执','artifact':ref(p),'step':0},'after':{'observation':'见真实最后请求与回执','artifact':ref(p),'step':len(trace)-1,'assertion':completed,'error':error},'completed':completed,'route':'bridge_process','raw_artifacts':[ref(p),ref(expect)],'limitations':lim})
def j1(i):
    s=family();a=i(s,'create');t=answer(s,'requires_scan','暂不确定');b=i(t,'rebind',ws(a));u=answer(t,'requires_scan','否');c=i(u,'rebind',ws(b))
    return a['prompt_field']=='requires_scan' and 'requires_scan' in ws(b)['deferred'] and c['prompt_field']!='requires_scan' and ws(c)['confirmed']['requires_scan'] is False
def j3(i):
    s=family();v=filled(s,i);t=i(s,'edit',ws(v),change('Brother HL-L1238W','starter',1500))
    return cost(v)['scenario_preference'] is None and cost(t)['scenario_preference'] is None and first(v)==first(t)
def j4(i):
    s=relaxed();v=filled(s,i);z=i(s,'edit',ws(v),change(None,'pages',0));u=i(s,'clear',ws(z),change(None,'pages',0));t=i(s,'edit',ws(u),change(None,'pages',1800))
    return ws(z)['basis']['pages']==0 and ws(u)['basis']['pages'] is None and cost(u)['scenario_preference'] is None and cost(t)['scenario_preference']=='HP M232dw'
def j5(i):
    s=relaxed();v=filled(s,i);a=i(s,'import_source',ws(v),source());b=i(s,'import_source',ws(a),source(id='wrong',candidate='other'));c=i(s,'import_source',ws(b),source(status='approved'))
    return '历史报价线索' in a['worksheet_sources'] and '型号不适用' in b['worksheet_sources'] and 'error' in c and public(b)['claims']==public(v)['claims']
def j6(i):
    s=relaxed();v=filled(s,i);c='HP M232dw';fid=next(iter(dependency_fingerprints(public(v),c)));p={'candidate':c,'fact_id':fid};b=i(s,'bind_reference',ws(v),p);w=ws(b);w['models'][c]['dependency_fingerprints'][fid]='0'*64;n=i(s,'preview',w);r=i(s,'withdraw_reference',ws(b),p)
    return cost(b)['scenario_preference'] is not None and cost(n)['scenario_preference'] is None and cost(r)['scenario_preference'] is None and public(r)['claims']==public(v)['claims'] and ws(r)['confirmed']==ws(v)['confirmed']
def j8(i):
    s=relaxed();v=filled(s,i);b=i(s,'edit',ws(v),change('HP M232dw','hardware','1e1000000'));t=i(s,'edit',ws(v),change('Brother HL-L1238W','starter',1500))
    return 'error' in b and cost(t)['scenario_preference']=='Brother HL-L1238W'
def j10(i):
    s=relaxed();v=filled(s,i);t=answer(s,'device_deployment_region','中国大陆北京市');a=i(t,'preview',ws(v));u=answer(s,'category','手机');b=i(u,'rebind',ws(v))
    return 'error' in a and not ws(b)['models'] and 'HL-L1238W' not in b['report_json']
def j11(i):
    s=relaxed();v=filled(s,i);t=i(s,'edit',ws(v),change('Brother HL-L1238W','hardware',450));u=answer(s,'needs_color','是');f=i(u,'rebind',ws(t))
    return cost(t)['scenario_preference'] is None and all(a['research_status']=='excluded_for_research' for a in public(f)['assessments'])
def j12(i):
    s=family();v=i(s,'create')
    return bool(v['worksheet_sources']) and '来源' in v['result_text'] and bool(v['prompt_field'])
run('J01','扫描未答→暂缓→无需，同源首问',j1)
run('J03','硬缺证时修改成本不选冠军',j3)
run('J04','零页/未知/口径补齐',j4,'共享口径补齐已验证；工作单共享口径不允许两候选各设不同值，直接规则异口径另有专项，完整链暂不签。')
cases[-1]['completed']=False
run('J05','未审/错型号/伪造状态隔离且合法邻居保留',j5)
run('J06','依赖撤回/同ID版本失效，独立事实保留',j6,'通过旧引用指纹变造模拟同ID改版；未实际核源变更，故完整链暂不签。')
cases[-1]['completed']=False
run('J08','超界错误后保留已提交工作单并继续有效修改',j8)
run('J10','需求地区或品类变更不回流',j10)
run('J11','平局/单候选/全部失败',j11,'未覆盖单候选完整链，暂不签。')
cases[-1]['completed']=False
run('J12','来源审计与首问可见，首屏可读性待独立审查',j12,'未完成首屏人工检查，暂不签。')
cases[-1]['completed']=False
native=sorted(EX.glob('java-native-*'))[-1]
for id,expected,files,complete,lim in [
 ('J02','窗口改单变量成本和行动翻转',['J02-before.txt','J02-after.txt','DecisionWorksheetSwingRegression.stdout.txt'],True,'真实事件→桥→结果；合成硬条件，无真人/实时价'),
 ('J07','窗口显式保存→新空白会话和Python子进程恢复重算',['J07-saved.json','J07-restored.txt','DecisionWorksheetSwingRegression.stdout.txt'],True,'实际窗口保存和恢复'),
 ('J09','草稿/文件选择取消及失败保全',['J02-before.txt','J02-after.txt','DecisionWorksheetSwingRegression.stdout.txt'],False,'取消已通过；写入失败及原文件保全的窗口链未测完')]:
    paths=[native/f for f in files];ok=all(p.is_file() for p in paths)
    cases.append({'id':id,'expected':expected,'before':{'artifact':ref(paths[0]),'observation':'原生实际操作原件'},'after':{'artifacts':[ref(p) for p in paths[1:]],'observation':'见原生回执和断言'},'completed':complete and ok,'route':'java_event','raw_artifacts':[ref(p) for p in paths if p.is_file()]+[ref(expect)],'limitations':lim})
cases.sort(key=lambda x:x['id'])
data={'schema_version':1,'baseline_description':'共同修复后的直接规则入口原件 '+baseline.name+' SHA='+sha(baseline),'cases':cases}
raw=EX/'journeys.json';save(raw,data)
summary={'raw_sha256':sha(raw),'generator_sha256':sha(Path(__file__)),'completed':sum(c['completed'] for c in cases),'core_completed':sum(c['completed'] and c['id']<='J08' for c in cases),'java_event_completed':sum(c['completed'] and c['route']=='java_event' for c in cases)}
save(EX/'journey-summary.json',summary)
print(summary)
for c in cases:print(c['id'],c['completed'],c['route'],c['after'].get('error'))
