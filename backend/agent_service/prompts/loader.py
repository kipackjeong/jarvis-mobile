"""
Prompty loader: parse local .prompty files (YAML front matter + Markdown body).

- Supports ${ENV_VAR} substitution in front matter values.
- Returns a validated structure with optional provider-specific overrides
  and the final instructions string (Markdown body).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


PROMPTS_DIR = Path(__file__).resolve().parent  # backend/agent_service/prompts/

_FRONT_MATTER_RE = re.compile(r"^---\s*$")
_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class PromptyAzureConfig(BaseModel):
    endpoint: Optional[str] = Field(default=None)
    deployment_name: Optional[str] = Field(default=None)
    api_version: Optional[str] = Field(default=None)


class PromptyOpenAIConfig(BaseModel):
    model: Optional[str] = Field(default=None)


class PromptyTemplate(BaseModel):
    name: Optional[str] = Field(default=None)
    provider: Optional[str] = Field(default=None)
    azure: Optional[PromptyAzureConfig] = Field(default=None)
    openai: Optional[PromptyOpenAIConfig] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)
    metadata: Optional[dict[str, Any]] = Field(default=None)
    instructions: str = Field(description="Markdown body used as system instructions")


def _substitute_env(value: Any) -> Any:
    """Recursively substitute ${VAR} in strings using environment variables.

    If an env var is missing, the placeholder is left as-is.
    """
    if isinstance(value, str):
        def repl(match: re.Match[str]) -> str:
            var = match.group(1)
            return os.environ.get(var, match.group(0))

        return _ENV_VAR_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env(v) for v in value]
    return value


def _parse_front_matter_and_body(text: str) -> tuple[dict[str, Any], str]:
    """Split a prompty text into (front_matter_dict, body_md).

    Expects the file to start with a '---' delimited YAML front matter block.
    If not present, assumes empty dict and entire text as body.
    """
    lines = text.splitlines()
    if not lines:
        return {}, ""

    if not _FRONT_MATTER_RE.match(lines[0]):
        # No front matter header; return everything as body
        return {}, text

    # Find the closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if _FRONT_MATTER_RE.match(lines[i]):
            end_idx = i
            break
    if end_idx is None:
        # Malformed front matter; treat entire file as body
        return {}, text

    front_matter_text = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])

    data = yaml.safe_load(front_matter_text) or {}
    if not isinstance(data, dict):
        raise ValueError("Prompty front matter must be a mapping (YAML object)")
    return data, body


def load_prompty(name: str) -> PromptyTemplate:
    """Load a .prompty file from the prompts directory by name (without extension)."""
    path = PROMPTS_DIR / f"{name}.prompty"
    if not path.exists():
        raise FileNotFoundError(f"Prompty file not found: {path}")

    text = path.read_text(encoding="utf-8")
    fm, body = _parse_front_matter_and_body(text)
    fm = _substitute_env(fm)

    try:
        # Validate + attach body as instructions
        return PromptyTemplate(**fm, instructions=body.strip())
    except ValidationError as ve:
        raise ValueError(f"Invalid prompty structure for {name}: {ve}") from ve
