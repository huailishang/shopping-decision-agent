import base64,json,subprocess,sys,unittest
from test_decision_worksheet import req,ws,change,filled
from test_session_decision_contract import family,public

def raw_call(raw):
    p=subprocess.run([sys.executable,'-m','shopping_decision.chat_bridge','--worksheet-stdin'],input=raw,capture_output=True,timeout=30)
    if p.returncode:raise AssertionError(p.stderr.decode(errors='replace'))
    return {k:base64.b64decode(v).decode() for k,v in (l.split('\t',1) for l in p.stdout.decode().splitlines())}
def bridge(s,a,w=None,p=None):
    return raw_call(json.dumps(req(s,a,w,p),ensure_ascii=False).encode())

class Bridge(unittest.TestCase):
    def test_create(self):self.assertEqual(len(ws(bridge(family(),'create'))['models']),2)
    def test_edit(self):
        s=family();w=ws(bridge(s,'create'))
        self.assertEqual(ws(bridge(s,'edit',w,change(None,'pages',0)))['basis']['pages'],0)
    def test_duplicate(self):self.assertIn('error',raw_call(b'{"action":"create","action":"restore"}'))
    def test_size(self):self.assertIn('error',raw_call(b' '*262145))
    def test_depth(self):self.assertIn('error',raw_call(b'['*20+b'0'+b']'*20))
    def test_unknown_action(self):self.assertIn('error',bridge(family(),'execute'))
