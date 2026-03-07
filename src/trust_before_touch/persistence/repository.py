import json
import sqlite3
from pathlib import Path

from trust_before_touch.models.events import SessionEvent
from trust_before_touch.models.protocol import Session


class SessionRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    session_id TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def save_session(self, session: Session) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions(session_id, payload) VALUES(?, ?)",
                (session.session_id, session.model_dump_json()),
            )

    def get_session(self, session_id: str) -> Session | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT payload FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if row is None:
            return None
        return Session.model_validate_json(row[0])

    def add_event(self, session_id: str, event: SessionEvent) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO events(session_id, ts, event_type, payload) VALUES(?, ?, ?, ?)",
                (
                    session_id,
                    event.timestamp.isoformat(),
                    event.event_type,
                    json.dumps(event.payload),
                ),
            )

    def list_events(self, session_id: str) -> list[SessionEvent]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT ts, event_type, payload FROM events WHERE session_id = ? ORDER BY ts ASC",
                (session_id,),
            ).fetchall()
        return [
            SessionEvent(timestamp=row[0], event_type=row[1], payload=json.loads(row[2])) for row in rows
        ]
