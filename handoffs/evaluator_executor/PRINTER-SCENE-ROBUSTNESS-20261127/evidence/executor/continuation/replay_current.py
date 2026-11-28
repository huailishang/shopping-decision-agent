import sys, tempfile, json, subprocess, base64, copy, os
from pathlib import Path
ROOT=Path.cwd(); TASK=ROOT/'handoffs/evaluator_executor/PRINTER-SCENE-ROBUSTNESS-20261127'; EX=TASK/'evidence/executor'; OLD=ROOT/'handoffs/evaluator_executor/PRINTER-FOCUSED-GUIDANCE-20261127'; sys.path.insert(0,str(OLD/'evidence/executor'))
import paired_replay as pr
from shopping_decision.chat_bridge import new_dialogue,submit_message
out=EX/'continuation'/'replay';out.mkdir(exist_ok=False)
refs=pr.load(pr.REF)['cases'];limits=pr.load(OLD/'TASK_CASES.json')['limits'];prior={x['case_id']:x['b']['basis'] for x in pr.load(OLD/'evidence/executor/comparisons.json')['pairs']}
rows=[]
for r in refs:
 cid=r['case_id']
 with tempfile.TemporaryDirectory(prefix='scene-control-') as d:
  base=Path(d);pr.populate(base,'focus')
  spec=r['setup_plan']
  if spec.get('kind')=='isolated_source_lifecycle':
   p=base/'knowledge/printer_cognition_guide_v1.json';data=pr.load(p);data['sources'][spec['source']]={'revision':spec['revision'],'status':spec['status']};p.write_text(json.dumps(data,ensure_ascii=False),encoding='utf8')
  b=pr.basis(base,limits);assert b==prior[cid],(cid,b,prior[cid]);x=pr.replay(base,out/cid,r,b);rows.append({'case_id':cid,'arm':x['arm']});print(cid,x['semantic_completed'],x['metrics'],flush=True)
pr.save(EX/'control_results.json',{'cases':rows})
scenes=pr.load(TASK/'SCENARIOS.json')['cases'];journeys=[]
answers={'requires_scan':'是','requires_auto_duplex':'是','idle_weeks_pattern':'经常连续多周不用','needs_color':'否','device_deployment_region':'河南','monthly_pages_range':'0-50','wechat_required':'否','accepts_outsourced_color':'暂不确定','budget_max_cny':'暂不确定','budget_scope':'暂不确定','delivery_region':'暂不确定'}
for c in scenes[:3]:
 cid=c['id']; folder=out/cid;folder.mkdir();s=submit_message(submit_message(new_dialogue(),'category','打印机'),'usage',c['usage']);initial=copy.deepcopy(s);events=[];target=c['allowed_fields'][0]
 for i in range(13):
  req={'schema_version':1,'action':'guide','state':s,'worksheet':None,'payload':{}};q=folder/f'{i}-stdin.json';pr.save(q,req)
  p=subprocess.run([sys.executable,'-X','utf8','-m','shopping_decision.chat_bridge','--worksheet-stdin'],cwd=ROOT,input=q.read_bytes(),capture_output=True,timeout=30)
  stdout=folder/f'{i}-stdout.txt';stdout.write_bytes(p.stdout);stderr=folder/f'{i}-stderr.txt';stderr.write_bytes(p.stderr);assert p.returncode==0,p.stderr
  v={k:base64.b64decode(x).decode() for k,x in (l.split('\t',1) for l in p.stdout.decode().splitlines())};vr=pr.save(folder/f'{i}-response.json',v);events.append({'type':'response','request':req,'exit_code':p.returncode,'stdin_artifact':pr.ref(q),'stdout_artifact':pr.ref(stdout),'stderr_artifact':pr.ref(stderr),'response_artifact':vr});ctx=json.loads(v['cognition_context_json']);confirmed=ctx['user_confirmed'];dim={'requires_scan':'scan','requires_auto_duplex':'auto_duplex'}.get(target)
  if target in confirmed and ((dim and any(f['dimension']==dim for f in ctx['candidate_facts']) and not v['prompt_field']) or (not dim and ctx['usage_research']['status']=='research_required')):break
  f=v['prompt_field'];a=answers.get(f,'暂不确定');
  if not f or i==12:break
  events.append({'type':'answer','field':f,'answer':a});s=submit_message(s,f,a)
 raw=pr.save(folder/'replay.json',{'initial_state':initial,'events':events});journeys.append({'scenario_id':cid,'replay':raw});print(cid,'terminal',v['prompt_field'],v['prompt'],flush=True)
pr.save(EX/'journeys.json',{'cases':journeys})
