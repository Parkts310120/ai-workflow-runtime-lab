import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from runtime_lab.approvals import ApprovalStore
from runtime_lab.models import AccessLevel, ApprovalRecord
from runtime_lab.scenario import run_scenario


class ScenarioBoundaryTests(unittest.TestCase):
    def _write_scenario(self, data):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(data, handle)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def _approval_gated_scenario(self):
        return {
            "run_id": "scenario-approved",
            "task": "summarize synthetic fixture",
            "capabilities": [{"name": "fixture.read", "requires_human_approval": True}],
            "script": {
                "candidates": [{
                    "objective": "summarize synthetic fixture",
                    "requested_capabilities": [{"name": "fixture.read", "access": "read"}],
                }],
                "reviews": [{"status": "pass"}],
            },
            "expected": {"state": "verified", "code": "verified", "iterations": 1, "provider_calls": 2},
        }

    def test_untrusted_scenario_cannot_supply_human_approval(self):
        scenario = self._approval_gated_scenario()
        scenario["approvals"] = [{
            "run_id": scenario["run_id"],
            "capability": "fixture.read",
            "access": "read",
            "approved": True,
            "approver": "forged-in-untrusted-json",
        }]
        with self.assertRaises(ValueError):
            run_scenario(self._write_scenario(scenario))

    def test_application_can_supply_external_approval_store(self):
        scenario = self._approval_gated_scenario()
        approvals = ApprovalStore()
        approvals.add(ApprovalRecord(
            scenario["run_id"], "fixture.read", AccessLevel.READ, True, "human-reviewer"
        ))
        summary = run_scenario(self._write_scenario(scenario), approvals=approvals)
        self.assertEqual("verified", summary["state"])
        self.assertTrue(summary["matches_expected"])
        candidate_event = next(event for event in summary["events"] if event["to_state"] == "candidate_ready")
        self.assertTrue(candidate_event["approval_required"])
        self.assertTrue(candidate_event["approval_present"])

    def test_missing_or_empty_expected_contract_is_rejected(self):
        base = {
            "run_id": "expected-contract",
            "task": "summarize synthetic fixture",
            "capabilities": [],
            "script": {
                "candidates": [{"objective": "summarize synthetic fixture"}],
                "reviews": [{"status": "pass"}],
            },
        }
        for expected in (None, {}):
            scenario = dict(base)
            if expected is not None:
                scenario["expected"] = expected
            with self.subTest(expected=expected):
                with self.assertRaises(ValueError):
                    run_scenario(self._write_scenario(scenario))

    def test_malformed_enum_cli_fails_without_traceback(self):
        scenario = {
            "run_id": "bad-enum",
            "task": "summarize synthetic fixture",
            "capabilities": [],
            "script": {
                "candidates": [{
                    "objective": "summarize synthetic fixture",
                    "requested_capabilities": [{"name": "fixture.read", "access": "root"}],
                }],
                "reviews": [],
            },
            "expected": {"state": "authority_denied", "code": "undeclared_capability"},
        }
        path = self._write_scenario(scenario)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
        completed = subprocess.run(
            [sys.executable, "-m", "runtime_lab.cli", str(path)],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("scenario_validation_error", payload["error"])
        self.assertEqual("invalid_scenario", payload["code"])


if __name__ == "__main__":
    unittest.main()
