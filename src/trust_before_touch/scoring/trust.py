from trust_before_touch.config import WeightConfig
from trust_before_touch.models.protocol import ScoreBreakdown, TelemetrySnapshot


class TrustScorer:
    def __init__(
        self, weights: WeightConfig, pass_threshold: float, borderline_threshold: float
    ) -> None:
        self.weights = weights
        self.pass_threshold = pass_threshold
        self.borderline_threshold = borderline_threshold

    def score(self, telemetry: TelemetrySnapshot) -> ScoreBreakdown:
        trajectory = max(0.0, 1.0 - telemetry.trajectory_error)
        timing = max(0.0, 1.0 - (abs(telemetry.timing_delta_ms) / 1000.0))
        observation = telemetry.vision_confidence
        alignment = telemetry.contact_alignment

        total = (
            trajectory * self.weights.trajectory
            + timing * self.weights.timing
            + observation * self.weights.observation
            + alignment * self.weights.alignment
        )

        if telemetry.replay_signature_match:
            total *= 0.5
        if telemetry.delay_flag:
            total *= 0.7

        verdict = "fail"
        if total >= self.pass_threshold:
            verdict = "pass"
        elif total >= self.borderline_threshold:
            verdict = "borderline"

        return ScoreBreakdown(
            trajectory=round(trajectory, 3),
            timing=round(timing, 3),
            observation=round(observation, 3),
            alignment=round(alignment, 3),
            total=round(total, 3),
            verdict=verdict,
        )
