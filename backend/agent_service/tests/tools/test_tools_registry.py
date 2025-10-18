from __future__ import annotations

from types import SimpleNamespace

from mcp.manager import MCPManager
from tools.registry import AgentTool, attach_tools_to_agent, collect_tools_from_mcp


def test_collect_tools_from_mcp_and_attach():
    # Manager with demo tool already provided by list_tools()
    mgr = MCPManager(config=SimpleNamespace(servers=[]))

    tools = collect_tools_from_mcp(mgr)
    # Should contain at least the demo echo tool
    assert any(isinstance(t, AgentTool) and t.name == "echo" for t in tools)

    # Attach to a dummy agent
    agent = SimpleNamespace()
    attach_tools_to_agent(agent, tools)

    attached = getattr(agent, "_mcp_tools", None)
    assert attached is not None
    assert any(t.name == "echo" for t in attached)
