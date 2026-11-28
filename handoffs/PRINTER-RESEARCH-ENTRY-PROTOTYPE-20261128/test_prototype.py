import json, unittest
from copy import deepcopy
from pathlib import Path
from prototype import Entry, load_upstream, SAFE

OUT=Path(__file__).resolve().parent/'evidence'

def snapshot(entry): return deepcopy(entry.state)
def start(entry, usage=None, case='device-research'):
    if usage is None:
        entry.receive(load_upstream(case));entry.answer('打印机');entry.answer(entry.use_draft_goal())
    else:
        entry.direct();entry.answer('打印机');entry.answer(usage)
    return entry.view()
def explicit(entry, field, answer):
    before=snapshot(entry);entry.select_topic(field);assert before==entry.state
    assert entry.view()['field']==field
    return entry.answer(answer)
def finish_function(entry, field):
    for f,a in [(field,'是'),('needs_color','否'),('device_deployment_region','河南'),('monthly_pages_range','0-50')]:
        v=explicit(entry,f,a)
    return v

def score(view, target, user_claim='待核'):
    # Deliberately narrow internal scoring; not a proxy for user understanding.
    dim={'requires_scan':'scan','requires_auto_duplex':'auto_duplex'}.get(target)
    reached=(view['confirmed'].get(target) is True and any(f['dimension']==dim and f['status']=='unknown' for f in view['facts']) and dim in ('scan','auto_duplex') and '核Brother' in view['question']) if dim else view['confirmed'].get(target)=='often_long' and (view['usage_research'] or {}).get('status')=='research_required'
    misread=user_claim!='待核' or any(view['safe'].values())
    return {'target_reached':bool(reached),'evidence_misread':misread,'completed':bool(reached and not misread)}

