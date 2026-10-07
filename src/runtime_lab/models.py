from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class AccessLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


class RunState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    CANDIDATE_READY = "candidate_ready"
    REVIEWED = "reviewed"
    VERIFIED = "verified"
    AWAITING_HUMAN = "awaiting_human"
    REJECTED = "rejected"
    FAILED = "failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    AUTHORITY_DENIED = "authority_denied"


class EvaluationStatus(str, Enum):
    PASS = "pass"
    CHANGES_REQUIRED = "changes_required"
    NEEDS_HUMAN = "needs_human"
    INVALID = "invalid"


class ReviewStatus(str, Enum):
    PASS = "pass"
    REVISE = "revise"
    NEEDS_HUMAN = "needs_human"


@dataclass(frozen=True, slots=True)
class CapabilityDeclaration:
    name: str
    access: AccessLevel = AccessLevel.READ
    requires_human_approval: bool = False


@dataclass(frozen=True, slots=True)
class CapabilityRequest:
    name: str
    access: AccessLevel = AccessLevel.READ


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    run_id: str
    capability: str
    access: AccessLevel
    approved: bool
    approver: str


@dataclass(frozen=True, slots=True)
class RunSpec:
    task: str
    capabilities: tuple[CapabilityDeclaration, ...] = ()
    max_iterations: int = 2
    max_provider_calls: int = 4

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("task must not be empty")
        if not 1 <= self.max_iterations <= 4:
            raise ValueError("max_iterations must be between 1 and 4")
        if not 1 <= self.max_provider_calls <= 8:
            raise ValueError("max_provider_calls must be between 1 and 8")
        names = [item.name for item in self.capabilities]
        if len(names) != len(set(names)):
            raise ValueError("capability declarations must be unique")


@dataclass(frozen=True, slots=True)
class Candidate:
    objective: str
    requested_capabilities: tuple[CapabilityRequest, ...] = ()
    requested_max_iterations: int | None = None
    requested_max_provider_calls: int | None = None
    claimed_human_approval: bool = False
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReviewVerdict:
    status: ReviewStatus
    reason: str = ""


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    status: EvaluationStatus
    code: str


@dataclass(frozen=True, slots=True)
class AuthorityDecision:
    allowed: bool
    code: str
    requires_human: bool = False


@dataclass(frozen=True, slots=True)
class RunResult:
    run_id: str
    state: RunState
    iterations: int
    provider_calls: int
    code: str
    candidate: Candidate | None = None
