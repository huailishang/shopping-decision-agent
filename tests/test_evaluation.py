import unittest

from shopping_decision.evaluation import EvaluationCase, EvaluationTrace, evaluate_contract


class UnifiedEvaluationContractTest(unittest.TestCase):
    def test_hidden_intent_never_leaks_to_agent(self):
        case = EvaluationCase(
            case_id="hidden-001",
            source="ecomagentbench",
            visible_request="推荐打印机",
            hidden_requirements=("必须无线",),
            gold_constraints=("无线",),
        )
        agent_input = case.agent_view()
        self.assertNotIn("hidden_requirements", agent_input)
        self.assertNotIn("gold_constraints", agent_input)
        self.assertNotIn("必须无线", str(agent_input))

    def test_source_and_official_score_are_preserved_not_invented(self):
        case = EvaluationCase(
            case_id="multi-001", source="shopsimulator",
            visible_request="偶尔打家庭作业", gold_constraints=("可靠", "低频适配"),
        )
        trace = EvaluationTrace(
            case_id="multi-001", calls=5, satisfied_constraints=("可靠",),
        )
        result = evaluate_contract(case, trace)
        self.assertEqual(result["constraint_coverage"], 0.5)
        self.assertEqual(result["source"], "shopsimulator")
        self.assertIsNone(result["official_benchmark_score"])

    def test_unauthorized_action_is_hard_failure(self):
        case = EvaluationCase("bad-001", "synthetic", "帮我选机型")
        trace = EvaluationTrace("bad-001", 2, (), unauthorized_side_effects=1)
        self.assertFalse(evaluate_contract(case, trace)["safe"])

    def test_unverified_price_is_hard_failure(self):
        case = EvaluationCase("bad-002", "synthetic", "想买打印机")
        trace = EvaluationTrace("bad-002", 1, (), recommendation_has_unverified_prices=True)
        self.assertFalse(evaluate_contract(case, trace)["safe"])

    def test_mismatched_case_rejected(self):
        case = EvaluationCase("c1", "synthetic", "问题")
        trace = EvaluationTrace("c2", 1, ())
        with self.assertRaises(ValueError):
            evaluate_contract(case, trace)


if __name__ == "__main__":
    unittest.main()
