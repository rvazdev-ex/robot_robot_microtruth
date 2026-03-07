from collections import defaultdict
from typing import Any
from uuid import uuid4

from trust_before_touch.config import AppConfig
from trust_before_touch.constants import AttackMode, ChallengeType, SessionState
from trust_before_touch.hardware.simulated import SimLeaderArm, SimProverArm, SimVerifierArm
from trust_before_touch.models.events import SessionEvent
from trust_before_touch.models.protocol import ScoreBreakdown, Session
from trust_before_touch.persistence.repository import SessionRepository
from trust_before_touch.protocol.challenges import ChallengeGenerator
from trust_before_touch.scoring.trust import TrustScorer
from trust_before_touch.simulation.engine import SimulationEngine
from trust_before_touch.state_machine import SessionStateMachine


class SessionManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.repo = SessionRepository(config.db_path)
        self.generator = ChallengeGenerator(config.seed)
        self.engine = SimulationEngine(config.seed, config.sim_noise)
        self.scorer = TrustScorer(
            config.scoring_weights(), config.pass_threshold, config.borderline_threshold
        )
        self._listeners: dict[str, list[Any]] = defaultdict(list)

    async def broadcast(self, session_id: str, event: SessionEvent) -> None:
        dead: list[Any] = []
        for ws in self._listeners[session_id]:
            try:
                await ws.send_json(event.model_dump(mode="json"))
            except RuntimeError:
                dead.append(ws)
        for ws in dead:
            self._listeners[session_id].remove(ws)

    def register_ws(self, session_id: str, ws: Any) -> None:
        self._listeners[session_id].append(ws)

    def create_session(self, attack_mode: AttackMode) -> Session:
        session = Session(session_id=str(uuid4()), attack_mode=attack_mode)
        self.repo.save_session(session)
        self.repo.add_event(session.session_id, SessionEvent(event_type="session_created"))
        return session

    def get_session(self, session_id: str) -> Session:
        session = self.repo.get_session(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def claim(self, session_id: str, message: str) -> Session:
        session = self.get_session(session_id)
        sm = SessionStateMachine(session.state)
        session.state = sm.transition(SessionState.CLAIM_RECEIVED)
        session.claim = message
        self.repo.save_session(session)
        self.repo.add_event(
            session_id,
            SessionEvent(event_type="claim_received", payload={"message": message}),
        )
        return session

    def challenge(self, session_id: str, challenge_type: ChallengeType | None = None) -> Session:
        session = self.get_session(session_id)
        sm = SessionStateMachine(session.state)
        session.state = sm.transition(SessionState.CHALLENGE_ISSUED)
        leader = SimLeaderArm(self.generator)
        session.challenge = leader.generate_challenge(challenge_type)
        self.repo.save_session(session)
        self.repo.add_event(
            session_id,
            SessionEvent(
                event_type="challenge_issued", payload=session.challenge.model_dump(mode="json")
            ),
        )
        return session

    def execute(self, session_id: str) -> Session:
        session = self.get_session(session_id)
        if session.challenge is None:
            raise ValueError("missing challenge")
        sm = SessionStateMachine(session.state)
        session.state = sm.transition(SessionState.EXECUTING)
        prover = SimProverArm()
        prover.execute_challenge(session.challenge)
        self.repo.save_session(session)
        self.repo.add_event(session_id, SessionEvent(event_type="executing"))
        return session

    def verify(self, session_id: str) -> Session:
        session = self.get_session(session_id)
        if session.challenge is None:
            raise ValueError("missing challenge")
        sm = SessionStateMachine(session.state)
        session.state = sm.transition(SessionState.VERIFYING)
        verifier = SimVerifierArm(self.engine, session.attack_mode)
        session.telemetry = verifier.observe_execution(session.challenge)
        score: ScoreBreakdown = self.scorer.score(session.telemetry)
        session.score = score
        final_state = SessionState.PASSED if score.verdict == "pass" else SessionState.FAILED
        session.state = sm.transition(final_state)
        self.repo.save_session(session)
        self.repo.add_event(
            session_id,
            SessionEvent(
                event_type="verified",
                payload={
                    "telemetry": session.telemetry.model_dump(mode="json"),
                    "score": score.model_dump(mode="json"),
                },
            ),
        )
        return session

    def events(self, session_id: str) -> list[SessionEvent]:
        return self.repo.list_events(session_id)
