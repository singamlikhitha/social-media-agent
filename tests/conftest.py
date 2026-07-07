"""Shared pytest fixtures and safe default env for the test suite.

Env defaults are set *before* app modules import so `app.config.Settings`
(instantiated at import time) picks them up. `setdefault` means CI-provided
values (e.g. the Postgres service DATABASE_URL) always win.
"""
import os

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_smoke.db")
os.environ.setdefault("OTEL_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    # No context manager -> lifespan (DB create_all + scheduler) is skipped.
    # The health endpoints don't need it, keeping this smoke test hermetic.
    return TestClient(app)
