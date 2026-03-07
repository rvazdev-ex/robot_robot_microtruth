"""FastAPI application with real-time robot control and PCS verification endpoints."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from trust_before_touch.config import load_config
from trust_before_touch.constants import ControlMode
from trust_before_touch.hardware.lerobot_so101 import LeRobotUnavailableError
from trust_before_touch.models.api import ClaimRequest, ExecuteRequest, SessionCreateRequest
from trust_before_touch.models.events import SessionEvent
from trust_before_touch.models.protocol import ScoreBreakdown, Session
from trust_before_touch.models.robot import RobotState
from trust_before_touch.protocol.session_manager import SessionManager


def _templates_directory() -> Path:
    return Path(str(files("trust_before_touch").joinpath("dashboard/templates")))


def create_app() -> FastAPI:
    config = load_config()
    manager = SessionManager(config)
    app = FastAPI(title="trust-before-touch-so101")
    templates = Jinja2Templates(directory=str(_templates_directory()))

    # -- Health & Config -----------------------------------------------------

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/config")
    def get_config() -> dict[str, float | int | str]:
        return config.model_dump()

    # -- Real-time Robot Control ---------------------------------------------

    @app.post("/control/start")
    async def start_control(
        mode: ControlMode = ControlMode.TELEOPERATION,
    ) -> dict[str, str | object]:
        """Connect hardware and start the real-time control loop."""
        try:
            state = await manager.start_control(mode)
        except LeRobotUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {"status": "started", "mode": str(mode), "state": state.model_dump(mode="json")}

    @app.post("/control/stop")
    async def stop_control() -> dict[str, str | object | None]:
        """Stop the control loop and disconnect hardware."""
        state = await manager.stop_control()
        payload = state.model_dump(mode="json") if state else None
        return {"status": "stopped", "final_state": payload}

    @app.get("/control/state")
    def get_robot_state() -> RobotState:
        """Get the latest aggregated robot state."""
        return manager.get_robot_state()

    @app.get("/control/recording")
    def get_recording() -> dict[str, object | None]:
        """Get the current trajectory recording (if in recording mode)."""
        loop = manager.control_loop
        if loop is None or loop.recording is None:
            return {"recording": None}
        rec = loop.recording
        return {
            "recording": {
                "num_points": rec.num_points,
                "duration_ms": rec.duration_ms,
                "tracking_error": rec.tracking_error(),
            }
        }

    @app.websocket("/ws/telemetry")
    async def ws_telemetry(websocket: WebSocket) -> None:
        """Real-time telemetry stream via WebSocket.

        Pushes joint positions, velocities, and control loop stats at
        the configured telemetry frequency.
        """
        await websocket.accept()
        manager.register_telemetry_ws(websocket)
        await websocket.send_json({
            "event_type": "connected",
            "control_frequency_hz": config.control_frequency_hz,
            "telemetry_frequency_hz": config.telemetry_frequency_hz,
            "backend": str(config.runtime_backend),
        })
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            manager.unregister_telemetry_ws(websocket)

    # -- PCS Session Management (existing) -----------------------------------

    @app.post("/sessions")
    def create_session(req: SessionCreateRequest) -> Session:
        return manager.create_session(req.attack_mode)

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> Session:
        try:
            return manager.get_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc

    @app.post("/sessions/{session_id}/claim")
    async def claim(session_id: str, req: ClaimRequest) -> Session:
        session = manager.claim(session_id, req.message)
        await manager.broadcast(session_id, manager.events(session_id)[-1])
        return session

    @app.post("/sessions/{session_id}/challenge")
    async def challenge(session_id: str) -> Session:
        try:
            session = manager.challenge(session_id)
        except LeRobotUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        await manager.broadcast(session_id, manager.events(session_id)[-1])
        return session

    @app.post("/sessions/{session_id}/execute")
    async def execute(session_id: str, req: ExecuteRequest) -> Session:
        _ = req
        try:
            session = await manager.execute(session_id)
        except LeRobotUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        await manager.broadcast(session_id, manager.events(session_id)[-1])
        return session

    @app.post("/sessions/{session_id}/verify")
    async def verify(session_id: str) -> Session:
        try:
            session = manager.verify(session_id)
        except LeRobotUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        await manager.broadcast(session_id, manager.events(session_id)[-1])
        return session

    @app.get("/sessions/{session_id}/score")
    def score(session_id: str) -> ScoreBreakdown | None:
        session = manager.get_session(session_id)
        return session.score

    @app.get("/sessions/{session_id}/events")
    def events(session_id: str) -> list[SessionEvent]:
        return manager.events(session_id)

    @app.websocket("/ws/sessions/{session_id}")
    async def ws_sessions(websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        manager.register_ws(session_id, websocket)
        await websocket.send_json({"event_type": "connected", "session_id": session_id})
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    # -- Dashboard -----------------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("index.html", {"request": request})

    return app
