from enum import StrEnum


class SessionState(StrEnum):
    IDLE = "idle"
    CLAIM_RECEIVED = "claim_received"
    CHALLENGE_ISSUED = "challenge_issued"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    PASSED = "passed"
    FAILED = "failed"
    ABORTED = "aborted"


class ChallengeType(StrEnum):
    MIRRORED_MICRO_TRAJECTORY = "mirrored_micro_trajectory"
    POSE_AND_PRESENT = "pose_and_present"
    TAP_RHYTHM = "tap_rhythm"
    HANDOFF_READINESS = "handoff_readiness"
    TRAINING_MICROMOVEMENT_WATERMARK = "training_micromovement_watermark"
    CROSS_CAMERA_HAT_WATERMARK = "cross_camera_hat_watermark"


class AttackMode(StrEnum):
    NORMAL = "normal"
    REPLAY = "replay"
    DELAY = "delay"
