"""Shared pytest configuration."""

from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """Ensure tests use an ephemeral database and simulation backend."""
    monkeypatch.setenv("TBT_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setenv("TBT_RUNTIME_BACKEND", "simulation")
