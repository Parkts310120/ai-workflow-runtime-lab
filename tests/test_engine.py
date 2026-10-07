import unittest

from runtime_lab.approvals import ApprovalStore
from runtime_lab.engine import WorkflowEngine
from runtime_lab.ledger import InMemoryEventLedger, LedgerWriteError
from runtime_lab.models import AccessLevel, ApprovalRecord, Candidate, CapabilityDeclaration, CapabilityRequest, ReviewStatus, ReviewVerdict, RunSpec, RunState
from runtime_lab.providers import ScriptedProvider


class FailingLedger:
    def append(self, event):
        raise LedgerWriteError("simulated audit failure")


class WorkflowEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = WorkflowEngine()
        self.spec = RunSpec(task="summarize synthetic fixture", capabilities=(CapabilityDeclaration("fixture.read"),))

    def test_scripted_success_reaches_verified_with_stable_events(self):
        provider = ScriptedProvider(candidates=[Candidate(self.spec.task, (CapabilityRequest("fixture.read"),))], reviews=[ReviewVerdict(ReviewStatus.PASS, "bounded result")])
        ledger = InMemoryEventLedger()
        result = self.engine.run(self.spec, provider, ledger, run_id="run-success")
        self.assertEqual(RunState.VERIFIED, result.state)
        self.assertEqual(1, result.iterations)
        self.assertEqual(2, result.provider_calls)
        self.assertEqual(["running", "candidate_ready", "reviewed", "verified"], [event.to_state.value for event in ledger.events])

    def test_undeclared_provider_capability_is_authority_denied(self):
        provider = ScriptedProvider(candidates=[Candidate(self.spec.task, (CapabilityRequest("network.read"),))], reviews=[])
        result = self.engine.run(self.spec, provider, InMemoryEventLedger(), run_id="run-denied")
        self.assertEqual(RunState.AUTHORITY_DENIED, result.state)
        self.assertEqual("undeclared_capability", result.code)
        self.assertEqual(1, result.provider_calls)

    def test_provider_budget_expansion_fails_closed(self):
        provider = ScriptedProvider(candidates=[Candidate(self.spec.task, requested_max_provider_calls=8)], reviews=[])
        result = self.engine.run(self.spec, provider, InMemoryEventLedger(), run_id="run-budget-expand")
        self.assertEqual(RunState.FAILED, result.state)
        self.assertEqual("budget_expansion_requested", result.code)

    def test_provider_claimed_approval_fails_closed(self):
        provider = ScriptedProvider(candidates=[Candidate(self.spec.task, claimed_human_approval=True)], reviews=[])
        result = self.engine.run(self.spec, provider, InMemoryEventLedger(), run_id="run-fake-approval")
        self.assertEqual(RunState.FAILED, result.state)
        self.assertEqual("provider_claimed_approval", result.code)

    def test_missing_external_approval_waits_for_human(self):
        spec = RunSpec(task=self.spec.task, capabilities=(CapabilityDeclaration("fixture.read", requires_human_approval=True),))
        provider = ScriptedProvider(candidates=[Candidate(spec.task, (CapabilityRequest("fixture.read"),))], reviews=[])
        result = self.engine.run(spec, provider, InMemoryEventLedger(), run_id="run-await")
        self.assertEqual(RunState.AWAITING_HUMAN, result.state)
        self.assertEqual("human_approval_required", result.code)

    def test_external_approval_allows_run_to_continue(self):
        run_id = "run-approved"
        spec = RunSpec(task=self.spec.task, capabilities=(CapabilityDeclaration("fixture.read", requires_human_approval=True),))
        approvals = ApprovalStore()
        approvals.add(ApprovalRecord(run_id, "fixture.read", AccessLevel.READ, True, "human-reviewer"))
        provider = ScriptedProvider(candidates=[Candidate(spec.task, (CapabilityRequest("fixture.read"),))], reviews=[ReviewVerdict(ReviewStatus.PASS)])
        result = self.engine.run(spec, provider, InMemoryEventLedger(), approvals=approvals, run_id=run_id)
        self.assertEqual(RunState.VERIFIED, result.state)

    def test_external_rejection_is_terminal_rejected(self):
        run_id = "run-rejected"
        spec = RunSpec(task=self.spec.task, capabilities=(CapabilityDeclaration("fixture.read", requires_human_approval=True),))
        approvals = ApprovalStore()
        approvals.add(ApprovalRecord(run_id, "fixture.read", AccessLevel.READ, False, "human-reviewer"))
        provider = ScriptedProvider(candidates=[Candidate(spec.task, (CapabilityRequest("fixture.read"),))], reviews=[])
        result = self.engine.run(spec, provider, InMemoryEventLedger(), approvals=approvals, run_id=run_id)
        self.assertEqual(RunState.REJECTED, result.state)
        self.assertEqual("human_rejected", result.code)

    def test_iteration_exhaustion_stops_refinement(self):
        spec = RunSpec(task=self.spec.task, max_iterations=1, max_provider_calls=4)
        provider = ScriptedProvider(candidates=[Candidate(spec.task)], reviews=[ReviewVerdict(ReviewStatus.REVISE, "revise")])
        result = self.engine.run(spec, provider, InMemoryEventLedger(), run_id="run-iteration-budget")
        self.assertEqual(RunState.BUDGET_EXHAUSTED, result.state)
        self.assertEqual("iteration_budget_exhausted", result.code)
        self.assertEqual(2, result.provider_calls)

    def test_provider_call_budget_stops_before_review_call(self):
        spec = RunSpec(task=self.spec.task, max_iterations=2, max_provider_calls=1)
        provider = ScriptedProvider(candidates=[Candidate(spec.task)], reviews=[ReviewVerdict(ReviewStatus.PASS)])
        result = self.engine.run(spec, provider, InMemoryEventLedger(), run_id="run-call-budget")
        self.assertEqual(RunState.BUDGET_EXHAUSTED, result.state)
        self.assertEqual("provider_call_budget_exhausted", result.code)
        self.assertEqual(1, provider.generate_calls)
        self.assertEqual(0, provider.review_calls)

    def test_malformed_provider_response_consumes_attempted_call(self):
        provider = ScriptedProvider(candidates=[{"not": "candidate"}], reviews=[])
        result = self.engine.run(self.spec, provider, InMemoryEventLedger(), run_id="run-malformed")
        self.assertEqual(RunState.FAILED, result.state)
        self.assertEqual("invalid_candidate_type", result.code)
        self.assertEqual(1, result.provider_calls)

    def test_provider_exception_is_sanitized(self):
        provider = ScriptedProvider(candidates=[RuntimeError("secret-token-123")], reviews=[])
        ledger = InMemoryEventLedger()
        result = self.engine.run(self.spec, provider, ledger, run_id="run-provider-error")
        self.assertEqual(RunState.FAILED, result.state)
        self.assertEqual("provider_error:RuntimeError", result.code)
        self.assertNotIn("secret-token-123", repr(ledger.events))

    def test_ledger_failure_stops_progression_before_provider_call(self):
        provider = ScriptedProvider(candidates=[Candidate(self.spec.task)], reviews=[])
        result = self.engine.run(self.spec, provider, FailingLedger(), run_id="run-audit-failure")
        self.assertEqual(RunState.FAILED, result.state)
        self.assertEqual("audit_failure", result.code)
        self.assertEqual(0, provider.generate_calls)


if __name__ == "__main__":
    unittest.main()
