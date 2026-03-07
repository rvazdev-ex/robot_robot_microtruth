from trust_before_touch.constants import AttackMode
from trust_before_touch.protocol.challenges import ChallengeGenerator
from trust_before_touch.simulation.engine import SimulationEngine


def test_simulation_deterministic() -> None:
    challenge = ChallengeGenerator(seed=42).generate()
    a = SimulationEngine(42, 0.02).run(challenge, AttackMode.NORMAL)
    b = SimulationEngine(42, 0.02).run(challenge, AttackMode.NORMAL)
    assert a == b
