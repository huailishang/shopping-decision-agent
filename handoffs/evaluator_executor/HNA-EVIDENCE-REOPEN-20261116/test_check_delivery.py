"""Synthetic integrity counterexamples only; no web access or real material admission."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from check_delivery import CheckError, validate_receipt

class DeliveryGuards(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.collected=self.root/"task/evidence/collected"
        self.collected.mkdir(parents=True)
        self.proof=self.collected/"fixture.txt"
        self.proof.write_text("SYNTHETIC guard fixture; no real observations",encoding="utf-8")
        self.ref={"path":"task/evidence/collected/fixture.txt",
                  "sha256":hashlib.sha256(self.proof.read_bytes()).hexdigest()}
        self.ledger=self.root/"prior.json"
        self.ledger.write_text(json.dumps({"budget":{"search_used":6,"search_limit":6,
                                "document_reads_used":5,"document_read_limit":12}}),encoding="utf-8")
        self.plan={"task_id":"TASK","task_dir":"task","prior_ledger":{"path":"prior.json",
            "sha256":hashlib.sha256(self.ledger.read_bytes()).hexdigest()},
            "document_read_limit":7,"approved_hosts":["official.example"],
            "blocked_urls":["https://official.example/blocked"],
            "prohibited_actions":["business_api_calls","messages_sent"],
            "routes":[{"id":r,"owner":"Executor","local_inputs":["source-"+r],
                       "seed_urls":["https://official.example/"+r+str(i) for i in range(9)],
                       "document_read_limit":4} for r in ("A","B")]}
        self.receipt={"schema":"evidence-acquisition-receipt/v2","task_id":"TASK",
            "outcome":"no_actionable_evidence","purchase_recommendation_approved":False,
            "transactions_enabled":False,"parent_restoration_authorized":False,
            "prohibited_actions":{"business_api_calls":0,"messages_sent":0},
            "actions":[{"id":r+"0","route_id":r,"kind":"local","input_path":"source-"+r,
                        "recorded_at":"2026-11-17T08:00:00+08:00",
                        "outcome":"no_relevant_fact","evidence":copy.deepcopy(self.ref)} for r in ("A","B")],
            "materials":[],
            "route_results":[{"route_id":r,"owner":"Executor","state":"no_relevant_fact",
                             "reason":"synthetic source lacks the needed fact","action_ids":[r+"0"]} for r in ("A","B")],
            "owner_request":{"recipient_role":"material_holder","exact_item":"specific missing field",
                             "sent":False,"evidence":copy.deepcopy(self.ref)},
            "next_step":"submit actual collection results to evaluator"}
    def run_check(self):
        return validate_receipt(self.root,self.plan,self.receipt)
    def add_document(self,rid,index,outcome="readable"):
        row={"id":rid+"doc"+str(index),"route_id":rid,"kind":"document",
             "url":"https://official.example/"+rid+str(index),
             "recorded_at":"2026-11-17T08:01:00+08:00","outcome":outcome,
             "evidence":copy.deepcopy(self.ref)}
        self.receipt["actions"].append(row)
        self.receipt["route_results"][0 if rid=="A" else 1]["action_ids"].append(row["id"])
        return row
    def test_complete_no_evidence_is_a_valid_collection_submission(self):
        self.assertEqual(self.run_check()["outcome"],"no_actionable_evidence")
    def test_candidate_is_pending_evaluator_not_automatic_approval(self):
        self.receipt["outcome"]="candidate_found"
        self.receipt["materials"]=[{"action_id":"A0","review_status":"pending_evaluator",
            "model_or_subject_scope":"synthetic model","supported_claim":"synthetic fact",
            "limitations":"not a real source","action_relevance":"synthetic decision",
            "observed_on":"2026-11-17","novelty":"new_relevant_fact","evidence":copy.deepcopy(self.ref)}]
        self.receipt["route_results"][0]["state"]="candidate"
        self.assertEqual(self.run_check()["candidate_count"],1)
        self.receipt["materials"][0]["review_status"]="approved"
        with self.assertRaises(CheckError):self.run_check()
    def test_waiting_without_collection_does_not_complete_task(self):
        self.receipt["actions"]=[]
        with self.assertRaises(CheckError):self.run_check()
    def test_uninvestigated_route_cannot_be_silently_skipped(self):
        self.receipt["route_results"][1]["action_ids"]=[]
        with self.assertRaises(CheckError):self.run_check()
    def test_business_api_call_is_rejected(self):
        self.receipt["prohibited_actions"]["business_api_calls"]=1
        with self.assertRaises(CheckError):self.run_check()
    def test_automatic_parent_restore_is_rejected(self):
        self.receipt["parent_restoration_authorized"]=True
        with self.assertRaises(CheckError):self.run_check()
    def test_hash_substitution_is_rejected(self):
        self.proof.write_text("tampered",encoding="utf-8")
        with self.assertRaises(CheckError):self.run_check()
    def test_reference_outside_collected_scope_is_rejected(self):
        self.receipt["actions"][0]["evidence"]["path"]="../private.txt"
        with self.assertRaises(CheckError):self.run_check()
    def test_unknown_external_host_is_rejected(self):
        self.add_document("A",0)["url"]="https://unapproved.example/A0"
        with self.assertRaises(CheckError):self.run_check()
    def test_known_restricted_entry_cannot_be_retried(self):
        self.add_document("A",0)["url"]="https://official.example/blocked"
        with self.assertRaises(CheckError):self.run_check()
    def test_seven_remaining_reads_is_a_joint_limit(self):
        for r in ("A","B"):
            for i in range(4):self.add_document(r,i)
        with self.assertRaises(CheckError):self.run_check()
    def test_duplicate_document_attempt_is_rejected(self):
        self.add_document("A",0)
        self.add_document("A",1)["url"]="https://official.example/A0"
        with self.assertRaises(CheckError):self.run_check()
    def test_followed_link_needs_captured_original_anchor(self):
        row=self.add_document("A",0)
        row["url"]="https://official.example/new-link"
        row["discovered_from"]="A0"
        with self.assertRaises(CheckError):self.run_check()
    def test_restricted_document_cannot_be_rendered_as_an_extra_retry(self):
        source=self.add_document("A",0,"restricted")
        self.receipt["actions"].append({"id":"render","route_id":"A","kind":"render",
            "url":source["url"],"discovered_from":source["id"],"recorded_at":"2026-11-17",
            "outcome":"restricted","evidence":copy.deepcopy(self.ref)})
        with self.assertRaises(CheckError):self.run_check()
    def test_rewriting_parent_budget_is_rejected(self):
        self.ledger.write_text("{}",encoding="utf-8")
        with self.assertRaises(CheckError):self.run_check()

if __name__=="__main__":
    unittest.main()
