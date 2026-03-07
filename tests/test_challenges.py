from trust_before_touch.constants import ChallengeType
from trust_before_touch.protocol.challenges import ChallengeGenerator


def test_challenge_generation_shape() -> None:
    challenge = ChallengeGenerator(seed=1).generate()
    assert len(challenge.trajectory_points) == 5
    assert len(challenge.rhythm_pattern) == 4
    assert challenge.expected_duration_ms >= 900


def test_training_watermark_challenge_shape() -> None:
    challenge = ChallengeGenerator(seed=1).generate(ChallengeType.TRAINING_MICROMOVEMENT_WATERMARK)
    assert challenge.challenge_type == ChallengeType.TRAINING_MICROMOVEMENT_WATERMARK
    assert challenge.expected_marker == "hat"
    assert challenge.expected_pose == "watermark_training"
    assert len(challenge.watermark_pattern) == 8


def test_cross_camera_watermark_challenge_shape() -> None:
    challenge = ChallengeGenerator(seed=1).generate(ChallengeType.CROSS_CAMERA_HAT_WATERMARK)
    assert challenge.challenge_type == ChallengeType.CROSS_CAMERA_HAT_WATERMARK
    assert challenge.expected_marker == "hat"
    assert challenge.expected_pose == "watermark_cross_camera"
    assert len(challenge.watermark_pattern) == 12
