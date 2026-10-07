import json
import tempfile
import unittest
from pathlib import Path

from runtime_lab.ledger import JsonlEventLedger, LedgerEvent
from runtime_lab.models import RunState


class LedgerTests(unittest.TestCase):
    def test_jsonl_ledger_is_append_only_and_keeps_trace_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            ledger = JsonlEventLedger(path)
            ledger.append(LedgerEvent(run_id="run-1", event_type="state_transition", from_state=RunState.CREATED, to_state=RunState.RUNNING))
            ledger.append(LedgerEvent(run_id="run-1", event_type="state_transition", from_state=RunState.RUNNING, to_state=RunState.CANDIDATE_READY))
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(2, len(lines))
            self.assertEqual(["run-1", "run-1"], [json.loads(line)["run_id"] for line in lines])

    def test_ledger_schema_does_not_persist_prompt_or_provider_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            ledger = JsonlEventLedger(path)
            ledger.append(LedgerEvent(run_id="run-1", event_type="state_transition", from_state=RunState.RUNNING, to_state=RunState.FAILED, code="provider_error", failure_type="RuntimeError"))
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("prompt", content)
            self.assertNotIn("model_output", content)
            self.assertNotIn("secret-token", content)


if __name__ == "__main__":
    unittest.main()
