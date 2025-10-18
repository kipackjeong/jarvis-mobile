"""
Tool registry and adapters.

- AgentTool: minimal abstraction for tools that can be attached to an agent.
- collect_tools_from_mcp(): converts MCP tool descriptors to AgentTool.
- attach_tools_to_agent(): placeholder hook to attach tools to a Microsoft Agent Framework agent.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AgentTool:
    name: str
    description: str = ""
    input_schema: Optional[Dict[str, Any]] = None
    source: str = "mcp"  # origin (e.g., mcp, local)
    handle: Optional[str] = None  # optional handle/identifier


def collect_tools_from_mcp(manager: Any) -> List[AgentTool]:
    """Collect tools from the MCP manager and map to AgentTool.

    The manager is expected to return a list of dicts with at least a name.
    """
    specs: List[Dict[str, Any]] = manager.list_tools()
    tools: List[AgentTool] = []
    for spec in specs:
        name = spec.get("name", "")
        if not name:
            continue
        tools.append(
            AgentTool(
                name=name,
                description=spec.get("description", ""),
                input_schema=spec.get("input_schema"),
                source="mcp",
                handle=spec.get("handle"),
            )
        )
    return tools


def attach_tools_to_agent(agent: Any, tools: List[AgentTool]) -> None:
    """Attach tools to an agent (placeholder).

    This scaffolds future wiring into the Agent Framework once the public API
    for tool registration is finalized. For now, we simply set an attribute.
    """
    try:
        setattr(agent, "_mcp_tools", tools)
    except Exception:
        # Best-effort; attachment is optional
        pass
