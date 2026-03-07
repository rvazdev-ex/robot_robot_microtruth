from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from trust_before_touch.constants import ControlMode, RuntimeBackend


class WeightConfig(BaseModel):
    trajectory: float = 0.30
    timing: float = 0.25
    observation: float = 0.25
    alignment: float = 0.20


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TBT_", env_file=".env", extra="ignore")

    db_path: str = "./data/tbt.sqlite"
    seed: int = 101
    pass_threshold: float = 0.80
    borderline_threshold: float = 0.60
    trajectory_weight: float = 0.30
    timing_weight: float = 0.25
    observation_weight: float = 0.25
    alignment_weight: float = 0.20
    sim_noise: float = 0.03
    runtime_backend: RuntimeBackend = Field(default=RuntimeBackend.SIMULATION)

    # --- LeRobot hardware ports (SO-101 Feetech serial) ---
    lerobot_leader_arm_port: str = "/dev/ttyACM1"
    lerobot_follower_with_camera_port: str = "/dev/ttyACM0"
    lerobot_follower_without_camera_port: str = "/dev/ttyACM2"
    lerobot_camera_device: str = "/dev/video2"

    # --- Real-time control parameters ---
    control_frequency_hz: float = 30.0  # Control loop frequency (Hz)
    telemetry_frequency_hz: float = 10.0  # WebSocket telemetry push rate (Hz)
    default_control_mode: ControlMode = Field(default=ControlMode.IDLE)
    max_joint_delta_deg: float = 5.0  # Max position change per step (safety)
    enable_follower_left: bool = True  # follower_with_camera
    enable_follower_right: bool = True  # follower_without_camera

    # --- LeRobot motor configuration (SO-101 Feetech STS3215) ---
    lerobot_motor_model: str = "sts3215"

    def scoring_weights(self) -> WeightConfig:
        return WeightConfig(
            trajectory=self.trajectory_weight,
            timing=self.timing_weight,
            observation=self.observation_weight,
            alignment=self.alignment_weight,
        )

    @property
    def control_dt(self) -> float:
        """Control loop period in seconds."""
        return 1.0 / self.control_frequency_hz

    @property
    def telemetry_dt(self) -> float:
        """Telemetry push period in seconds."""
        return 1.0 / self.telemetry_frequency_hz


def load_config() -> AppConfig:
    return AppConfig()
