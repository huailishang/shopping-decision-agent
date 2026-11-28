"""Evaluator-only read-only probe. Does not write original prototype evidence."""
import json, sys
from pathlib import Path
from copy import deepcopy
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'handoffs/PRINTER-RESEARCH-ENTRY-PROTOTYPE-20261128'))
from prototype import Entry, load_upstream
def start(e,usage):
    e.direct(); e.answer('打印机'); e.answer(usage)
def answer(e,f,a):
    old=deepcopy(e.state); e.select_topic(f); assert e.state==old
    return e.answer(a)
rows=[]
for usage,field,dim in [
 ('把爷爷签过字的纸保存到电脑里，发给远方家人','requires_scan','scan'),
 ('每份练习纸正反都印满，不想翻纸重放','requires_auto_duplex','auto_duplex'),
 ('一年就寒暑假回去住几天，其余时候机器不动','idle_weeks_pattern',None)]:
    e=Entry(); start(e,usage); base=e.view()['field']
    if dim:
        for f,a in [(field,'是'),('needs_color','否'),('device_deployment_region','河南'),('monthly_pages_range','0-50')]: v=answer(e,f,a)
        reached=v['confirmed'].get(field) is True and any(x['dimension']==dim and x['status']=='unknown' for x in v['facts'])
    else:
        v=answer(e,field,'经常连续多周不用'); reached=(v['usage_research'] or {}).get('status')=='research_required'
    assert reached and not any(v['safe'].values())
    rows.append({'usage':usage,'base_first_field':base,'manual_target':field,'reached':reached,'question':v['question'],'safe':v['safe']})
e=Entry(); draft=load_upstream('device-research'); e.receive(draft); e.withdraw()
assert e.receive(draft)=='duplicate' and not e.view()['active']
fresh=Entry(); fresh.receive(draft)
rows.append({'same_instance_replay_blocked':True,'fresh_instance_replay_reactivates':fresh.view()['active'],'scope':'process-local only'})
print(json.dumps(rows,ensure_ascii=False,indent=2))
