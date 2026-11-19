"""Synthetic tests of the evaluator checker, not product-effect observations."""
import copy
import json
import unittest
from pathlib import Path
from check_delivery import validate_snapshot


class CheckerGuards(unittest.TestCase):
    def setUp(self):
        task = Path(__file__).resolve().parent
        self.case = json.loads((task / 'cases.json').read_text(encoding='utf-8'))['cases'][0]
        rows = [json.loads(line) for line in (task / 'preparation/baseline.stdout.jsonl')
                .read_text(encoding='utf-8').splitlines() if line.strip()]
        self.snapshot = copy.deepcopy(rows[-1]['real_printer_case_research']['shared_research_snapshot'])
        self.snapshot['decision_plan'] = {
            'schema_version': 1, 'scope': 'conditional_model_research',
            'current_path': 'clarify_wechat_requirement', 'reuse_verified': False,
            'purchase_recommendation_approved': False, 'transactions_enabled': False,
            'primary_question': {'field': 'wechat_required', 'status': 'unconfirmed'},
            'branches': [{'when': {'wechat_required': flag},
                          'basis': 'hypothetical_not_user_confirmation',
                          'candidate_model_ids': ['HL-L1238W', 'M232dw'],
                          'source_ids': ['R7', 'R10'],
                          'state': 'pending_reuse_evidence' if flag else 'research_can_continue',
                          'explanation': 'SYNTHETIC fixture, not source or product output',
                          'limitations': 'No physical reuse, live quote or permission is proved',
                          'next_step': {'action': 'SYNTHETIC next action', 'owner_role': 'SYNTHETIC owner',
                                        'exact_item': 'SYNTHETIC field',
                                        'blocks': 'wechat_reuse_claim' if flag else 'specific_unverified_claim_only'}}
                         for flag in (True, False)],
            'purchase_checks': [{'field': field, 'stage': 'purchase', 'verified': False}
                                for field in ('budget_scope', 'delivery_region', 'sale_identity', 'live_price')],
            'text': 'SYNTHETIC fixture only. No real model fact or user confirmation is created. '
                    'Two conditional paths remain research-only and both lack physical reuse evidence.'}

    def check(self):
        return validate_snapshot(self.snapshot, self.case)

    def test_structurally_complete_fixture_is_accepted(self):
        self.assertEqual(self.check()['current_path'], 'clarify_wechat_requirement')

    def test_existing_output_without_conditional_plan_is_rejected(self):
        del self.snapshot['decision_plan']
        with self.assertRaises(ValueError): self.check()

    def test_unknown_cannot_become_user_confirmation(self):
        self.snapshot['decision_plan']['primary_question']['status'] = 'confirmed'
        with self.assertRaises(ValueError): self.check()

    def test_hypothetical_branch_cannot_become_user_answer(self):
        self.snapshot['decision_plan']['branches'][0]['basis'] = 'user_confirmed'
        with self.assertRaises(ValueError): self.check()

    def test_unmapped_source_is_rejected(self):
        del self.snapshot['source_registry']['R7']
        with self.assertRaises(ValueError): self.check()

    def test_setup_cannot_become_verified_reuse(self):
        self.snapshot['decision_plan']['reuse_verified'] = True
        with self.assertRaises(ValueError): self.check()

    def test_unknown_fact_cannot_remove_a_candidate(self):
        self.snapshot['decision_plan']['branches'][0]['candidate_model_ids'] = ['M232dw']
        with self.assertRaises(ValueError): self.check()

    def test_purchase_gate_cannot_block_all_research(self):
        self.snapshot['decision_plan']['purchase_checks'][0]['stage'] = 'all_research'
        with self.assertRaises(ValueError): self.check()

    def test_order_or_payment_cannot_be_enabled(self):
        self.snapshot['decision_plan']['transactions_enabled'] = True
        with self.assertRaises(ValueError): self.check()

    def test_answered_requirement_is_not_reasked(self):
        self.case['expected_primary_question_field'] = None
        self.case['expected_current_path'] = 'verify_wechat_reuse'
        self.snapshot['decision_plan']['current_path'] = 'verify_wechat_reuse'
        with self.assertRaises(ValueError): self.check()


if __name__ == '__main__':
    unittest.main(verbosity=2)
