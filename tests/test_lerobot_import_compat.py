import types

import pytest

from trust_before_touch.hardware.lerobot_so101 import (
    LeRobotUnavailableError,
    _build_feetech_motors,
    _resolve_feetech_bus_class,
    _resolve_motors_bus_motor_class,
    _try_import_any,
)


class _BusA:
    pass


class _BusB:
    pass


def test_try_import_any_returns_first_available(monkeypatch: pytest.MonkeyPatch) -> None:
    modules = {
        "a.module": types.SimpleNamespace(v=1),
        "b.module": types.SimpleNamespace(v=2),
    }

    def fake_import(name: str) -> object:
        if name in modules:
            return modules[name]
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("trust_before_touch.hardware.lerobot_so101.import_module", fake_import)

    mod = _try_import_any(["missing.one", "b.module", "a.module"])
    assert mod.v == 2


def test_try_import_any_raises_with_all_paths() -> None:
    with pytest.raises(LeRobotUnavailableError) as exc_info:
        _try_import_any(["x.y", "a.b"])

    message = str(exc_info.value)
    assert "x.y" in message
    assert "a.b" in message


def test_resolve_feetech_bus_supports_legacy_class(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = types.SimpleNamespace(FeetechMotorsBus=_BusA)
    monkeypatch.setattr(
        "trust_before_touch.hardware.lerobot_so101._try_import_any",
        lambda paths: mod,
    )

    assert _resolve_feetech_bus_class() is _BusA


def test_resolve_feetech_bus_supports_new_class(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = types.SimpleNamespace(FeetechMotorBus=_BusB)
    monkeypatch.setattr(
        "trust_before_touch.hardware.lerobot_so101._try_import_any",
        lambda paths: mod,
    )

    assert _resolve_feetech_bus_class() is _BusB


def test_resolve_feetech_bus_raises_when_class_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "trust_before_touch.hardware.lerobot_so101._try_import_any",
        lambda paths: types.SimpleNamespace(),
    )

    with pytest.raises(LeRobotUnavailableError) as exc_info:
        _resolve_feetech_bus_class()

    assert "missing a supported bus class" in str(exc_info.value)


def test_resolve_motors_bus_motor_class_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "trust_before_touch.hardware.lerobot_so101._try_import_any",
        lambda paths: types.SimpleNamespace(),
    )

    assert _resolve_motors_bus_motor_class() is None


def test_build_feetech_motors_legacy_payload() -> None:
    payload = _build_feetech_motors(
        {1: "joint_a", 2: "joint_b"},
        "sts3215",
        use_motor_model_objects=False,
    )

    assert payload == {
        "joint_a": ("sts3215", 1),
        "joint_b": ("sts3215", 2),
    }


def test_build_feetech_motors_raises_when_motor_class_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "trust_before_touch.hardware.lerobot_so101._resolve_motors_bus_motor_class",
        lambda: None,
    )

    with pytest.raises(LeRobotUnavailableError) as exc_info:
        _build_feetech_motors({1: "joint_a"}, "sts3215", use_motor_model_objects=True)

    assert "missing `Motor` class" in str(exc_info.value)


def test_build_feetech_motors_with_motor_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeMotor:
        def __init__(self, id: int, model: str) -> None:
            self.id = id
            self.model = model

    monkeypatch.setattr(
        "trust_before_touch.hardware.lerobot_so101._resolve_motors_bus_motor_class",
        lambda: FakeMotor,
    )

    payload = _build_feetech_motors({3: "joint_c"}, "sts3215", use_motor_model_objects=True)
    motor = payload["joint_c"]
    assert isinstance(motor, FakeMotor)
    assert motor.id == 3
    assert motor.model == "sts3215"
