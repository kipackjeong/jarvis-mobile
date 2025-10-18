from __future__ import annotations

import os

import pytest

from prompts.loader import load_prompty, PromptyTemplate


def test_load_prompty_env_substitution(monkeypatch: pytest.MonkeyPatch):
    # Ensure env vars used in jarvis.prompty are present
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://unit-test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "unittest-deployment")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview")

    tpl: PromptyTemplate = load_prompty("jarvis")

    assert tpl.provider == "azure"
    assert tpl.azure is not None
    assert tpl.azure.endpoint == "https://unit-test.openai.azure.com/"
    assert tpl.azure.deployment_name == "unittest-deployment"
    assert tpl.azure.api_version == "2025-03-01-preview"
    assert isinstance(tpl.instructions, str) and len(tpl.instructions) > 0


def test_load_prompty_missing_file():
    with pytest.raises(FileNotFoundError):
        load_prompty("does-not-exist")
