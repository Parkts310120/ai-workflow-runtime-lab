from __future__ import annotations

from runtime_lab.models import RunState


class InvalidTransition(RuntimeError):
    pass


_ALLOWED: dict[RunState, frozenset[RunState]] = {
    RunState.CREATED: frozenset({RunState.RUNNING, RunState.FAILED}),
    RunState.RUNNING: frozenset({
        RunState.CANDIDATE_READY,
        RunState.AWAITING_HUMAN,
        RunState.AUTHORITY_DENIED,
        RunState.REJECTED,
        RunState.BUDGET_EXHAUSTED,
        RunState.FAILED,
    }),
    RunState.CANDIDATE_READY: frozenset({
        RunState.REVIEWED,
        RunState.AWAITING_HUMAN,
        RunState.RUNNING,
        RunState.BUDGET_EXHAUSTED,
        RunState.FAILED,
    }),
    RunState.REVIEWED: frozenset({RunState.VERIFIED, RunState.RUNNING, RunState.FAILED}),
    RunState.AWAITING_HUMAN: frozenset({RunState.REJECTED}),
    RunState.VERIFIED: frozenset(),
    RunState.REJECTED: frozenset(),
    RunState.FAILED: frozenset(),
    RunState.BUDGET_EXHAUSTED: frozenset(),
    RunState.AUTHORITY_DENIED: frozenset(),
}


class RunStateMachine:
    def __init__(self) -> None:
        self._state = RunState.CREATED

    @property
    def state(self) -> RunState:
        return self._state

    def transition(self, next_state: RunState) -> None:
        if next_state not in _ALLOWED[self._state]:
            raise InvalidTransition(f"invalid transition: {self._state.value} -> {next_state.value}")
        self._state = next_state
