from trust_before_touch.constants import SessionState

TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.IDLE: {SessionState.CLAIM_RECEIVED, SessionState.ABORTED},
    SessionState.CLAIM_RECEIVED: {SessionState.CHALLENGE_ISSUED, SessionState.ABORTED},
    SessionState.CHALLENGE_ISSUED: {SessionState.EXECUTING, SessionState.ABORTED},
    SessionState.EXECUTING: {SessionState.VERIFYING, SessionState.ABORTED},
    SessionState.VERIFYING: {SessionState.PASSED, SessionState.FAILED, SessionState.ABORTED},
    SessionState.PASSED: set(),
    SessionState.FAILED: set(),
    SessionState.ABORTED: set(),
}


class InvalidTransitionError(ValueError):
    pass


class SessionStateMachine:
    def __init__(self, initial_state: SessionState = SessionState.IDLE):
        self.state = initial_state

    def transition(self, new_state: SessionState) -> SessionState:
        if new_state not in TRANSITIONS[self.state]:
            raise InvalidTransitionError(f"Cannot transition from {self.state} to {new_state}")
        self.state = new_state
        return self.state
