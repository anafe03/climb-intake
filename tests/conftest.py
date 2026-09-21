import os
import pytest


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Every test gets its own audit DB. Rules mode unless a test opts into llm."""
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "audit.db"))
    monkeypatch.setenv("CLASSIFIER_MODE", os.environ.get("TEST_CLASSIFIER_MODE", "rules"))
    yield
