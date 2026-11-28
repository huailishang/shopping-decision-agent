import json
from unittest import TestCase
from shopping_decision.model_adapter import ModelRoute,payload,normalize
R=ModelRoute("offline","mock","responses",16000,2048,"fixture")
C=ModelRoute("offline","mock","chat_completions",16000,2048,"fixture")
def response(model="mock",role="assistant",text="{}"):
    d={"status":"completed","output":[{"type":"message","role":role,"content":[{"type":"output_text","text":text}]}]}
    if model is not None:d["model"]=model
    return d
def norm(route,data,status=200,**kw):
    return normalize(route,http_status=status,raw=json.dumps(data),**kw)
class ModelAdapterTests(TestCase):
    def test_protocol_and_budget(self):
        self.assertEqual(payload(R,"system",{},512,256)["max_output_tokens"],768)
        self.assertEqual(payload(C,"system",{},512)["max_tokens"],512)
        for bad in (True,-1,9999):
            with self.assertRaises(ValueError):payload(R,"system",{},bad)
    def test_identity_role_and_multiple_messages(self):
        self.assertEqual(norm(R,response())["status"],"complete")
        unknown=norm(R,response(None))
        self.assertEqual((unknown["status"],unknown["identity"]),("identity_unknown","unknown"))
        self.assertEqual(norm(R,response("other"))["status"],"model_mismatch")
        self.assertEqual(norm(R,response(role="user"))["status"],"unexpected_output")
        d=response(); d["output"]*=2
        self.assertEqual(norm(R,d)["status"],"unexpected_output")
        self.assertEqual(norm(R,{"model":"mock","status":"completed","output":[{"type":"reasoning"}]})["status"],"reasoning_only")
    def test_classify_and_raw_hash(self):
        for status,data,expected in ((400,{},"invalid_request"),(400,{"error":{"code":"context_length_exceeded"}},"context_limit"),
             (429,{},"rate_or_quota_limit"),(401,{},"auth_or_permission"),(500,{},"provider_error"),
             (200,{"success":False,"code":500},"application_error"),
             (200,{"status":"incomplete","incomplete_details":{"reason":"max_output_tokens"}},"output_limit")):
            got=norm(R,data,status)
            self.assertEqual(got["status"],expected)
            self.assertEqual(len(got["raw_sha256"]),64)
            self.assertIsNone(got["text"])
        self.assertEqual(normalize(R,http_status=200,raw='bad')["status"],"malformed_response")
        self.assertEqual(normalize(R,transport_error="timeout")["status"],"timeout")
    def test_chat_completions(self):
        d={"model":"mock","choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"{}"}}]}
        self.assertEqual(norm(C,d)["status"],"complete")
        d["choices"][0]["message"]["tool_calls"]=[{}]
        self.assertEqual(norm(C,d)["status"],"unexpected_output")
        d["choices"][0]["finish_reason"]="length"
        self.assertEqual(norm(C,d)["status"],"output_limit")
