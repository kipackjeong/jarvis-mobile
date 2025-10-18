"""
Chainlit frontend for fast validation of the Agent Framework service.

Run:
  source venv_linux/bin/activate
  chainlit run backend/agent_service/chainlit_app.py -w

This uses the same Settings and Agent factory as the FastAPI app.
"""
from __future__ import annotations

import chainlit as cl

from config.settings import get_settings
from agents.factory import build_agent, normalize_provider


@cl.on_chat_start
async def on_chat_start():
    """Initialize an agent for the user session and show context info."""
    settings = get_settings()
    # Use default prompty if provided via settings
    agent = build_agent(settings, template_name=settings.agent_prompty)
    cl.user_session.set("agent", agent)

    provider = normalize_provider(settings.provider)
    model_desc = ""
    if provider == "openai":
        model_desc = settings.openai_model or "(unset)"
    elif provider == "azure":
        model_desc = settings.azure_openai_deployment_name or "(unset)"
    else:
        model_desc = "mock"

    # Surface MCP tool info if available
    mcp_tools = getattr(agent, "_mcp_tools", [])
    mcp_summary = f"MCP tools: {len(mcp_tools)}" if mcp_tools else "MCP tools: disabled"

    await cl.Message(
        content=(
            f"Agent ready.\n"
            f"Provider: {provider}\n"
            f"Model/Deployment: {model_desc}\n"
            f"{mcp_summary}\n"
            "Type your message to begin."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user message with streaming token updates."""
    agent = cl.user_session.get("agent")
    if agent is None:
        # Fallback: rebuild if session was lost
        s = get_settings()
        agent = build_agent(s, template_name=s.agent_prompty)
        cl.user_session.set("agent", agent)

    # Prepare a streaming message to the user
    reply = cl.Message(content="")
    await reply.send()

    try:
        async for chunk in agent.run_stream(message.content):
            if chunk:
                await reply.stream_token(chunk)
    except Exception as exc:  # Surface the error in the UI
        reply.content = f"Error: {exc}"
        await reply.update()
    else:
        await reply.update()
