"""Factory functions for creating hardware adapters.

Supports both the real-time RobotArm/RobotCamera interfaces and the
legacy PCS challenge-response adapters.
"""

from __future__ import annotations

from trust_before_touch.config import AppConfig
from trust_before_touch.constants import AttackMode, RuntimeBackend
from trust_before_touch.hardware.interfaces import (
    LeaderArm,
    ProverArm,
    RobotArm,
    RobotCamera,
    VerifierArm,
)
from trust_before_touch.hardware.simulated import (
    SimLeaderArm,
    SimProverArm,
    SimRobotArm,
    SimRobotCamera,
    SimVerifierArm,
)
from trust_before_touch.protocol.challenges import ChallengeGenerator
from trust_before_touch.simulation.engine import SimulationEngine


def create_realtime_hardware(
    config: AppConfig,
) -> tuple[RobotArm, list[RobotArm], RobotCamera]:
    """Create real-time hardware handles (leader, followers, camera).

    Returns arms and camera that are NOT yet connected — call connect() on each.
    """
    if config.runtime_backend == RuntimeBackend.LEROBOT:
        from trust_before_touch.hardware.lerobot_so101 import create_lerobot_hardware

        leader, fl, fr, cam = create_lerobot_hardware(config)
        followers: list[RobotArm] = []
        if config.enable_follower_left:
            followers.append(fl)
        if config.enable_follower_right:
            followers.append(fr)
        return leader, followers, cam

    # Simulation backend
    leader_sim = SimRobotArm("leader", seed=config.seed)
    followers_sim: list[RobotArm] = []
    if config.enable_follower_left:
        followers_sim.append(SimRobotArm("follower_left", seed=config.seed + 1))
    if config.enable_follower_right:
        followers_sim.append(SimRobotArm("follower_right", seed=config.seed + 2))
    camera_sim = SimRobotCamera()
    return leader_sim, followers_sim, camera_sim


def create_adapters(
    config: AppConfig, backend: RuntimeBackend, mode: AttackMode
) -> tuple[LeaderArm, ProverArm, VerifierArm]:
    """Legacy PCS adapter factory (kept for verification sessions)."""
    if backend == RuntimeBackend.LEROBOT:
        from trust_before_touch.hardware.lerobot_so101 import create_lerobot_adapters

        return create_lerobot_adapters(config, mode)

    generator = ChallengeGenerator(config.seed)
    engine = SimulationEngine(config.seed, config.sim_noise)
    leader = SimLeaderArm(generator)
    prover = SimProverArm()
    verifier = SimVerifierArm(engine, mode)
    return leader, prover, verifier
