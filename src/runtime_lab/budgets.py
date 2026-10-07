from __future__ import annotations


class BudgetExhausted(RuntimeError):
    def __init__(self, kind: str) -> None:
        super().__init__(f"{kind} budget exhausted")
        self.kind = kind


class BudgetGuard:
    __slots__ = ("_max_iterations", "_max_provider_calls", "iterations", "provider_calls")

    def __init__(self, max_iterations: int, max_provider_calls: int) -> None:
        self._max_iterations = max_iterations
        self._max_provider_calls = max_provider_calls
        self.iterations = 0
        self.provider_calls = 0

    @property
    def max_iterations(self) -> int:
        return self._max_iterations

    @property
    def max_provider_calls(self) -> int:
        return self._max_provider_calls

    def begin_iteration(self) -> int:
        if self.iterations >= self._max_iterations:
            raise BudgetExhausted("iteration")
        self.iterations += 1
        return self.iterations

    def consume_provider_call(self) -> int:
        if self.provider_calls >= self._max_provider_calls:
            raise BudgetExhausted("provider_call")
        self.provider_calls += 1
        return self.provider_calls
