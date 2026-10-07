import unittest

from runtime_lab.models import RunState
from runtime_lab.state_machine import InvalidTransition, RunStateMachine


class RunStateMachineTests(unittest.TestCase):
    def test_happy_path_transitions_are_explicit(self):
        machine = RunStateMachine()
        machine.transition(RunState.RUNNING)
        machine.transition(RunState.CANDIDATE_READY)
        machine.transition(RunState.REVIEWED)
        machine.transition(RunState.VERIFIED)
        self.assertEqual(RunState.VERIFIED, machine.state)

    def test_invalid_transition_is_rejected(self):
        machine = RunStateMachine()
        with self.assertRaises(InvalidTransition):
            machine.transition(RunState.VERIFIED)

    def test_terminal_state_cannot_resume(self):
        machine = RunStateMachine()
        machine.transition(RunState.RUNNING)
        machine.transition(RunState.AUTHORITY_DENIED)
        with self.assertRaises(InvalidTransition):
            machine.transition(RunState.RUNNING)


if __name__ == "__main__":
    unittest.main()
