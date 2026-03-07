import types

import pytest

from trust_before_touch.hardware.lerobot_so101 import (
    LeRobotUnavailableError,
    _resolve_feetech_bus_class,
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
