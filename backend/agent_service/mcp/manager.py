"""
MCP Manager: loads servers.yaml and manages MCP server sessions.

This is a scaffold for future integration with real MCP clients. For now, it
supports:
- Loading YAML config with ${ENV} substitution
- Creating a manager instance which can (no-op) connect/disconnect
- Exposing a normalized interface for tool collection
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from .schemas import MCPConfig

_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _subst_env(value: Any) -> Any:
    """Recursively substitute ${VAR} in strings using environment variables.

    Unknown variables are left intact to make it obvious at runtime.
    """
    if isinstance(value, str):
        def repl(m: re.Match[str]) -> str:
            var = m.group(1)
            return os.environ.get(var, m.group(0))
        return _ENV_VAR_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: _subst_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_subst_env(v) for v in value]
    return value


class MCPManager:
    """MCP manager holding config and connection lifecycle.

    This scaffold does not spin real sessions yet. It provides the shape needed
    to integrate once a client is selected.
    """

    def __init__(self, config: MCPConfig) -> None:
        self.config = config
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        """Connect to configured servers (no-op scaffold)."""
        self._connected = True

    def disconnect(self) -> None:
        """Disconnect from servers (no-op scaffold)."""
        self._connected = False

    def list_tools(self) -> list[dict[str, Any]]:
        """Return a normalized list of tool descriptors.

        Demo implementation: returns a static "echo" tool so that downstream
        layers can verify attachment and rendering. Replace this with real
        discovery once an MCP client is integrated.
        """
        return [
            {
                "name": "echo",
                "description": "Echo input text back to the caller.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to echo"}
                    },
                    "required": ["text"],
                },
                "handle": "demo:echo",
            }
        ]


def load_manager_from_path(path: str | Path) -> MCPManager:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"MCP servers config not found: {p}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("MCP config YAML must be a mapping at the top level")
    raw = _subst_env(raw)
    config = MCPConfig(**raw)
    return MCPManager(config)
