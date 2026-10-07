import unittest

from runtime_lab.approvals import ApprovalStore
from runtime_lab.engine import WorkflowEngine
from runtime_lab.ledger import InMemoryEventLedger
from runtime_lab.models import AccessLevel, ApprovalRecord, Candidate, CapabilityDeclaration, CapabilityRequest, ReviewStatus, ReviewVerdict, RunSpec
from runtime_lab.providers import ScriptedProvider


class ApprovalAuditTests(unittest.TestCase):
    def test_successful_external_approval_is_audited_as_required_and_present(self):
        run_id = "run-approved-audit"
        spec = RunSpec(
            task="summarize synthetic fixture",
            capabilities=(CapabilityDeclaration("fixture.read", requires_human_approval=True),),
        )
        approvals = ApprovalStore()
        approvals.add(ApprovalRecord(run_id, "fixture.read", AccessLevel.READ, True, "human-reviewer"))
        provider = ScriptedProvider(
            candidates=[Candidate(spec.task, (CapabilityRequest("fixture.read"),))],
            reviews=[ReviewVerdict(ReviewStatus.PASS)],
        )
        ledger = InMemoryEventLedger()

        result = WorkflowEngine().run(spec, provider, ledger, approvals=approvals, run_id=run_id)

        self.assertEqual("verified", result.state.value)
        candidate_event = next(event for event in ledger.events if event.to_state.value == "candidate_ready")
        self.assertTrue(candidate_event.approval_required)
        self.assertTrue(candidate_event.approval_present)


if __name__ == "__main__":
    unittest.main()
