import pytest

from trust_before_touch.constants import SessionState
from trust_before_touch.state_machine import InvalidTransitionError, SessionStateMachine


def test_happy_path_transitions() -> None:
    sm = SessionStateMachine()
    assert sm.transition(SessionState.CLAIM_RECEIVED) == SessionState.CLAIM_RECEIVED
    assert sm.transition(SessionState.CHALLENGE_ISSUED) == SessionState.CHALLENGE_ISSUED
    assert sm.transition(SessionState.EXECUTING) == SessionState.EXECUTING
    assert sm.transition(SessionState.VERIFYING) == SessionState.VERIFYING
    assert sm.transition(SessionState.PASSED) == SessionState.PASSED


def test_invalid_transition() -> None:
    sm = SessionStateMachine()
    with pytest.raises(InvalidTransitionError):
        sm.transition(SessionState.VERIFYING)
