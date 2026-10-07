from __future__ import annotations

from runtime_lab.approvals import ApprovalStore
from runtime_lab.models import (
    AccessLevel,
    AuthorityDecision,
    CapabilityDeclaration,
    CapabilityRequest,
    RunSpec,
    RunState,
)


_ACCESS_RANK = {
    AccessLevel.READ: 1,
    AccessLevel.WRITE: 2,
    AccessLevel.EXECUTE: 3,
}


class AuthorityPolicy:
    """Deny-by-default authority policy for the bounded public R1 surface."""

    _KNOWN_CAPABILITIES = frozenset({"fixture.read"})
    _LEGAL_STATES = frozenset({RunState.RUNNING})

    def evaluate(
        self,
        run_id: str,
        spec: RunSpec,
        request: CapabilityRequest,
        state: RunState,
        approvals: ApprovalStore,
    ) -> AuthorityDecision:
        if state not in self._LEGAL_STATES:
            return AuthorityDecision(False, "invalid_state")

        declaration = self._find_declaration(spec, request.name)
        if declaration is None:
            return AuthorityDecision(False, "undeclared_capability")
        if request.name not in self._KNOWN_CAPABILITIES:
            return AuthorityDecision(False, "unknown_capability")
        if _ACCESS_RANK[request.access] > _ACCESS_RANK[declaration.access]:
            return AuthorityDecision(False, "access_escalation")
        if request.access in {AccessLevel.WRITE, AccessLevel.EXECUTE}:
            return AuthorityDecision(False, "forbidden_access_level")
        if declaration.access in {AccessLevel.WRITE, AccessLevel.EXECUTE}:
            return AuthorityDecision(False, "forbidden_access_level")

        if declaration.requires_human_approval:
            approval = approvals.find(run_id, request.name, request.access)
            if approval is None:
                return AuthorityDecision(False, "human_approval_required", requires_human=True)
            if not approval.approved:
                return AuthorityDecision(False, "human_rejected", requires_human=True)
            return AuthorityDecision(True, "allowed", requires_human=True)

        return AuthorityDecision(True, "allowed")

    @staticmethod
    def _find_declaration(spec: RunSpec, name: str) -> CapabilityDeclaration | None:
        for declaration in spec.capabilities:
            if declaration.name == name:
                return declaration
        return None
