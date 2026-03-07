from trust_before_touch.protocol.challenges import ChallengeGenerator


def test_challenge_generation_shape() -> None:
    challenge = ChallengeGenerator(seed=1).generate()
    assert len(challenge.trajectory_points) == 5
    assert len(challenge.rhythm_pattern) == 4
    assert challenge.expected_duration_ms >= 900
