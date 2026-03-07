from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from trust_before_touch.config import load_config
from trust_before_touch.models.api import ClaimRequest, ExecuteRequest, SessionCreateRequest
from trust_before_touch.models.events import SessionEvent
from trust_before_touch.models.protocol import ScoreBreakdown, Session
from trust_before_touch.protocol.session_manager import SessionManager


def _templates_directory() -> Path:
    return Path(str(files("trust_before_touch").joinpath("dashboard/templates")))


def create_app() -> FastAPI:
    config = load_config()
    manager = SessionManager(config)
    app = FastAPI(title="trust-before-touch-so101")
    templates = Jinja2Templates(directory=str(_templates_directory()))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/config")
    def get_config() -> dict[str, float | int | str]:
        return config.model_dump()

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
        session = manager.challenge(session_id)
        await manager.broadcast(session_id, manager.events(session_id)[-1])
        return session

    @app.post("/sessions/{session_id}/execute")
    async def execute(session_id: str, req: ExecuteRequest) -> Session:
        _ = req
        session = manager.execute(session_id)
        await manager.broadcast(session_id, manager.events(session_id)[-1])
        return session

    @app.post("/sessions/{session_id}/verify")
    async def verify(session_id: str) -> Session:
        session = manager.verify(session_id)
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
        while True:
            await websocket.receive_text()

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("index.html", {"request": request})

    return app
