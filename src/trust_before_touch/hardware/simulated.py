from trust_before_touch.constants import AttackMode, ChallengeType
from trust_before_touch.hardware.interfaces import Camera, LeaderArm, ProverArm, VerifierArm
from trust_before_touch.models.protocol import Challenge, TelemetrySnapshot
from trust_before_touch.protocol.challenges import ChallengeGenerator
from trust_before_touch.simulation.engine import SimulationEngine


class SimLeaderArm(LeaderArm):
    def __init__(self, generator: ChallengeGenerator) -> None:
        self.generator = generator

    def generate_challenge(self, challenge_type: ChallengeType | None = None) -> Challenge:
        return self.generator.generate(challenge_type)


class SimProverArm(ProverArm):
    def execute_challenge(self, challenge: Challenge) -> None:
        _ = challenge


class SimCamera(Camera):
    def capture_frame(self) -> dict[str, float | str]:
        return {"marker": "object-A", "confidence": 0.95}


class SimVerifierArm(VerifierArm):
    def __init__(self, engine: SimulationEngine, mode: AttackMode):
        self.engine = engine
        self.mode = mode

    def observe_execution(self, challenge: Challenge) -> TelemetrySnapshot:
        return self.engine.run(challenge, self.mode)
