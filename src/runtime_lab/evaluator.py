from __future__ import annotations

from typing import Any

from runtime_lab.models import AccessLevel, Candidate, EvaluationResult, EvaluationStatus, RunSpec


class DeterministicEvaluator:
    """Evaluates candidate shape/scope without granting authority."""

    def evaluate(self, spec: RunSpec, candidate: Any) -> EvaluationResult:
        if not isinstance(candidate, Candidate):
            return EvaluationResult(EvaluationStatus.INVALID, "invalid_candidate_type")
        if candidate.claimed_human_approval:
            return EvaluationResult(EvaluationStatus.INVALID, "provider_claimed_approval")
        if (
            candidate.requested_max_iterations is not None
            and candidate.requested_max_iterations > spec.max_iterations
        ) or (
            candidate.requested_max_provider_calls is not None
            and candidate.requested_max_provider_calls > spec.max_provider_calls
        ):
            return EvaluationResult(EvaluationStatus.INVALID, "budget_expansion_requested")
        if candidate.objective != spec.task:
            return EvaluationResult(EvaluationStatus.CHANGES_REQUIRED, "objective_mismatch")
        if any(request.access in {AccessLevel.WRITE, AccessLevel.EXECUTE} for request in candidate.requested_capabilities):
            return EvaluationResult(EvaluationStatus.CHANGES_REQUIRED, "forbidden_access_level")
        return EvaluationResult(EvaluationStatus.PASS, "ok")
