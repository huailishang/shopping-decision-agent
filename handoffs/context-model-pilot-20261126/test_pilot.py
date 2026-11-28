import copy
import json
import pathlib
import unittest
from runtime_contract import ModelRoute, assemble, normalize, request_payload, canonical
from shopping_projection import plan, validate_rank

ROOT = pathlib.Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "handoffs/evaluator_executor/PRINTER-CANDIDATE-TRADEOFF-20261125/evidence/executor/model"
ROUTE = ModelRoute("fixture","mock","responses",16000,2048)
CHAT = ModelRoute("fixture","mock","chat_completions",16000,2048)

def bundle(case):
    return json.loads((EVIDENCE / "web-gpt-20261125" / case / "request.json").read_text(encoding="utf-8"))

class PilotTests(unittest.TestCase):
    def test_context_budget(self):
        packet, ledger = assemble({"hard": "keep"}, {"large": "X"*2000, "small": 1}, ROUTE,
                                  input_cap=100,output_cap=100)
        self.assertEqual(packet["required"], {"hard":"keep"})
        self.assertEqual(packet["optional"], {"small":1})
        self.assertEqual(ledger["omitted"][0]["id"],"large")
        with self.assertRaisesRegex(ValueError, "required_context_over_budget"):
            assemble({"hard": "X"*200}, {}, ROUTE, input_cap=100,output_cap=100)

    def test_protocols(self):
        self.assertEqual(request_payload(ROUTE,"s",{},512)["max_output_tokens"],512)
        self.assertEqual(request_payload(CHAT,"s",{},512)["max_tokens"],512)
        with self.assertRaises(ValueError):
            request_payload(CHAT,"s",{},4096)
        with self.assertRaisesRegex(ValueError,"wire_input_over_budget"):
            request_payload(CHAT,"s"*500,{},512,input_cap=100)

    def test_failures(self):
        fixtures = [(ROUTE,200,'not json',None,"malformed_response"),
                    (ROUTE,200,{"status":"incomplete","incomplete_details":{"reason":"max_output_tokens"}},None,"output_limit"),
                    (ROUTE,200,{"success":False,"code":500},None,"provider_error"),
                    (ROUTE,None,None,"timeout","timeout"),
                    (ROUTE,400,{},None,"invalid_request"),
                    (ROUTE,400,{"error":{"code":"context_length_exceeded"}},None,"context_limit"),
                    (CHAT,429,{},None,"rate_or_quota_limit"),
                    (CHAT,401,{},None,"auth_or_permission"),
                    (CHAT,200,{"choices":[{"finish_reason":"length"}]},None,"output_limit"),
                    (ROUTE,200,{"status":"completed","output":[{"type":"reasoning"}]},None,"no_final_answer")]
        for route,status,body,err,expected in fixtures:
            with self.subTest(expected=expected):
                actual = normalize(route,status,body,err)
                self.assertEqual(actual["status"],expected)
                self.assertIsNone(actual["text"])

    def test_success(self):
        r = normalize(ROUTE,200,{"model":"mock","status":"completed","output":[{"type":"reasoning"},{"type":"message","content":[{"type":"output_text","text":"{}"}]}]})
        c = normalize(CHAT,200,{"model":"mock","choices":[{"finish_reason":"stop","message":{"content":"{}"}}]})
        self.assertEqual(r["text"],c["text"])
        self.assertEqual(r["status"],"complete")
        self.assertEqual(c["status"],"complete")

    def test_all_excluded(self):
        for case in ("C08","C08_SHORT"):
            p=plan(bundle(case),ROUTE)
            self.assertEqual(p["mode"],"rules_only")
            self.assertEqual(p["reason"],"all_candidates_excluded")
            self.assertNotIn("payload",p)

    def test_withdrawn_evidence(self):
        p=plan(bundle("C12"),ROUTE)
        self.assertEqual(p["mode"],"model_rank_actions")
        self.assertTrue(p["actions"])
        self.assertTrue(all(a["candidate"]=="HP M232dw" for a in p["actions"]))

    def test_action_gate(self):
        b=bundle("C01")
        p=plan(b,ROUTE)
        ctx=p["packet"]["required"]["context_id"]
        first=p["actions"][0]["id"]
        result={"context_id":ctx,"action_ids":[first]}
        self.assertEqual(validate_rank(p,result,b),[p["actions"][0]])
        for invalid in ({"context_id":"old","action_ids":[first]}, {"context_id":ctx,"action_ids":["fake"]},
                        {"context_id":ctx,"action_ids":[first,first]},dict(result, summary="invented fact")):
            with self.assertRaises(ValueError):
                validate_rank(p,invalid,b)
        changed=copy.deepcopy(b); changed["dialogue_version"]+=1
        with self.assertRaisesRegex(ValueError,"stale_context"):
            validate_rank(p,result,changed)

    def test_report(self):
        from shopping_decision.evidence_comparison import build_prompt, response_schema
        for case in ("C01","C08","C12","C08_SHORT"):
            b=bundle(case); p=plan(b,ROUTE)
            old=len((build_prompt(b)+"\nJSON Schema:\n"+json.dumps(response_schema(b),ensure_ascii=False)).encode("utf-8"))
            new=len(canonical(p["payload"]).encode("utf-8")) if "payload" in p else 0
            print(json.dumps({"case":case,"mode":p["mode"],"old_prompt_bytes":old,"new_wire_bytes":new,
                              "optional_omitted":len(p.get("ledger",{}).get("omitted",[]))},ensure_ascii=False))
            self.assertLess(new,old)

if __name__ == "__main__":
    unittest.main(verbosity=2)
