import random
from uuid import uuid4

from trust_before_touch.constants import ChallengeType
from trust_before_touch.models.protocol import Challenge


class ChallengeGenerator:
    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def generate(self, challenge_type: ChallengeType | None = None) -> Challenge:
        ctype = challenge_type or self._rng.choice(list(ChallengeType))
        challenge = Challenge(
            challenge_id=str(uuid4()),
            challenge_type=ctype,
            trajectory_points=[round(self._rng.uniform(-1.0, 1.0), 3) for _ in range(5)],
            expected_duration_ms=self._rng.randint(900, 1800),
            expected_pose=self._rng.choice(["forward", "left", "right", "present"]),
            rhythm_pattern=[self._rng.randint(100, 400) for _ in range(4)],
        )

        if ctype == ChallengeType.TRAINING_MICROMOVEMENT_WATERMARK:
            challenge.watermark_pattern = [self._rng.randint(0, 1) for _ in range(8)]
            challenge.expected_pose = "watermark_training"
            challenge.expected_marker = "hat"
        elif ctype == ChallengeType.CROSS_CAMERA_HAT_WATERMARK:
            challenge.watermark_pattern = [self._rng.randint(0, 1) for _ in range(12)]
            challenge.expected_pose = "watermark_cross_camera"
            challenge.expected_marker = "hat"

        return challenge
