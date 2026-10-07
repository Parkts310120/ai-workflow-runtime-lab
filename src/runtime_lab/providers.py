from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from runtime_lab.models import Candidate, ReviewVerdict, RunSpec


class ProviderPort(Protocol):
    def generate(self, spec: RunSpec, iteration: int) -> object: ...
    def review(self, candidate: Candidate, iteration: int) -> object: ...


class ScriptExhausted(RuntimeError):
    pass


class ScriptedProvider:
    """Deterministic provider for tests and examples only."""

    def __init__(self, candidates: Iterable[object], reviews: Iterable[object]) -> None:
        self._candidates = iter(candidates)
        self._reviews = iter(reviews)
        self.generate_calls = 0
        self.review_calls = 0

    def generate(self, spec: RunSpec, iteration: int) -> object:
        self.generate_calls += 1
        return self._next(self._candidates, "candidate")

    def review(self, candidate: Candidate, iteration: int) -> object:
        self.review_calls += 1
        return self._next(self._reviews, "review")

    @staticmethod
    def _next(iterator, kind: str) -> object:
        try:
            item = next(iterator)
        except StopIteration as exc:
            raise ScriptExhausted(f"script has no {kind} response") from exc
        if isinstance(item, BaseException):
            raise item
        return item
