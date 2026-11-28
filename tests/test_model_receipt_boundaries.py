import unittest,json
from copy import deepcopy
from shopping_decision.model_adapter import ModelRoute,normalize
R=ModelRoute('fixture','mock','responses',32000,2048,'fixture')
C=ModelRoute('fixture','mock','chat_completions',32000,2048,'fixture')
def body(route):
    if route.protocol=='responses':
        return {'model':'mock','status':'completed','output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':'{}'}]}]}
    return {'model':'mock','choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'{}'}}]}
def message(route,b):
    return b['output'][0] if route.protocol=='responses' else b['choices'][0]['message']
def run(route,b):
    return normalize(route,http_status=200,raw=json.dumps(b))
class ReceiptBoundaries(unittest.TestCase):
    def test_both_pure(self):
        for route in (R,C):
            result=run(route,body(route))
            self.assertEqual(result['status'],'complete')
            self.assertEqual(len(result['text_sha256']),64)
            self.assertFalse(result['business_accepted'])
    def test_mixed_tool(self):
        for route in (R,C):
            for k,v in [('tool_calls',[{'id':'x'}]),('function_call',{'name':'x'}),('refusal','no')]:
                b=body(route);message(route,b)[k]=v
                self.assertEqual(run(route,b)['status'],'unexpected_output')
    def test_metadata_compatible(self):
        for route in (R,C):
            b=body(route);message(route,b)['vendor_extension']={'metric':3}
            self.assertEqual(run(route,b)['status'],'complete')
    def test_size(self):
        self.assertEqual(normalize(R,http_status=200,raw=' '*1048577)['status'],'response_over_limit')
    def test_deep_json(self):
        self.assertEqual(normalize(R,http_status=200,raw='['*2000+']'*2000)['status'],'malformed_response')

    def test_reasoning_shape_and_nested_execution(self):
        for content in ([{"type":"reasoning_text","text":"valid"}],):
            b=body(R); b["output"].insert(0,{"type":"reasoning","content":content,"summary":[{"type":"summary_text","text":"valid"}],"vendor_metadata":{"metric":2}})
            self.assertEqual(run(R,b)["status"],"complete")
        for content in ([{"type":"function_call","arguments":"{}"}],[{"type":"refusal","text":"no"}],
                        [{"type":"reasoning_text","text":"x","extra":{"tool_calls":[{"type":"function"}]}}],{},[{"type":"reasoning_text","text":42}]):
            b=body(R);b["output"].insert(0,{"type":"reasoning","content":content})
            self.assertEqual(run(R,b)["status"],"unexpected_output")
        b=body(C);message(C,b)["reasoning_content"]={"type":"function_call"}
        self.assertEqual(run(C,b)["status"],"unexpected_output")
