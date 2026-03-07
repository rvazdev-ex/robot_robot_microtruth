"""Session manager: orchestrates both real-time control and PCS verification."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any
from uuid import uuid4

from trust_before_touch.config import AppConfig
from trust_before_touch.constants import AttackMode, ChallengeType, ControlMode, SessionState
from trust_before_touch.control.loop import RealtimeControlLoop
from trust_before_touch.hardware.factory import create_adapters, create_realtime_hardware
from trust_before_touch.models.events import SessionEvent
from trust_before_touch.models.protocol import ScoreBreakdown, Session
from trust_before_touch.models.robot import RobotState
from trust_before_touch.persistence.repository import SessionRepository
from trust_before_touch.scoring.trust import TrustScorer
from trust_before_touch.state_machine import SessionStateMachine


class SessionManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.repo = SessionRepository(config.db_path)
        self.scorer = TrustScorer(
            config.scoring_weights(), config.pass_threshold, config.borderline_threshold
        )
        self._listeners: dict[str, list[Any]] = defaultdict(list)
        self._telemetry_listeners: list[Any] = []

        # Real-time control
        self._control_loop: RealtimeControlLoop | None = None

    # -- Real-time control API -----------------------------------------------

    @property
    def control_loop(self) -> RealtimeControlLoop | None:
        return self._control_loop

    async def start_control(self, mode: ControlMode = ControlMode.TELEOPERATION) -> RobotState:
        """Connect hardware and start the real-time control loop."""
        leader, followers, camera = create_realtime_hardware(self.config)
        self._control_loop = RealtimeControlLoop(
            self.config, leader, followers, camera
        )
        self._control_loop.on_telemetry(self._broadcast_telemetry)
        await self._control_loop.connect_all()
        await self._control_loop.start(mode)
        return self._control_loop.latest_state

    async def stop_control(self) -> RobotState | None:
        """Stop the control loop and disconnect hardware."""
        if self._control_loop is None:
            return None
        state = self._control_loop.latest_state
        await self._control_loop.stop()
        await self._control_loop.disconnect_all()
        self._control_loop = None
        return state

    def get_robot_state(self) -> RobotState:
        """Get the latest aggregated robot state."""
        if self._control_loop is not None:
            return self._control_loop.latest_state
        return RobotState()

    def register_telemetry_ws(self, ws: Any) -> None:
        self._telemetry_listeners.append(ws)

    def unregister_telemetry_ws(self, ws: Any) -> None:
        if ws in self._telemetry_listeners:
            self._telemetry_listeners.remove(ws)

    async def _broadcast_telemetry(self, state: RobotState) -> None:
        """Push real-time telemetry to all registered WebSocket clients."""
        dead: list[Any] = []
        payload = state.model_dump(mode="json")
        # Strip camera frame data to reduce bandwidth (send separately if needed)
        if "camera_frame" in payload and payload["camera_frame"] is not None:
            payload["camera_frame"].pop("data_b64", None)
        for ws in self._telemetry_listeners:
            try:
                await ws.send_json({"event_type": "telemetry", "payload": payload})
            except (RuntimeError, Exception):
                dead.append(ws)
        for ws in dead:
            self._telemetry_listeners.remove(ws)

    # -- PCS session management (existing) -----------------------------------

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
        leader, _, _ = create_adapters(
            self.config, self.config.runtime_backend, session.attack_mode
        )
        session.challenge = leader.generate_challenge(challenge_type)
        self.repo.save_session(session)
        self.repo.add_event(
            session_id,
            SessionEvent(
                event_type="challenge_issued", payload=session.challenge.model_dump(mode="json")
            ),
        )
        return session

    async def execute(self, session_id: str) -> Session:
        session = self.get_session(session_id)
        if session.challenge is None:
            raise ValueError("missing challenge")
        sm = SessionStateMachine(session.state)
        session.state = sm.transition(SessionState.EXECUTING)
        _, prover, _ = create_adapters(
            self.config, self.config.runtime_backend, session.attack_mode
        )

        trajectory = session.challenge.trajectory_points
        for i, point in enumerate(trajectory):
            await self.broadcast(
                session_id,
                SessionEvent(
                    event_type="robot_moving",
                    payload={
                        "step": i,
                        "position": point,
                        "total_steps": len(trajectory),
                    },
                ),
            )
            await asyncio.sleep(0.1)

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
        _, _, verifier = create_adapters(
            self.config, self.config.runtime_backend, session.attack_mode
        )
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
