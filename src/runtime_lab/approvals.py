from __future__ import annotations

from runtime_lab.models import AccessLevel, ApprovalRecord


class ApprovalStore:
    """External approval records. Provider output never writes to this store."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str, AccessLevel], ApprovalRecord] = {}

    def add(self, record: ApprovalRecord) -> None:
        key = (record.run_id, record.capability, record.access)
        self._records[key] = record

    def find(self, run_id: str, capability: str, access: AccessLevel) -> ApprovalRecord | None:
        return self._records.get((run_id, capability, access))
