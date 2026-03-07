import random

from trust_before_touch.constants import AttackMode, ChallengeType
from trust_before_touch.models.protocol import Challenge, TelemetrySnapshot


class SimulationEngine:
    def __init__(self, seed: int, base_noise: float) -> None:
        self.rng = random.Random(seed)
        self.base_noise = base_noise

    def run(
        self, challenge: Challenge, mode: AttackMode, noise: float | None = None
    ) -> TelemetrySnapshot:
        n = self.base_noise if noise is None else noise
        trajectory_error = abs(self.rng.gauss(0.08, n))
        timing_delta = int(self.rng.gauss(40, n * 1000))
        vision = min(1.0, max(0.0, self.rng.gauss(0.92, n)))
        align = min(1.0, max(0.0, self.rng.gauss(0.9, n)))
        watermark_match_score = 0.0
        hat_detected_by_other_camera = False
        replay = False
        delay = False

        if challenge.challenge_type == ChallengeType.TRAINING_MICROMOVEMENT_WATERMARK:
            watermark_match_score = min(1.0, max(0.0, self.rng.gauss(0.9, n)))
            vision = max(vision, 0.86)
        elif challenge.challenge_type == ChallengeType.CROSS_CAMERA_HAT_WATERMARK:
            watermark_match_score = min(1.0, max(0.0, self.rng.gauss(0.87, n)))
            hat_detected_by_other_camera = self.rng.random() > min(0.2, n)
            vision = max(vision, 0.83)

        if mode == AttackMode.REPLAY:
            trajectory_error = max(trajectory_error, 0.35)
            timing_delta = max(timing_delta, 400)
            replay = True
            watermark_match_score = min(watermark_match_score, 0.45)
            hat_detected_by_other_camera = False
        elif mode == AttackMode.DELAY:
            timing_delta = max(timing_delta, 550)
            delay = True

        return TelemetrySnapshot(
            trajectory_error=round(trajectory_error, 3),
            timing_delta_ms=timing_delta,
            vision_confidence=round(vision, 3),
            contact_alignment=round(align, 3),
            replay_signature_match=replay,
            delay_flag=delay,
            watermark_match_score=round(watermark_match_score, 3),
            hat_detected_by_other_camera=hat_detected_by_other_camera,
        )
