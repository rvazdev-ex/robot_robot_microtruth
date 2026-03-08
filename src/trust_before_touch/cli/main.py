"""CLI for real-time robot control and PCS verification demos."""

from __future__ import annotations

import asyncio
import signal
import time

import typer

from trust_before_touch.config import load_config
from trust_before_touch.constants import AttackMode, ChallengeType, ControlMode, RuntimeBackend
from trust_before_touch.models.robot import SO101_JOINT_NAMES
from trust_before_touch.protocol.session_manager import SessionManager

app = typer.Typer(help="Real-time robot control & trust-before-touch CLI")


def _manager(backend: RuntimeBackend | None) -> SessionManager:
    config = load_config()
    if backend is not None:
        config.runtime_backend = backend
    return SessionManager(config)


# ---------------------------------------------------------------------------
# Real-time control commands
# ---------------------------------------------------------------------------


@app.command()
def teleoperate(
    backend: RuntimeBackend | None = None,
    frequency: float | None = None,
    duration: float = 0.0,
) -> None:
    """Start real-time leader-follower teleoperation.

    Reads leader arm positions and mirrors them to follower arm(s).
    Press Ctrl+C to stop.
    """
    config = load_config()
    if backend is not None:
        config.runtime_backend = backend
    if frequency is not None:
        config.control_frequency_hz = frequency
    manager = SessionManager(config)

    async def _run() -> None:
        typer.echo(
            "Starting teleoperation "
            f"({config.runtime_backend}) at {config.control_frequency_hz} Hz"
        )
        typer.echo("Press Ctrl+C to stop\n")

        await manager.start_control(ControlMode.TELEOPERATION)
        stop_event = asyncio.Event()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)

        start = time.time()
        try:
            while not stop_event.is_set():
                state = manager.get_robot_state()
                if state.leader and state.leader.joint_state:
                    joints = state.leader.joint_state.positions
                    names = SO101_JOINT_NAMES[: len(joints)]
                    parts = [f"{n}={v:+7.1f}" for n, v in zip(names, joints, strict=False)]
                    dt_str = f"dt={state.loop_dt_ms:.1f}ms"
                    typer.echo(f"\r  Leader: {' '.join(parts)}  [{dt_str}]", nl=False)
                await asyncio.sleep(0.1)
                if duration > 0 and (time.time() - start) >= duration:
                    break
        finally:
            typer.echo("\n\nStopping...")
            await manager.stop_control()
            typer.echo("Teleoperation stopped.")

    asyncio.run(_run())


@app.command()
def record(
    backend: RuntimeBackend | None = None,
    duration: float = 10.0,
) -> None:
    """Record a leader-follower trajectory for a given duration (seconds)."""
    config = load_config()
    if backend is not None:
        config.runtime_backend = backend
    manager = SessionManager(config)

    async def _run() -> None:
        typer.echo(f"Recording trajectory for {duration}s...")
        await manager.start_control(ControlMode.RECORDING)
        await asyncio.sleep(duration)
        state = await manager.stop_control()

        typer.echo("Recording complete.")
        if state:
            typer.echo(state.model_dump_json(indent=2))

    asyncio.run(_run())


@app.command()
def read_joints(
    backend: RuntimeBackend | None = None,
) -> None:
    """Read and display current joint positions from all connected arms."""
    config = load_config()
    if backend is not None:
        config.runtime_backend = backend

    from trust_before_touch.hardware.factory import create_realtime_hardware

    leader, followers, camera = create_realtime_hardware(config)

    leader.connect()
    for f in followers:
        f.connect()

    try:
        typer.echo("--- Joint Positions ---\n")
        leader_js = leader.read_joints()
        typer.echo(f"Leader ({leader.name}):")
        for name, pos in zip(SO101_JOINT_NAMES, leader_js.positions, strict=False):
            typer.echo(f"  {name:20s}: {pos:+8.2f} deg")

        for f in followers:
            typer.echo(f"\nFollower ({f.name}):")
            fjs = f.read_joints()
            for name, pos in zip(SO101_JOINT_NAMES, fjs.positions, strict=False):
                typer.echo(f"  {name:20s}: {pos:+8.2f} deg")
    finally:
        leader.disconnect()
        for f in followers:
            f.disconnect()


# ---------------------------------------------------------------------------
# PCS verification commands (existing)
# ---------------------------------------------------------------------------


@app.command()
def run_demo(
    mode: AttackMode = AttackMode.NORMAL,
    backend: RuntimeBackend | None = None,
) -> None:
    """Run an end-to-end PCS protocol session."""
    manager = _manager(backend)
    session = manager.create_session(mode)
    session = manager.claim(session.session_id, "prover ready")
    session = manager.challenge(session.session_id)
    session = asyncio.run(manager.execute(session.session_id))
    session = manager.verify(session.session_id)
    typer.echo(session.model_dump_json(indent=2))


@app.command()
def run_training_watermark_demo(backend: RuntimeBackend | None = None) -> None:
    """Run a training demo with watermark encoded in micromovements."""
    manager = _manager(backend)
    session = manager.create_session(AttackMode.NORMAL)
    session = manager.claim(session.session_id, "prover ready")
    session = manager.challenge(session.session_id, ChallengeType.TRAINING_MICROMOVEMENT_WATERMARK)
    session = asyncio.run(manager.execute(session.session_id))
    session = manager.verify(session.session_id)
    typer.echo(session.model_dump_json(indent=2))


@app.command()
def run_cross_camera_watermark_demo(backend: RuntimeBackend | None = None) -> None:
    """Run a watermark demo requiring hat detection by the other arm camera."""
    manager = _manager(backend)
    session = manager.create_session(AttackMode.NORMAL)
    session = manager.claim(session.session_id, "prover ready")
    session = manager.challenge(session.session_id, ChallengeType.CROSS_CAMERA_HAT_WATERMARK)
    session = asyncio.run(manager.execute(session.session_id))
    session = manager.verify(session.session_id)
    typer.echo(session.model_dump_json(indent=2))


@app.command()
def stream_events(session_id: str, backend: RuntimeBackend | None = None) -> None:
    """Print saved events for a session."""
    manager = _manager(backend)
    for event in manager.events(session_id):
        typer.echo(event.model_dump_json())


@app.command()
def smoke() -> None:
    """Basic async smoke for tooling."""

    async def _noop() -> None:
        return None

    asyncio.run(_noop())
