from trust_before_touch.constants import AttackMode, ChallengeType
from trust_before_touch.protocol.challenges import ChallengeGenerator
from trust_before_touch.simulation.engine import SimulationEngine


def test_simulation_deterministic() -> None:
    challenge = ChallengeGenerator(seed=42).generate()
    a = SimulationEngine(42, 0.02).run(challenge, AttackMode.NORMAL)
    b = SimulationEngine(42, 0.02).run(challenge, AttackMode.NORMAL)
    assert a == b


def test_cross_camera_watermark_sets_hat_detection() -> None:
    challenge = ChallengeGenerator(seed=42).generate(ChallengeType.CROSS_CAMERA_HAT_WATERMARK)
    telemetry = SimulationEngine(42, 0.02).run(challenge, AttackMode.NORMAL)
    assert telemetry.watermark_match_score > 0
    assert telemetry.hat_detected_by_other_camera is True


def test_replay_degrades_watermark_verification() -> None:
    challenge = ChallengeGenerator(seed=42).generate(ChallengeType.TRAINING_MICROMOVEMENT_WATERMARK)
    telemetry = SimulationEngine(42, 0.02).run(challenge, AttackMode.REPLAY)
    assert telemetry.watermark_match_score <= 0.45
    assert telemetry.hat_detected_by_other_camera is False
