"""
Pydantic schemas for MCP server configuration.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    name: str = Field(description="Logical server name")
    mode: Literal["stdio", "sse"] = Field(
        default="stdio", description="Connection mode: stdio or sse"
    )
    # stdio
    command: Optional[List[str]] = Field(
        default=None, description="Command + args for stdio servers"
    )
    env: Optional[Dict[str, str]] = Field(default=None, description="Extra env vars")

    # sse
    url: Optional[str] = Field(default=None, description="SSE server URL")
    headers: Optional[Dict[str, str]] = Field(
        default=None, description="Optional HTTP headers for SSE"
    )


class MCPConfig(BaseModel):
    servers: List[MCPServerConfig] = Field(default_factory=list)
