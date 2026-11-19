"""Checker self-tests: sparse data can proceed; invented evidence cannot."""
import copy
import json
import unittest
from pathlib import Path
from check_delivery import check_case


class MinimalFlowCheckerTests(unittest.TestCase):
    def setUp(self):
        task = Path(__file__).resolve().parent
        self.cases = json.loads((task / 'cases.json').read_text(encoding='utf-8'))['cases']
        self.packs = json.loads((task / 'evidence_packs.json').read_text(encoding='utf-8'))['packs']
        self.case = copy.deepcopy(self.cases[0])
        self.result = self.fixture(self.case)

    def fixture(self, case):
        pack_id = case['input']['research_context']['evidence_pack_id']
        pack = self.packs[pack_id]
        view = {'schema_version': 1, 'case_id': 'PRINTER-HENAN-FAMILY-20261116',
                'input_basis': 'project_owner_proxy', 'flow_status': 'research_delivered_with_limits',
                'purchase_recommendation_approved': False, 'transactions_enabled': False,
                'wechat_reuse_verified': False, 'live_price_verified': False,
                'long_term_reliability_verified': False, 'real_user_effect_verified': False,
                'new_external_fact_count': 0, 'evidence_pack_id': pack_id,
                'used_facts': copy.deepcopy(pack['claims']), 'source_registry': copy.deepcopy(pack['sources']),
                'candidate_assessments': [
                    {'model_id': mid, 'supported_claim_ids': [f['id'] for f in pack['claims'] if f['model_id'] == mid],
                     'research_status': 'keep_for_research', 'reason': 'SYNTHETIC fixture; not product output',
                     'unknown_fields': ['wechat_reuse', 'live_price', 'long_term_reliability']}
                    for mid in ('HL-L1238W', 'M232dw')],
                'processed_stages': ['requirements', 'evidence', 'comparison', 'explanation'],
                'feedback': {'status': 'not_collected', 'actual_response_count': 0},
                'report_text': 'SYNTHETIC validation fixture only; not a user response or a real product result. '
                               'Sparse evidence can reach a readable research comparison while missing live prices, '
                               'reuse success and actual feedback remain explicitly unknown.',
                'next_actions': [{'action': 'SYNTHETIC action', 'owner_role': 'SYNTHETIC role',
                                  'exact_item': 'SYNTHETIC missing item'}]}
        return {'research_case': view}

    def test_two_existing_facts_are_enough_for_flow(self):
        self.assertEqual(len(check_case(self.result, self.case)['used_facts']), 2)

    def test_one_fact_can_continue_without_waiting_for_two_models(self):
        case = self.cases[1]
        self.assertEqual(len(check_case(self.fixture(case), case)['used_facts']), 1)

    def test_empty_variant_still_processes_research_with_unknowns(self):
        case = self.cases[2]
        self.assertEqual(check_case(self.fixture(case), case)['used_facts'], [])

    def test_current_output_without_selected_pack_flow_is_rejected(self):
        with self.assertRaises(ValueError): check_case({}, self.case)

    def test_selected_pack_cannot_be_ignored(self):
        self.result['research_case']['evidence_pack_id'] = 'another_pack'
        with self.assertRaises(ValueError): check_case(self.result, self.case)

    def test_changed_statement_or_date_is_not_accepted(self):
        self.result['research_case']['used_facts'][0]['observed_on'] = '2026-11-17'
        with self.assertRaises(ValueError): check_case(self.result, self.case)

    def test_unselected_sources_are_not_silently_used(self):
        self.result['research_case']['source_registry']['OTHER'] = {'url': 'synthetic.invalid'}
        with self.assertRaises(ValueError): check_case(self.result, self.case)

    def test_missing_claim_cannot_be_used_for_other_candidate(self):
        self.result['research_case']['candidate_assessments'][1]['supported_claim_ids'] = ['BROTHER-FIRST-SETUP']
        with self.assertRaises(ValueError): check_case(self.result, self.case)

    def test_unknown_reuse_does_not_become_verified(self):
        self.result['research_case']['wechat_reuse_verified'] = True
        with self.assertRaises(ValueError): check_case(self.result, self.case)

    def test_missing_feedback_is_not_relabelled_as_real_validation(self):
        self.result['research_case']['feedback']['status'] = 'confirmed_by_user'
        with self.assertRaises(ValueError): check_case(self.result, self.case)

    def test_purchase_permission_stays_false(self):
        self.result['research_case']['purchase_recommendation_approved'] = True
        with self.assertRaises(ValueError): check_case(self.result, self.case)

    def test_skipping_comparison_is_not_complete_flow(self):
        self.result['research_case']['processed_stages'].remove('comparison')
        with self.assertRaises(ValueError): check_case(self.result, self.case)


if __name__ == '__main__':
    unittest.main(verbosity=2)
