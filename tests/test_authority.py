import unittest

from runtime_lab.approvals import ApprovalStore
from runtime_lab.models import (
    AccessLevel,
    ApprovalRecord,
    CapabilityDeclaration,
    CapabilityRequest,
    RunSpec,
    RunState,
)
from runtime_lab.policy import AuthorityPolicy


class AuthorityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = AuthorityPolicy()
        self.run_id = "run-001"

    def test_exact_declared_read_capability_is_allowed(self):
        spec = RunSpec(task="synthetic", capabilities=(CapabilityDeclaration("fixture.read"),))
        decision = self.policy.evaluate(self.run_id, spec, CapabilityRequest("fixture.read"), RunState.RUNNING, ApprovalStore())
        self.assertTrue(decision.allowed)
        self.assertEqual("allowed", decision.code)

    def test_undeclared_capability_is_denied(self):
        decision = self.policy.evaluate(self.run_id, RunSpec(task="synthetic"), CapabilityRequest("fixture.read"), RunState.RUNNING, ApprovalStore())
        self.assertFalse(decision.allowed)
        self.assertEqual("undeclared_capability", decision.code)

    def test_unknown_capability_is_denied_even_if_declared(self):
        spec = RunSpec(task="synthetic", capabilities=(CapabilityDeclaration("unknown.read"),))
        decision = self.policy.evaluate(self.run_id, spec, CapabilityRequest("unknown.read"), RunState.RUNNING, ApprovalStore())
        self.assertFalse(decision.allowed)
        self.assertEqual("unknown_capability", decision.code)

    def test_access_escalation_is_denied(self):
        spec = RunSpec(task="synthetic", capabilities=(CapabilityDeclaration("fixture.read", AccessLevel.READ),))
        decision = self.policy.evaluate(self.run_id, spec, CapabilityRequest("fixture.read", AccessLevel.WRITE), RunState.RUNNING, ApprovalStore())
        self.assertFalse(decision.allowed)
        self.assertEqual("access_escalation", decision.code)

    def test_write_is_denied_in_r1(self):
        spec = RunSpec(task="synthetic", capabilities=(CapabilityDeclaration("fixture.read", AccessLevel.WRITE),))
        decision = self.policy.evaluate(self.run_id, spec, CapabilityRequest("fixture.read", AccessLevel.WRITE), RunState.RUNNING, ApprovalStore())
        self.assertFalse(decision.allowed)
        self.assertEqual("forbidden_access_level", decision.code)

    def test_execute_is_denied_in_r1(self):
        spec = RunSpec(task="synthetic", capabilities=(CapabilityDeclaration("fixture.read", AccessLevel.EXECUTE),))
        decision = self.policy.evaluate(self.run_id, spec, CapabilityRequest("fixture.read", AccessLevel.EXECUTE), RunState.RUNNING, ApprovalStore())
        self.assertFalse(decision.allowed)
        self.assertEqual("forbidden_access_level", decision.code)

    def test_missing_required_approval_blocks_without_auto_approval(self):
        spec = RunSpec(task="synthetic", capabilities=(CapabilityDeclaration("fixture.read", requires_human_approval=True),))
        decision = self.policy.evaluate(self.run_id, spec, CapabilityRequest("fixture.read"), RunState.RUNNING, ApprovalStore())
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_human)
        self.assertEqual("human_approval_required", decision.code)

    def test_exact_external_approval_allows_declared_read(self):
        store = ApprovalStore()
        store.add(ApprovalRecord(run_id=self.run_id, capability="fixture.read", access=AccessLevel.READ, approved=True, approver="human-reviewer"))
        spec = RunSpec(task="synthetic", capabilities=(CapabilityDeclaration("fixture.read", requires_human_approval=True),))
        decision = self.policy.evaluate(self.run_id, spec, CapabilityRequest("fixture.read"), RunState.RUNNING, store)
        self.assertTrue(decision.allowed)
        self.assertEqual("allowed", decision.code)

    def test_external_rejection_is_terminal_policy_denial(self):
        store = ApprovalStore()
        store.add(ApprovalRecord(run_id=self.run_id, capability="fixture.read", access=AccessLevel.READ, approved=False, approver="human-reviewer"))
        spec = RunSpec(task="synthetic", capabilities=(CapabilityDeclaration("fixture.read", requires_human_approval=True),))
        decision = self.policy.evaluate(self.run_id, spec, CapabilityRequest("fixture.read"), RunState.RUNNING, store)
        self.assertFalse(decision.allowed)
        self.assertEqual("human_rejected", decision.code)


if __name__ == "__main__":
    unittest.main()
