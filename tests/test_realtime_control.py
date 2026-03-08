"""Tests for the real-time control loop and simulated robot arms."""

from __future__ import annotations

import asyncio

from trust_before_touch.config import AppConfig
from trust_before_touch.constants import ControlMode, RuntimeBackend
from trust_before_touch.control.loop import RealtimeControlLoop
from trust_before_touch.hardware.factory import create_realtime_hardware
from trust_before_touch.hardware.simulated import SimRobotArm, SimRobotCamera
from trust_before_touch.models.robot import NUM_JOINTS, SO101_JOINT_NAMES, RobotState


def test_sim_arm_connects_and_reads() -> None:
    arm = SimRobotArm("leader", seed=42)
    assert not arm.is_connected
    arm.connect()
    assert arm.is_connected
    js = arm.read_joints()
    assert len(js.positions) == NUM_JOINTS
    assert len(js.velocities) == NUM_JOINTS
    arm.disconnect()
    assert not arm.is_connected


def test_sim_arm_write_and_readback() -> None:
    arm = SimRobotArm("follower_left", seed=42)
    arm.connect()
    target = [10.0, 20.0, 30.0, -10.0, -20.0, 0.0]
    arm.write_joints(target)
    js = arm.read_joints()
    assert js.positions == target


def test_sim_arm_telemetry() -> None:
    arm = SimRobotArm("leader", seed=42)
    arm.connect()
    t = arm.get_telemetry()
    assert t.arm_name == "leader"
    assert len(t.temperature) == NUM_JOINTS
    assert len(t.load) == NUM_JOINTS


def test_sim_camera() -> None:
    cam = SimRobotCamera()
    cam.connect()
    assert cam.is_connected
    frame = cam.capture_frame()
    assert frame.width == 640
    assert frame.height == 480
    cam.disconnect()


def test_joint_names() -> None:
    assert len(SO101_JOINT_NAMES) == 6
    assert "shoulder_pan" in SO101_JOINT_NAMES
    assert "gripper" in SO101_JOINT_NAMES


def test_create_realtime_hardware_simulation() -> None:
    config = AppConfig()
    config.runtime_backend = RuntimeBackend.SIMULATION
    leader, followers, camera = create_realtime_hardware(config)
    assert leader.name == "leader"
    assert len(followers) == 2
    assert followers[0].name == "follower_left"
    assert followers[1].name == "follower_right"


def test_create_realtime_hardware_single_follower() -> None:
    config = AppConfig()
    config.enable_follower_right = False
    leader, followers, camera = create_realtime_hardware(config)
    assert len(followers) == 1
    assert followers[0].name == "follower_left"


def test_control_loop_starts_and_stops() -> None:
    config = AppConfig()
    config.control_frequency_hz = 100.0  # fast for testing
    config.telemetry_frequency_hz = 50.0
    leader, followers, camera = create_realtime_hardware(config)

    loop = RealtimeControlLoop(config, leader, followers, camera)

    received_states: list[RobotState] = []

    async def on_telemetry(state: RobotState) -> None:
        received_states.append(state)

    loop.on_telemetry(on_telemetry)

    async def _run() -> None:
        await loop.connect_all()
        await loop.start(ControlMode.TELEOPERATION)
        assert loop.is_running

        await asyncio.sleep(0.3)  # Let it run a few cycles

        await loop.stop()
        assert not loop.is_running

        await loop.disconnect_all()

    asyncio.run(_run())

    # Should have received some telemetry
    assert len(received_states) > 0
    state = received_states[-1]
    assert state.control_active
    assert state.leader is not None
    assert state.follower_left is not None


def test_control_loop_recording_mode() -> None:
    config = AppConfig()
    config.control_frequency_hz = 100.0
    leader, followers, camera = create_realtime_hardware(config)

    loop = RealtimeControlLoop(config, leader, followers, camera)

    async def _run() -> None:
        await loop.connect_all()
        await loop.start(ControlMode.RECORDING)

        await asyncio.sleep(0.2)

        await loop.stop()
        await loop.disconnect_all()

    asyncio.run(_run())

    rec = loop.recording
    assert rec is not None
    assert rec.num_points > 0
    assert rec.duration_ms > 0


def test_safety_clamp() -> None:
    config = AppConfig()
    config.max_joint_delta_deg = 2.0
    leader, followers, camera = create_realtime_hardware(config)

    loop = RealtimeControlLoop(config, leader, followers, camera)

    # Set follower to zero positions
    followers[0].connect()
    followers[0].write_joints([0.0] * NUM_JOINTS)

    # Try to clamp a large jump
    target = [100.0] * NUM_JOINTS
    clamped = loop._safety_clamp(target, followers[0])

    for val in clamped:
        assert abs(val) <= 2.0  # Max delta from 0
