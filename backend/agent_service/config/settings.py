"""
Settings management for the Agent service.

Uses pydantic for validation and python-dotenv to load environment variables.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from a .env file if present
load_dotenv()


class Settings(BaseSettings):
    """Application settings.

    Args:
        provider: Which model provider to use. One of: 'openai', 'azure', 'mock'.
        debug: Enable debug mode.
        agent_name: Name for the agent instance.
        agent_instructions: System instructions for the agent.

        openai_api_key: API key for OpenAI (if using provider 'openai').
        openai_model: Model id for OpenAI Responses client (e.g., 'gpt-4o-mini').

        azure_openai_endpoint: Endpoint URL for Azure OpenAI (e.g., https://<resource>.openai.azure.com/).
        azure_openai_deployment_name: Deployment name for Azure OpenAI Responses.
        azure_openai_api_version: API version string for Azure OpenAI.
        azure_openai_use_cli_credential: If true, use Azure CLI credential (requires `az login`).
        azure_openai_api_key: API key for Azure OpenAI (optional alternative to CLI credential).
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
        case_sensitive=False,  # allow uppercase env vars like OPENAI_API_KEY, PROVIDER, etc.
    )

    provider: Literal["openai", "azure", "mock"] = Field(
        default="mock", description="Model provider: openai | azure | mock"
    )
    debug: bool = Field(default=False)

    agent_name: str = Field(default="JarvisAgent")
    agent_instructions: str = Field(default="You are a helpful assistant.")
    # Default prompty to load (used by Chainlit/app when template not provided)
    agent_prompty: Optional[str] = Field(default=None)

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")

    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = Field(default=None)
    azure_openai_deployment_name: Optional[str] = Field(default=None)
    azure_openai_api_version: Optional[str] = Field(default=None)
    azure_openai_use_cli_credential: bool = Field(default=True)
    azure_openai_api_key: Optional[str] = Field(default=None)

    # MCP (Model Context Protocol) integration
    mcp_enabled: bool = Field(default=False, description="Enable MCP tool integration")
    mcp_config_path: Optional[str] = Field(
        default=None,
        description="Path to MCP servers.yaml; default resolves to backend/agent_service/mcp/servers.yaml",
    )
    mcp_auto_connect: bool = Field(default=True, description="Auto-connect MCP servers on startup")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get a cached Settings instance.

    Returns:
        Settings: The application settings.
    """
    return Settings()
