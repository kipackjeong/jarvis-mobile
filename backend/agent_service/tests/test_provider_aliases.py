"""Tests for provider alias normalization and unsupported provider handling."""
from __future__ import annotations

import pytest

from agents.factory import normalize_provider, build_agent
from config.settings import Settings


def test_normalize_provider_aliases():
    assert normalize_provider("azure_foundry") == "azure"
    assert normalize_provider("azure-openai") == "azure"
    assert normalize_provider("azure-ai") == "azure"
    assert normalize_provider("azureai") == "azure"
    assert normalize_provider("oai") == "openai"
    assert normalize_provider("openai") == "openai"
    assert normalize_provider("mock") == "mock"


def test_build_agent_unsupported_provider():
    settings = Settings(provider="mock")
    with pytest.raises(ValueError):
        build_agent(settings, provider_override="unsupported")
