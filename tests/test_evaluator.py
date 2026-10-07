import unittest

from runtime_lab.evaluator import DeterministicEvaluator
from runtime_lab.models import (
    AccessLevel,
    Candidate,
    CapabilityDeclaration,
    CapabilityRequest,
    EvaluationStatus,
    RunSpec,
)


class DeterministicEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.evaluator = DeterministicEvaluator()
        self.spec = RunSpec(
            task="summarize synthetic fixture",
            capabilities=(CapabilityDeclaration("fixture.read"),),
        )

    def test_valid_candidate_passes(self):
        result = self.evaluator.evaluate(
            self.spec,
            Candidate(
                objective=self.spec.task,
                requested_capabilities=(CapabilityRequest("fixture.read"),),
            ),
        )
        self.assertEqual(EvaluationStatus.PASS, result.status)
        self.assertEqual("ok", result.code)

    def test_wrong_type_is_invalid(self):
        result = self.evaluator.evaluate(self.spec, {"objective": self.spec.task})
        self.assertEqual(EvaluationStatus.INVALID, result.status)
        self.assertEqual("invalid_candidate_type", result.code)

    def test_candidate_cannot_expand_iteration_budget(self):
        result = self.evaluator.evaluate(
            self.spec,
            Candidate(objective=self.spec.task, requested_max_iterations=4),
        )
        self.assertEqual(EvaluationStatus.INVALID, result.status)
        self.assertEqual("budget_expansion_requested", result.code)

    def test_candidate_cannot_expand_provider_call_budget(self):
        result = self.evaluator.evaluate(
            self.spec,
            Candidate(objective=self.spec.task, requested_max_provider_calls=8),
        )
        self.assertEqual(EvaluationStatus.INVALID, result.status)
        self.assertEqual("budget_expansion_requested", result.code)

    def test_provider_cannot_claim_human_approval(self):
        result = self.evaluator.evaluate(
            self.spec,
            Candidate(objective=self.spec.task, claimed_human_approval=True),
        )
        self.assertEqual(EvaluationStatus.INVALID, result.status)
        self.assertEqual("provider_claimed_approval", result.code)

    def test_forbidden_write_request_requires_changes(self):
        result = self.evaluator.evaluate(
            self.spec,
            Candidate(
                objective=self.spec.task,
                requested_capabilities=(CapabilityRequest("fixture.read", AccessLevel.WRITE),),
            ),
        )
        self.assertEqual(EvaluationStatus.CHANGES_REQUIRED, result.status)
        self.assertEqual("forbidden_access_level", result.code)

    def test_objective_mismatch_requires_changes(self):
        result = self.evaluator.evaluate(self.spec, Candidate(objective="different objective"))
        self.assertEqual(EvaluationStatus.CHANGES_REQUIRED, result.status)
        self.assertEqual("objective_mismatch", result.code)


if __name__ == "__main__":
    unittest.main()
