from trust_before_touch.config import load_config


def test_config_defaults() -> None:
    cfg = load_config()
    assert cfg.pass_threshold == 0.8
    assert cfg.scoring_weights().trajectory == 0.3
