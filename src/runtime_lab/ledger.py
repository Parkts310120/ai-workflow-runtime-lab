from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from runtime_lab.models import RunState


class LedgerWriteError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    run_id: str
    event_type: str
    from_state: RunState
    to_state: RunState
    code: str = ""
    iterations: int = 0
    provider_calls: int = 0
    evaluator_code: str = ""
    authority_code: str = ""
    approval_required: bool = False
    approval_present: bool = False
    failure_type: str = ""

    def to_record(self) -> dict[str, object]:
        record = asdict(self)
        record["from_state"] = self.from_state.value
        record["to_state"] = self.to_state.value
        return record


class EventLedger(Protocol):
    def append(self, event: LedgerEvent) -> None: ...


class InMemoryEventLedger:
    def __init__(self) -> None:
        self.events: list[LedgerEvent] = []

    def append(self, event: LedgerEvent) -> None:
        self.events.append(event)


class JsonlEventLedger:
    """Append-only sanitized operational event ledger."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: LedgerEvent) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(event.to_record(), sort_keys=True, separators=(",", ":")))
                handle.write("\n")
        except OSError as exc:
            raise LedgerWriteError("unable to append audit event") from exc
