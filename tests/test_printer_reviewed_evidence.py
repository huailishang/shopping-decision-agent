"""Normal-chat regression for the explicitly enabled manufacturer pack."""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message
from shopping_decision.evidence_comparison import SAFE_FLAGS
from shopping_decision import printer_reviewed_evidence as reviewed

ROOT = Path(__file__).resolve().parents[1]
VERIFY = runpy.run_path(str(ROOT / "handoffs/evaluator_executor/PRINTER-EVIDENCE-TO-DECISION-20261124/VERIFY_DELIVERY.py"))

class ReviewedPrinterTests(unittest.TestCase):
    def setUp(self):
        # Exercise the prior deterministic gate using historical bytes as a
        # test fixture. This does not confer production approval.
        fixture = patch.object(reviewed, "PACK_SHA256", sha256(reviewed.PACK_PATH.read_bytes()).hexdigest())
        fixture.start()
        self.addCleanup(fixture.stop)
        self.state = new_dialogue()
        for field, answer in (("category","打印机"),("usage","家用黑白"),
                              ("budget_max_cny","1000"),("wechat_required","必须"),
                              ("device_deployment_region","中国大陆河南省"),
                              ("accepts_initial_setup","接受"),
                              ("wechat_workflow","微信小程序直接打印")):
            self.state = submit_message(self.state,field,answer)

    def view(self, state=None, enabled="1"):
        with patch.dict("os.environ", {"SHOPPING_PRINTER_REVIEWED_EVIDENCE":enabled}):
            output = render_chat(deepcopy(state or self.state))
        report = json.loads(output["report_json"])
        self.assertTrue(all(report[k] is False for k in SAFE_FLAGS[:3]))
        public = report["public_decision"]
        if public:
            self.assertTrue(all(public[k] is False for k in SAFE_FLAGS))
        return output["result_text"], public

    def claims(self,state=None):
        text, public = self.view(state)
        self.assertIsNotNone(public)
        return {(c["candidate_id"],c["dimension"]):c for c in public["claims"]}

    def test_normal_entry_and_gate(self):
        claims = self.claims()
        brother = claims[("Brother HL-L1238W","wechat_miniprogram")]
        self.assertEqual(brother["status"],"met")
        self.assertEqual(brother["source_audit"][0]["source_id"],"brother-cn-manual")
        self.assertEqual(claims[("HP M232dw","wechat_miniprogram")]["status"],"unknown")
        self.assertTrue(all(c["status"]=="unknown" for (_,d),c in claims.items() if d=="cost"))
        text,_ = self.view()
        self.assertIn(brother["claim_id"],text)
        self.assertIn("support.brother.com",text)

    def test_switch_off(self):
        self.assertIsNone(self.view(enabled="0")[1])

    def test_transfer_distinct(self):
        claims=self.claims(submit_message(self.state,"wechat_workflow","转App"))
        self.assertTrue(all(c["status"]=="unknown" for (_,d),c in claims.items() if d=="wechat_transfer_to_app"))

    def test_revised_and_withdrawn(self):
        revised=submit_message(self.state,"budget_max_cny","800")
        text,_=self.view(revised)
        self.assertIn("800元",text)
        for answer in ("不是必须","暂不确定"):
            self.assertIsNone(self.view(submit_message(self.state,"wechat_required",answer))[1])

    def test_wrong_region_and_rejected_initial_setup(self):
        for field,answer in (("device_deployment_region","日本"),("accepts_initial_setup","不接受")):
            self.assertIsNone(self.view(submit_message(self.state,field,answer))[1])

    def test_missing_corrupt_and_adversarial_pack(self):
        original=json.loads(reviewed.PACK_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"pack.json"
            with patch.object(reviewed,"PACK_PATH",path):
                self.assertIsNone(self.view()[1])
                path.write_text("{",encoding="utf-8")
                self.assertIsNone(self.view()[1])
                for mutate in (
                    lambda p:p["facts"][0].update(candidate_id="HP M232dw"),
                    lambda p:p["facts"][0].update(statement="无条件批准购买"),
                    lambda p:p["sources"][0].update(revoked=True),
                    lambda p:p["sources"][0].update(valid_until="2020-01-01"),
                    lambda p:p["facts"][0].update(dimension="cost",unit="CNY",value=1,kind="live_quote"),
                ):
                    changed=deepcopy(original)
                    mutate(changed)
                    path.write_text(json.dumps(changed,ensure_ascii=False),encoding="utf-8")
                    self.assertIsNone(self.view()[1])

    def test_expired_real_pack(self):
        with patch("shopping_decision.chat_bridge.date") as clock:
            clock.today.return_value=date(2027,1,1)
            self.assertIsNone(self.view()[1])

    def test_frozen_replay(self):
        runs=VERIFY["replay"]()
        self.assertTrue(all(not row["public_decision"] for row in runs["0"].values()))
        self.assertIsNotNone(runs["1"]["miniprogram"]["public_decision"])

if __name__ == "__main__":
    unittest.main()
