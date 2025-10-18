"""
Agent factory for Microsoft Agent Framework (Python).

Supports providers:
- openai: OpenAI Responses client
- azure: Azure OpenAI Responses client (Azure AI Foundry / Azure OpenAI)
- mock: Local mock agent for tests and offline dev

Enhancements:
- Provider alias normalization (e.g., 'azure_foundry' -> 'azure')
- Lightweight provider registry for extensibility
- Optional Prompty support: load .prompty then merge into provider/instructions/client config
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Callable, Optional

from config.settings import Settings
from prompts.loader import load_prompty
from mcp.manager import MCPManager, load_manager_from_path
from tools.registry import attach_tools_to_agent, collect_tools_from_mcp

# Optional imports (only when actually used)
try:  # OpenAI Responses
    from agent_framework.openai import OpenAIResponsesClient  # type: ignore
except Exception:  # pragma: no cover - optional in CI without package
    OpenAIResponsesClient = None  # type: ignore

try:  # Azure Responses
    from agent_framework.azure import AzureOpenAIResponsesClient  # type: ignore
    from azure.identity import AzureCliCredential  # type: ignore
except Exception:  # pragma: no cover
    AzureOpenAIResponsesClient = None  # type: ignore
    AzureCliCredential = None  # type: ignore


@dataclass
class BuiltAgent:
    """A small wrapper around the underlying Agent Framework agent.

    The wrapped agent must implement:
      - async def run(prompt: str) -> Any (with .text attr or str)
      - async def run_stream(prompt: str) -> AsyncIterator[Any] (with .text attr or str)
    """

    agent: Any

    async def run(self, prompt: str) -> str:
        result = await self.agent.run(prompt)
        # Agent Framework typically returns an object with .text
        if hasattr(result, "text") and isinstance(result.text, str):
            return result.text
        # Fallback to string representation
        return str(result)

    async def run_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        async for update in self.agent.run_stream(prompt):
            text = getattr(update, "text", None)
            if isinstance(text, str) and text:
                yield text


class MockResponsesAgent:
    """A simple mock streaming agent for local testing.

    It echoes the prompt with a prefix and streams in small chunks.
    """

    def __init__(self, name: str, instructions: str) -> None:
        self.name = name
        self.instructions = instructions

    async def run(self, prompt: str) -> SimpleNamespace:
        text = f"[mock:{self.name}] {self.instructions} | {prompt}"
        return SimpleNamespace(text=text)

    async def run_stream(self, prompt: str):  # -> AsyncIterator[SimpleNamespace]
        text = f"[mock:{self.name}] {self.instructions} | {prompt}"
        # stream in 4 chunks
        n = max(1, len(text) // 4)
        for i in range(0, len(text), n):
            await asyncio.sleep(0.01)
            yield SimpleNamespace(text=text[i : i + n])


# --- Option B: Provider alias normalization and registry ---

# Public for testing
def normalize_provider(value: str) -> str:
    """Normalize provider aliases to canonical ids.

    Known canonical values: 'mock', 'openai', 'azure'.
    Examples:
      - 'azure_foundry', 'azure-openai', 'azure-ai' -> 'azure'
      - 'oai' -> 'openai'
    """
    v = (value or "").strip().lower()
    aliases = {
        "azure_foundry": "azure",
        "azure-foundry": "azure",
        "foundry": "azure",
        "azure-openai": "azure",
        "azure_ai": "azure",
        "azure-ai": "azure",
        "azureai": "azure",
        "oai": "openai",
    }
    return aliases.get(v, v)


def _build_mock(settings: Settings, name: str, instructions: str, overrides: Optional[dict[str, Any]] = None) -> BuiltAgent:
    """Build a mock agent. Overrides are ignored for mock."""
    return BuiltAgent(agent=MockResponsesAgent(name=name, instructions=instructions))


def _build_openai(settings: Settings, name: str, instructions: str, overrides: Optional[dict[str, Any]] = None) -> BuiltAgent:
    if OpenAIResponsesClient is None:  # pragma: no cover
        raise RuntimeError("OpenAIResponsesClient not available. Ensure agent-framework is installed.")
    client_kwargs: dict[str, Any] = {}
    if settings.openai_model:
        client_kwargs["ai_model_id"] = settings.openai_model
    if settings.openai_api_key:
        client_kwargs["api_key"] = settings.openai_api_key
    if overrides:
        client_kwargs.update({k: v for k, v in overrides.items() if v is not None})
    client = OpenAIResponsesClient(**client_kwargs)
    agent = client.create_agent(name=name, instructions=instructions)
    return BuiltAgent(agent=agent)


def _build_azure(settings: Settings, name: str, instructions: str, overrides: Optional[dict[str, Any]] = None) -> BuiltAgent:
    if AzureOpenAIResponsesClient is None:  # pragma: no cover
        raise RuntimeError(
            "AzureOpenAIResponsesClient not available. Ensure agent-framework and azure-identity are installed."
        )
    client_kwargs: dict[str, Any] = {}
    if settings.azure_openai_endpoint:
        client_kwargs["endpoint"] = settings.azure_openai_endpoint
    if settings.azure_openai_deployment_name:
        client_kwargs["deployment_name"] = settings.azure_openai_deployment_name
    if settings.azure_openai_api_version:
        client_kwargs["api_version"] = settings.azure_openai_api_version
    if settings.azure_openai_api_key:
        client_kwargs["api_key"] = settings.azure_openai_api_key
    elif settings.azure_openai_use_cli_credential and AzureCliCredential is not None:
        client_kwargs["credential"] = AzureCliCredential()

    if overrides:
        client_kwargs.update({k: v for k, v in overrides.items() if v is not None})

    client = AzureOpenAIResponsesClient(**client_kwargs)
    agent = client.create_agent(name=name, instructions=instructions)
    return BuiltAgent(agent=agent)


PROVIDER_REGISTRY: dict[str, Callable[[Settings, str, str, Optional[dict[str, Any]]], BuiltAgent]] = {
    "mock": _build_mock,
    "openai": _build_openai,
    "azure": _build_azure,
}


def build_agent(
    settings: Settings,
    provider_override: Optional[str] = None,
    instructions_override: Optional[str] = None,
    template_name: Optional[str] = None,
    template_variables: Optional[dict[str, Any]] = None,
    enable_mcp: Optional[bool] = None,
    mcp_manager: Optional[MCPManager] = None,
) -> BuiltAgent:
    """Build an Agent Framework agent based on settings/provider.

    Args:
        settings: App settings object.
        provider_override: Optional provider override.
        instructions_override: Optional system prompt override.
        template_name: Optional prompty template name (without extension).
        template_variables: Reserved for future interpolation support.

    Returns:
        BuiltAgent: A wrapper exposing run and run_stream to return text.
    """
    prompty = None
    if template_name:
        try:
            prompty = load_prompty(template_name)
        except Exception as e:
            # Fall back silently to settings if prompty not found/invalid
            prompty = None

    # Determine provider
    provider_raw = provider_override or (prompty.provider if prompty and prompty.provider else settings.provider)
    provider = normalize_provider(provider_raw)

    # Determine instructions
    name = settings.agent_name
    instructions = instructions_override or (prompty.instructions if prompty and prompty.instructions else settings.agent_instructions)

    # Build provider-specific overrides from prompty
    overrides: dict[str, Any] = {}
    if provider == "openai" and prompty and prompty.openai and prompty.openai.model:
        overrides["ai_model_id"] = prompty.openai.model
    if provider == "azure" and prompty and prompty.azure:
        if prompty.azure.endpoint:
            overrides["endpoint"] = prompty.azure.endpoint
        if prompty.azure.deployment_name:
            overrides["deployment_name"] = prompty.azure.deployment_name
        if prompty.azure.api_version:
            overrides["api_version"] = prompty.azure.api_version

    builder = PROVIDER_REGISTRY.get(provider)
    if not builder:
        raise ValueError(f"Unsupported provider: {provider}")
    built = builder(settings, name, instructions, overrides or None)

    # Optionally attach MCP tools
    use_mcp = enable_mcp if enable_mcp is not None else settings.mcp_enabled
    if use_mcp:
        # Lazily load manager if not provided
        mgr = mcp_manager
        if mgr is None:
            # Resolve default config path
            cfg_path = settings.mcp_config_path
            if not cfg_path:
                from pathlib import Path

                cfg_path = str(
                    Path(__file__).resolve().parent.parent
                    / "mcp"
                    / "servers.yaml"
                )
            try:
                mgr = load_manager_from_path(cfg_path)
                if settings.mcp_auto_connect:
                    mgr.connect()
            except Exception:
                mgr = None  # Best-effort; continue without MCP
        if mgr is not None:
            tools = collect_tools_from_mcp(mgr)
            attach_tools_to_agent(built.agent, tools)

    return built
