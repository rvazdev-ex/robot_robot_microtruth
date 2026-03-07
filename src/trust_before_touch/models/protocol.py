from pydantic import BaseModel

from trust_before_touch.constants import AttackMode, ChallengeType, SessionState


class Challenge(BaseModel):
    challenge_id: str
    challenge_type: ChallengeType
    trajectory_points: list[float]
    expected_duration_ms: int
    expected_pose: str
    rhythm_pattern: list[int]


class TelemetrySnapshot(BaseModel):
    trajectory_error: float
    timing_delta_ms: int
    vision_confidence: float
    contact_alignment: float
    replay_signature_match: bool = False
    delay_flag: bool = False


class ScoreBreakdown(BaseModel):
    trajectory: float
    timing: float
    observation: float
    alignment: float
    total: float
    verdict: str


class Session(BaseModel):
    session_id: str
    state: SessionState = SessionState.IDLE
    attack_mode: AttackMode = AttackMode.NORMAL
    claim: str | None = None
    challenge: Challenge | None = None
    telemetry: TelemetrySnapshot | None = None
    score: ScoreBreakdown | None = None