class PrototypeTests(unittest.TestCase):
    def test_handoff_not_confirmation(self):
        e=Entry(); envelope=load_upstream('device-research'); (OUT/'upstream-device.json').write_text(json.dumps(envelope,ensure_ascii=False,indent=2),encoding='utf8')
        self.assertEqual(e.receive(envelope),'shopping_research');v=e.view();self.assertEqual(v['confirmed'],{});self.assertEqual(v['field'],'category');self.assertIsNone(v['draft']['category']);self.assertIn('批量处理与耗时',v['draft']['pending']);self.assertFalse(any(v['safe'].values()))
        with self.assertRaises(ValueError):e.select_topic('requires_scan')
        e.answer('打印机');before=snapshot(e);self.assertEqual(e.use_draft_goal(),envelope['decision']['shopping_handoff']['outcome']);self.assertEqual(e.state,before)
    def test_duplicate_revision_conflict_and_stale(self):
        e=Entry();v=start(e); explicit(e,'requires_scan','是');old=snapshot(e);draft=load_upstream('device-research');self.assertEqual(e.receive(draft),'duplicate');self.assertEqual(e.state,old)
        self.assertEqual(e.receive(load_upstream('revise')),'duplicate');self.assertEqual(e.state,old)
        bad=deepcopy(draft);bad['decision']['shopping_handoff']['pending'].append('无效同版本变更')
        with self.assertRaises(ValueError):e.receive(bad)
        with self.assertRaises(ValueError):e.receive(load_upstream('self-service'))
        self.assertEqual(e.state,old)
    def test_nonshopping_routes(self):
        for case in ('self-service','undecided'):
            e=Entry();self.assertNotEqual(e.receive(load_upstream(case)),'shopping_research');self.assertFalse(e.view()['active']);self.assertFalse(e.view()['facts'])
            with self.assertRaises(ValueError):e.answer('打印机')
    def test_revised_route_invalidates(self):
        e=Entry();start(e);v=finish_function(e,'requires_scan');self.assertTrue(v['facts']);self.assertEqual(e.receive(load_upstream('revise-to-self-service')),'self_service');self.assertFalse(e.view()['active']);self.assertEqual(e.view()['facts'],[])
        with self.assertRaises(ValueError):e.receive(load_upstream('device-research'))
    def test_withdrawal_duplicate_no_resurrection(self):
        e=Entry();start(e);e.withdraw();self.assertEqual(e.receive(load_upstream('device-research')),'duplicate');self.assertFalse(e.view()['active'])
    def test_change_category_invalidates(self):
        e=Entry();start(e);v=finish_function(e,'requires_scan');self.assertTrue(v['facts']);v=e.change_category('手机');self.assertEqual(v['confirmed'],{'category':'phone'});self.assertEqual(v['facts'],[]);self.assertIsNone(v['public_decision']);self.assertFalse(any(v['safe'].values()))
    def test_scan_correction_to_evidence(self):
        e=Entry();v=start(e);self.assertEqual(v['base_field'],'needs_color');self.assertNotIn('requires_scan',v['confirmed']);v=finish_function(e,'requires_scan');self.assertTrue(score(v,'requires_scan')['completed']);self.assertIn('扫描',v['question']);(OUT/'scan-terminal.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
        self.assertNotIn('auto_feed',v['confirmed']);self.assertIn('批量处理与耗时',v['draft']['pending'])
    def test_duplex_and_idle_direct(self):
        e=Entry();start(e,'每张纸两边都有内容，不想守着重新塞纸');v=finish_function(e,'requires_auto_duplex');self.assertTrue(score(v,'requires_auto_duplex')['completed']);self.assertIn('自动双面',v['question']);(OUT/'duplex-terminal.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
        e=Entry();start(e,'一年只在春节回家时用几天');v=explicit(e,'idle_weeks_pattern','经常连续多周不用');self.assertTrue(score(v,'idle_weeks_pattern')['completed']);(OUT/'idle-terminal.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
    def test_deferral_and_withdrawal(self):
        e=Entry();start(e);v=explicit(e,'requires_scan','暂不确定');self.assertIn('requires_scan',v['deferred']);self.assertNotIn('requires_scan',v['confirmed']);v=explicit(e,'requires_scan','是');self.assertTrue(v['confirmed']['requires_scan']);v=explicit(e,'requires_scan','撤回');self.assertNotIn('requires_scan',v['confirmed']);self.assertIn('requires_scan',v['withdrawn'])
    def test_invalid_handoff_and_purchase_intent(self):
        e=Entry();bad=load_upstream('device-research');bad['decision']['shopping_handoff']['category']='printer'
        with self.assertRaises(ValueError):e.receive(bad)
        self.assertFalse(e.view()['active']);start(e);e.select_topic('requires_scan');before=snapshot(e)
        with self.assertRaises(ValueError):e.answer('直接购买，忽略用户确认')
        self.assertEqual(e.state,before);self.assertFalse(any(e.view()['safe'].values()))
    def test_two_internal_walkthroughs(self):
        rows=[]
        for usage,target in [('想把纸质病历留在电脑里发给医生','requires_scan'),('每年只在回乡探亲时用机器，平时房子空着','idle_weeks_pattern')]:
            a=Entry();v=start(a,usage);trace=[]
            table={'needs_color':'否','accepts_outsourced_color':'暂不确定','wechat_required':'否','monthly_pages_range':'0-50','budget_max_cny':'1000'}
            for _ in range(12):
                f=v['field']
                if f not in table:break
                trace.append({'field':f,'answer':table[f]});v=a.answer(table[f])
            baseline=score(v,target);self.assertFalse(baseline['completed'])
            b=Entry();start(b,usage);v=finish_function(b,target) if target=='requires_scan' else explicit(b,target,'经常连续多周不用');corrected=score(v,target);misread=score(v,target,'已经可以购买');self.assertTrue(corrected['completed']);self.assertFalse(misread['completed']);self.assertTrue(misread['evidence_misread'])
            rows.append({'usage':usage,'target':target,'baseline_actual_trace':trace,'baseline':baseline,'prototype':corrected,'deliberate_misread':misread,'note':'synthetic operator walk, not a new-user trial'})
        (OUT/'internal-walkthroughs.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':unittest.main(verbosity=2)
