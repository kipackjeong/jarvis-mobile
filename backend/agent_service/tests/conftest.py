"""Pytest configuration and fixtures for the Agent service tests."""
from __future__ import annotations

import os
import pytest
from fastapi import FastAPI

# Ensure mock provider for deterministic tests
os.environ.setdefault("PROVIDER", "mock")


@pytest.fixture(scope="session")
def app() -> FastAPI:  # type: ignore[override]
    # Import after setting env so settings resolve correctly
    from app.main import app as fastapi_app

    return fastapi_app
