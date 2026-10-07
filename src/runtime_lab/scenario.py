from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime_lab.approvals import ApprovalStore
from runtime_lab.engine import WorkflowEngine
from runtime_lab.ledger import EventLedger, InMemoryEventLedger
from runtime_lab.models import AccessLevel, ApprovalRecord, Candidate, CapabilityDeclaration, CapabilityRequest, ReviewStatus, ReviewVerdict, RunSpec
from runtime_lab.providers import ScriptedProvider


def run_scenario(path: str | Path, ledger: EventLedger | None = None) -> dict[str, Any]:
    scenario = json.loads(Path(path).read_text(encoding="utf-8"))
    spec = _parse_spec(scenario)
    provider = ScriptedProvider(
        candidates=[_parse_candidate(item) for item in scenario["script"]["candidates"]],
        reviews=[_parse_review(item) for item in scenario["script"]["reviews"]],
    )
    approvals = _parse_approvals(scenario.get("approvals", []))
    actual_ledger = ledger or InMemoryEventLedger()
    result = WorkflowEngine().run(spec, provider, actual_ledger, approvals=approvals, run_id=scenario["run_id"])
    summary: dict[str, Any] = {
        "run_id": result.run_id,
        "state": result.state.value,
        "code": result.code,
        "iterations": result.iterations,
        "provider_calls": result.provider_calls,
    }
    expected = scenario.get("expected", {})
    summary["matches_expected"] = all(summary.get(key) == value for key, value in expected.items())
    if isinstance(actual_ledger, InMemoryEventLedger):
        summary["events"] = [event.to_record() for event in actual_ledger.events]
    return summary


def _parse_spec(data: dict[str, Any]) -> RunSpec:
    return RunSpec(
        task=data["task"],
        capabilities=tuple(
            CapabilityDeclaration(
                name=item["name"],
                access=AccessLevel(item.get("access", "read")),
                requires_human_approval=bool(item.get("requires_human_approval", False)),
            )
            for item in data.get("capabilities", [])
        ),
        max_iterations=int(data.get("max_iterations", 2)),
        max_provider_calls=int(data.get("max_provider_calls", 4)),
    )


def _parse_candidate(item: dict[str, Any]) -> Candidate:
    return Candidate(
        objective=item["objective"],
        requested_capabilities=tuple(
            CapabilityRequest(name=request["name"], access=AccessLevel(request.get("access", "read")))
            for request in item.get("requested_capabilities", [])
        ),
        requested_max_iterations=item.get("requested_max_iterations"),
        requested_max_provider_calls=item.get("requested_max_provider_calls"),
        claimed_human_approval=bool(item.get("claimed_human_approval", False)),
        payload=item.get("payload", {}),
    )


def _parse_review(item: dict[str, Any]) -> ReviewVerdict:
    return ReviewVerdict(status=ReviewStatus(item["status"]), reason=item.get("reason", ""))


def _parse_approvals(items: list[dict[str, Any]]) -> ApprovalStore:
    store = ApprovalStore()
    for item in items:
        store.add(
            ApprovalRecord(
                run_id=item["run_id"],
                capability=item["capability"],
                access=AccessLevel(item.get("access", "read")),
                approved=bool(item["approved"]),
                approver=item["approver"],
            )
        )
    return store
