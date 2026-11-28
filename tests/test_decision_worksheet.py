import json, unittest
from copy import deepcopy
from shopping_decision.decision_worksheet import handle, parse
from test_session_decision_contract import family, answer, public
from test_cost_scenario_binding import relaxed

def req(s, action, w=None, payload=None):
    return dict(schema_version=1, action=action, state=s, worksheet=w, payload=payload or {})
def ws(v):
    return json.loads(v['worksheet_json'])
def call(s,action,w=None,payload=None):
    return handle(req(s,action,w,payload))
def change(cid,field,value):
    return dict(candidate=cid,field=field,value=value)
def filled(s,invoke=call):
    w=ws(invoke(s,'create'))
    changes=[change(None,'pages',1800),change(None,'months',36)]
    for cid,h,p in [('Brother HL-L1238W',500,100),('HP M232dw',550,50)]:
        for f,v in dict(hardware=h,starter=0,toner_yield=1500,toner_price=p,separate_drum=False,maintenance=0).items():
            changes.append(change(cid,f,v))
    return invoke(s,'edit_many',w,{'changes':changes})

class Worksheet(unittest.TestCase):
    def test_new(self):
        w=ws(call(family(),'create'))
        self.assertEqual(len(w['models']),2)
        self.assertIsNone(w['basis']['pages'])
    def test_zero_unknown(self):
        s=family();w=ws(call(s,'create'))
        w=ws(call(s,'edit',w,change(None,'pages',0)))
        self.assertEqual(w['basis']['pages'],0)
        self.assertIsNone(ws(call(s,'clear',w,change(None,'pages',0)))['basis']['pages'])
    def test_invalid_batch_atomic(self):
        s=family();w=ws(call(s,'create'));old=deepcopy(w)
        with self.assertRaises(ValueError):
            call(s,'edit_many',w,{'changes':[change(None,'pages',4),change(None,'months',0)]})
        self.assertEqual(old,w)
    def test_stale_rebind(self):
        s=family();w=ws(filled(s));t=answer(s,'requires_scan','否')
        with self.assertRaises(ValueError):call(t,'preview',w)
        self.assertIsNone(ws(call(t,'rebind',w))['basis']['pages'])
    def test_invalid_version(self):
        s=family();w=ws(call(s,'create'));w['schema_version']=9
        with self.assertRaises(ValueError):call(s,'preview',w)
    def test_numeric_bound(self):
        s=family();w=ws(call(s,'create'))
        for v in ('1e1000000',True,-1):
            with self.assertRaises(ValueError):call(s,'edit',w,change('HP M232dw','hardware',v))
