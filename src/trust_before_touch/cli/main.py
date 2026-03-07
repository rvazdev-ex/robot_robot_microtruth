import asyncio

import typer

from trust_before_touch.config import load_config
from trust_before_touch.constants import AttackMode, ChallengeType
from trust_before_touch.protocol.session_manager import SessionManager

app = typer.Typer(help="Trust-before-touch demo CLI")


@app.command()
def run_demo(mode: AttackMode = AttackMode.NORMAL) -> None:
    """Run an end-to-end PCS protocol session."""
    manager = SessionManager(load_config())
    session = manager.create_session(mode)
    session = manager.claim(session.session_id, "prover ready")
    session = manager.challenge(session.session_id)
    session = manager.execute(session.session_id)
    session = manager.verify(session.session_id)
    typer.echo(session.model_dump_json(indent=2))


@app.command()
def run_training_watermark_demo() -> None:
    """Run a training demo with watermark encoded in micromovements."""
    manager = SessionManager(load_config())
    session = manager.create_session(AttackMode.NORMAL)
    session = manager.claim(session.session_id, "prover ready")
    session = manager.challenge(session.session_id, ChallengeType.TRAINING_MICROMOVEMENT_WATERMARK)
    session = manager.execute(session.session_id)
    session = manager.verify(session.session_id)
    typer.echo(session.model_dump_json(indent=2))


@app.command()
def run_cross_camera_watermark_demo() -> None:
    """Run a watermark demo requiring hat detection by the other arm camera."""
    manager = SessionManager(load_config())
    session = manager.create_session(AttackMode.NORMAL)
    session = manager.claim(session.session_id, "prover ready")
    session = manager.challenge(session.session_id, ChallengeType.CROSS_CAMERA_HAT_WATERMARK)
    session = manager.execute(session.session_id)
    session = manager.verify(session.session_id)
    typer.echo(session.model_dump_json(indent=2))


@app.command()
def stream_events(session_id: str) -> None:
    """Print saved events for a session."""
    manager = SessionManager(load_config())
    for event in manager.events(session_id):
        typer.echo(event.model_dump_json())


@app.command()
def smoke() -> None:
    """Basic async smoke for tooling."""

    async def _noop() -> None:
        return None

    asyncio.run(_noop())
