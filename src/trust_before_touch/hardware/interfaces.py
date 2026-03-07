from typing import Protocol

from trust_before_touch.models.protocol import Challenge, TelemetrySnapshot


class LeaderArm(Protocol):
    def generate_challenge(self) -> Challenge: ...


class ProverArm(Protocol):
    def execute_challenge(self, challenge: Challenge) -> None: ...


class VerifierArm(Protocol):
    def observe_execution(self, challenge: Challenge) -> TelemetrySnapshot: ...


class Camera(Protocol):
    def capture_frame(self) -> dict[str, float | str]: ...
