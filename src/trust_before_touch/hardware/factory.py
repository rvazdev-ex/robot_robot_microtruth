from trust_before_touch.config import AppConfig
from trust_before_touch.constants import AttackMode, RuntimeBackend
from trust_before_touch.hardware.interfaces import LeaderArm, ProverArm, VerifierArm
from trust_before_touch.hardware.lerobot_so101_stub import create_lerobot_adapters
from trust_before_touch.hardware.simulated import SimLeaderArm, SimProverArm, SimVerifierArm
from trust_before_touch.protocol.challenges import ChallengeGenerator
from trust_before_touch.simulation.engine import SimulationEngine


def create_adapters(
    config: AppConfig, backend: RuntimeBackend, mode: AttackMode
) -> tuple[LeaderArm, ProverArm, VerifierArm]:
    if backend == RuntimeBackend.LEROBOT:
        return create_lerobot_adapters(config, mode)

    generator = ChallengeGenerator(config.seed)
    engine = SimulationEngine(config.seed, config.sim_noise)
    leader = SimLeaderArm(generator)
    prover = SimProverArm()
    verifier = SimVerifierArm(engine, mode)
    return leader, prover, verifier
