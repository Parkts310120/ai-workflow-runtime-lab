from __future__ import annotations

from uuid import uuid4

from runtime_lab.approvals import ApprovalStore
from runtime_lab.budgets import BudgetExhausted, BudgetGuard
from runtime_lab.evaluator import DeterministicEvaluator
from runtime_lab.ledger import EventLedger, LedgerEvent, LedgerWriteError
from runtime_lab.models import (
    Candidate,
    EvaluationStatus,
    ReviewStatus,
    ReviewVerdict,
    RunResult,
    RunSpec,
    RunState,
)
from runtime_lab.policy import AuthorityPolicy
from runtime_lab.providers import ProviderPort
from runtime_lab.state_machine import RunStateMachine


class WorkflowEngine:
    def __init__(
        self,
        evaluator: DeterministicEvaluator | None = None,
        policy: AuthorityPolicy | None = None,
    ) -> None:
        self._evaluator = evaluator or DeterministicEvaluator()
        self._policy = policy or AuthorityPolicy()

    def run(
        self,
        spec: RunSpec,
        provider: ProviderPort,
        ledger: EventLedger,
        approvals: ApprovalStore | None = None,
        run_id: str | None = None,
    ) -> RunResult:
        actual_run_id = run_id or str(uuid4())
        approval_store = approvals or ApprovalStore()
        budget = BudgetGuard(spec.max_iterations, spec.max_provider_calls)
        machine = RunStateMachine()
        candidate: Candidate | None = None

        if not self._transition(ledger, actual_run_id, machine, RunState.RUNNING, budget, "run_started"):
            return self._audit_failure(actual_run_id, budget, candidate)

        while True:
            try:
                budget.begin_iteration()
            except BudgetExhausted:
                if not self._transition(ledger, actual_run_id, machine, RunState.BUDGET_EXHAUSTED, budget, "iteration_budget_exhausted"):
                    return self._audit_failure(actual_run_id, budget, candidate)
                return self._result(actual_run_id, machine, budget, "iteration_budget_exhausted", candidate)

            try:
                budget.consume_provider_call()
            except BudgetExhausted:
                if not self._transition(ledger, actual_run_id, machine, RunState.BUDGET_EXHAUSTED, budget, "provider_call_budget_exhausted"):
                    return self._audit_failure(actual_run_id, budget, candidate)
                return self._result(actual_run_id, machine, budget, "provider_call_budget_exhausted", candidate)

            try:
                raw_candidate = provider.generate(spec, budget.iterations)
            except Exception as exc:
                code = f"provider_error:{type(exc).__name__}"
                if not self._transition(ledger, actual_run_id, machine, RunState.FAILED, budget, code, failure_type=type(exc).__name__):
                    return self._audit_failure(actual_run_id, budget, candidate)
                return self._result(actual_run_id, machine, budget, code, candidate)

            evaluation = self._evaluator.evaluate(spec, raw_candidate)
            if evaluation.status is not EvaluationStatus.PASS:
                if not self._transition(ledger, actual_run_id, machine, RunState.FAILED, budget, evaluation.code, evaluator_code=evaluation.code):
                    return self._audit_failure(actual_run_id, budget, candidate)
                return self._result(actual_run_id, machine, budget, evaluation.code, candidate)

            candidate = raw_candidate
            authority_code = "no_capability_requested"
            approval_required = False
            approval_present = False
            for request in candidate.requested_capabilities:
                decision = self._policy.evaluate(actual_run_id, spec, request, machine.state, approval_store)
                authority_code = decision.code
                approval_required = decision.requires_human
                approval_present = approval_store.find(actual_run_id, request.name, request.access) is not None
                if not decision.allowed:
                    if decision.code == "human_approval_required":
                        target = RunState.AWAITING_HUMAN
                    elif decision.code == "human_rejected":
                        target = RunState.REJECTED
                    else:
                        target = RunState.AUTHORITY_DENIED
                    if not self._transition(ledger, actual_run_id, machine, target, budget, decision.code, evaluator_code=evaluation.code, authority_code=decision.code, approval_required=decision.requires_human, approval_present=approval_present):
                        return self._audit_failure(actual_run_id, budget, candidate)
                    return self._result(actual_run_id, machine, budget, decision.code, candidate)

            if not self._transition(ledger, actual_run_id, machine, RunState.CANDIDATE_READY, budget, "candidate_ready", evaluator_code=evaluation.code, authority_code=authority_code, approval_required=approval_required, approval_present=approval_present):
                return self._audit_failure(actual_run_id, budget, candidate)

            try:
                budget.consume_provider_call()
            except BudgetExhausted:
                if not self._transition(ledger, actual_run_id, machine, RunState.BUDGET_EXHAUSTED, budget, "provider_call_budget_exhausted"):
                    return self._audit_failure(actual_run_id, budget, candidate)
                return self._result(actual_run_id, machine, budget, "provider_call_budget_exhausted", candidate)

            try:
                raw_review = provider.review(candidate, budget.iterations)
            except Exception as exc:
                code = f"provider_error:{type(exc).__name__}"
                if not self._transition(ledger, actual_run_id, machine, RunState.FAILED, budget, code, failure_type=type(exc).__name__):
                    return self._audit_failure(actual_run_id, budget, candidate)
                return self._result(actual_run_id, machine, budget, code, candidate)

            if not isinstance(raw_review, ReviewVerdict):
                code = "invalid_review_type"
                if not self._transition(ledger, actual_run_id, machine, RunState.FAILED, budget, code):
                    return self._audit_failure(actual_run_id, budget, candidate)
                return self._result(actual_run_id, machine, budget, code, candidate)

            if raw_review.status is ReviewStatus.REVISE:
                if not self._transition(ledger, actual_run_id, machine, RunState.RUNNING, budget, "review_revise"):
                    return self._audit_failure(actual_run_id, budget, candidate)
                continue

            if raw_review.status is ReviewStatus.NEEDS_HUMAN:
                if not self._transition(ledger, actual_run_id, machine, RunState.AWAITING_HUMAN, budget, "review_needs_human"):
                    return self._audit_failure(actual_run_id, budget, candidate)
                return self._result(actual_run_id, machine, budget, "review_needs_human", candidate)

            if not self._transition(ledger, actual_run_id, machine, RunState.REVIEWED, budget, "review_pass"):
                return self._audit_failure(actual_run_id, budget, candidate)
            if not self._transition(ledger, actual_run_id, machine, RunState.VERIFIED, budget, "verified"):
                return self._audit_failure(actual_run_id, budget, candidate)
            return self._result(actual_run_id, machine, budget, "verified", candidate)

    @staticmethod
    def _transition(ledger: EventLedger, run_id: str, machine: RunStateMachine, next_state: RunState, budget: BudgetGuard, code: str, *, evaluator_code: str = "", authority_code: str = "", approval_required: bool = False, approval_present: bool = False, failure_type: str = "") -> bool:
        event = LedgerEvent(run_id=run_id, event_type="state_transition", from_state=machine.state, to_state=next_state, code=code, iterations=budget.iterations, provider_calls=budget.provider_calls, evaluator_code=evaluator_code, authority_code=authority_code, approval_required=approval_required, approval_present=approval_present, failure_type=failure_type)
        try:
            ledger.append(event)
        except LedgerWriteError:
            return False
        machine.transition(next_state)
        return True

    @staticmethod
    def _result(run_id: str, machine: RunStateMachine, budget: BudgetGuard, code: str, candidate: Candidate | None) -> RunResult:
        return RunResult(run_id, machine.state, budget.iterations, budget.provider_calls, code, candidate)

    @staticmethod
    def _audit_failure(run_id: str, budget: BudgetGuard, candidate: Candidate | None) -> RunResult:
        return RunResult(run_id, RunState.FAILED, budget.iterations, budget.provider_calls, "audit_failure", candidate)
