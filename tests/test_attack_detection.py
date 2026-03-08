from trust_before_touch.constants import AttackMode, ChallengeType
from trust_before_touch.models.protocol import Challenge
from trust_before_touch.simulation.engine import SimulationEngine


def _challenge() -> Challenge:
    return Challenge(
        challenge_id="c1",
        challenge_type=ChallengeType.TAP_RHYTHM,
        trajectory_points=[0.1, 0.2, -0.1, 0.3, 0.0],
        expected_duration_ms=1000,
        expected_pose="forward",
        rhythm_pattern=[120, 180, 200, 150],
    )


def test_replay_mode_flags() -> None:
    engine = SimulationEngine(1, 0.01)
    t = engine.run(_challenge(), AttackMode.REPLAY)
    assert t.replay_signature_match is True
    assert t.timing_delta_ms >= 400


def test_delay_mode_flags() -> None:
    engine = SimulationEngine(1, 0.01)
    t = engine.run(_challenge(), AttackMode.DELAY)
    assert t.delay_flag is True
    assert t.timing_delta_ms >= 550
