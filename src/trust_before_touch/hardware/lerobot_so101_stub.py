"""LeRobot-oriented SO-101 stubs.

Replace TODO sections with actual LeRobot robot and camera adapters for hardware execution.
"""

from trust_before_touch.hardware.interfaces import Camera, LeaderArm, ProverArm, VerifierArm
from trust_before_touch.models.protocol import Challenge, TelemetrySnapshot


class SO101LeaderLeRobotAdapter(LeaderArm):
    def generate_challenge(self) -> Challenge:
        raise NotImplementedError("TODO: map challenge intents to LeRobot leader arm motion commands")


class SO101ProverLeRobotAdapter(ProverArm):
    def execute_challenge(self, challenge: Challenge) -> None:
        _ = challenge
        raise NotImplementedError("TODO: execute challenge through LeRobot arm interface")


class SO101VerifierLeRobotAdapter(VerifierArm):
    def observe_execution(self, challenge: Challenge) -> TelemetrySnapshot:
        _ = challenge
        raise NotImplementedError("TODO: collect telemetry via LeRobot state + camera streams")


class SO101CameraLeRobotAdapter(Camera):
    def capture_frame(self) -> dict[str, float | str]:
        raise NotImplementedError("TODO: capture and process frame via LeRobot camera hooks")
