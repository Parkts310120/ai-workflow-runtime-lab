import unittest
from pathlib import Path

from runtime_lab.scenario import run_scenario


ROOT = Path(__file__).resolve().parents[1]


class ExampleScenarioTests(unittest.TestCase):
    def test_success_example_is_deterministic(self):
        summary = run_scenario(ROOT / "examples" / "read_only_success.json")
        self.assertEqual("verified", summary["state"])
        self.assertEqual("verified", summary["code"])
        self.assertEqual(1, summary["iterations"])
        self.assertEqual(2, summary["provider_calls"])
        self.assertTrue(summary["matches_expected"])

    def test_authority_denial_example_is_deterministic(self):
        summary = run_scenario(ROOT / "examples" / "authority_denial.json")
        self.assertEqual("authority_denied", summary["state"])
        self.assertEqual("undeclared_capability", summary["code"])
        self.assertEqual(1, summary["provider_calls"])
        self.assertTrue(summary["matches_expected"])

    def test_budget_exhaustion_example_is_deterministic(self):
        summary = run_scenario(ROOT / "examples" / "budget_exhaustion.json")
        self.assertEqual("budget_exhausted", summary["state"])
        self.assertEqual("iteration_budget_exhausted", summary["code"])
        self.assertEqual(2, summary["provider_calls"])
        self.assertTrue(summary["matches_expected"])


if __name__ == "__main__":
    unittest.main()
