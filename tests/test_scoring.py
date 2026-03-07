from trust_before_touch.config import WeightConfig
from trust_before_touch.models.protocol import TelemetrySnapshot
from trust_before_touch.scoring.trust import TrustScorer


def test_scoring_pass() -> None:
    scorer = TrustScorer(WeightConfig(), 0.8, 0.6)
    s = scorer.score(
        TelemetrySnapshot(
            trajectory_error=0.05,
            timing_delta_ms=30,
            vision_confidence=0.95,
            contact_alignment=0.94,
        )
    )
    assert s.verdict == "pass"


def test_replay_penalty() -> None:
    scorer = TrustScorer(WeightConfig(), 0.8, 0.6)
    s = scorer.score(
        TelemetrySnapshot(
            trajectory_error=0.05,
            timing_delta_ms=30,
            vision_confidence=0.95,
            contact_alignment=0.94,
            replay_signature_match=True,
        )
    )
    assert s.total < 0.8
