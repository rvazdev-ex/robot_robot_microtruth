from pydantic import BaseModel

from trust_before_touch.constants import AttackMode


class SessionCreateRequest(BaseModel):
    attack_mode: AttackMode = AttackMode.NORMAL


class ClaimRequest(BaseModel):
    message: str = "prover ready"


class ExecuteRequest(BaseModel):
    noise: float | None = None


class SessionSummary(BaseModel):
    session_id: str
    state: str
    verdict: str | None
