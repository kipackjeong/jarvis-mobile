from __future__ import annotations

from pathlib import Path

import pytest

from mcp.manager import MCPManager, load_manager_from_path


def test_load_manager_from_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Prepare a temp servers.yaml with env expansion
    yaml_text = (
        "servers:\n"
        "  - name: sse-1\n"
        "    mode: sse\n"
        "    url: ${MCP_SSE_URL}\n"
        "    headers:\n"
        "      Authorization: Bearer ${MCP_SSE_TOKEN}\n"
    )
    fp = tmp_path / "servers.yaml"
    fp.write_text(yaml_text, encoding="utf-8")

    monkeypatch.setenv("MCP_SSE_URL", "https://example.com/sse")
    monkeypatch.setenv("MCP_SSE_TOKEN", "test-token")

    mgr = load_manager_from_path(str(fp))
    assert isinstance(mgr, MCPManager)
    assert len(mgr.config.servers) == 1
    s = mgr.config.servers[0]
    assert s.name == "sse-1"
    assert s.mode == "sse"
    assert s.url == "https://example.com/sse"
    assert s.headers and s.headers.get("Authorization") == "Bearer test-token"


def test_demo_tool_list():
    # The manager emits a demo tool spec for now
    mgr = MCPManager(config=type("Cfg", (), {"servers": []})())
    tools = mgr.list_tools()
    assert any(t.get("name") == "echo" for t in tools)
