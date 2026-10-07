import unittest

from runtime_lab.budgets import BudgetExhausted, BudgetGuard
from runtime_lab.models import RunSpec


class BudgetGuardTests(unittest.TestCase):
    def test_default_budgets_are_bounded(self):
        spec = RunSpec(task="synthetic")
        self.assertEqual(2, spec.max_iterations)
        self.assertEqual(4, spec.max_provider_calls)

    def test_configuration_ceiling_rejects_excessive_iterations(self):
        with self.assertRaises(ValueError):
            RunSpec(task="synthetic", max_iterations=5)

    def test_configuration_ceiling_rejects_excessive_provider_calls(self):
        with self.assertRaises(ValueError):
            RunSpec(task="synthetic", max_provider_calls=9)

    def test_iteration_limit_is_checked_before_increment(self):
        guard = BudgetGuard(max_iterations=1, max_provider_calls=4)
        guard.begin_iteration()
        with self.assertRaises(BudgetExhausted):
            guard.begin_iteration()
        self.assertEqual(1, guard.iterations)

    def test_provider_call_limit_is_checked_before_call(self):
        guard = BudgetGuard(max_iterations=2, max_provider_calls=1)
        guard.consume_provider_call()
        with self.assertRaises(BudgetExhausted):
            guard.consume_provider_call()
        self.assertEqual(1, guard.provider_calls)

    def test_budget_cannot_be_expanded_at_runtime(self):
        guard = BudgetGuard(max_iterations=2, max_provider_calls=4)
        with self.assertRaises(AttributeError):
            guard.max_provider_calls = 8


if __name__ == "__main__":
    unittest.main()
