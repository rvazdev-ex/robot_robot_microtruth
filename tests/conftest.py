"""Shared pytest configuration."""

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    """Ensure tests use an ephemeral database and simulation backend."""
    monkeypatch.setenv("TBT_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setenv("TBT_RUNTIME_BACKEND", "simulation")
