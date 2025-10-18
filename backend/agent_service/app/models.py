"""
Pydantic request/response models for the Agent service API.
"""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request payload.

    Args:
        message: The user's input message to the agent.
        provider: Optional override for the model provider.
        instructions: Optional override for the agent's system instructions.
        template: Optional prompty name to load from `prompts/`.
        variables: Optional variables for templating (reserved for future use).
        stream: If true, the streaming endpoint will stream tokens/chunks.
    """

    message: str = Field(min_length=1, description="User input text for the agent")
    provider: Optional[Literal["openai", "azure", "mock"]] = None
    instructions: Optional[str] = None
    template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Non-streaming chat response."""

    text: str


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str
