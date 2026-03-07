from trust_before_touch.config import load_config


def test_config_defaults() -> None:
    cfg = load_config()
    assert cfg.pass_threshold == 0.8
    assert cfg.scoring_weights().trajectory == 0.3


def test_lerobot_device_defaults() -> None:
    cfg = load_config()
    assert cfg.lerobot_leader_arm_port == "/dev/ttyACM1"
    assert cfg.lerobot_follower_with_camera_port == "/dev/ttyACM0"
    assert cfg.lerobot_follower_without_camera_port == "/dev/ttyACM2"
    assert cfg.lerobot_camera_device == "/dev/video2"
