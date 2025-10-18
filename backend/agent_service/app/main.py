"""
FastAPI application exposing Microsoft Agent Framework-based chat endpoints.

Endpoints:
- POST /v1/chat: Non-streaming chat that returns the full response text.
- POST /v1/chat/stream: SSE streaming endpoint emitting text chunks.
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from agents.factory import build_agent
from app.models import ChatRequest, ChatResponse, ErrorResponse
from config.settings import get_settings

app = FastAPI(title="Agent Service", version="0.1.0")


async def _sse_event_stream(
    prompt: str,
    provider: Optional[str],
    instructions: Optional[str],
    template: Optional[str],
    variables: Optional[Dict[str, Any]],
) -> AsyncGenerator[bytes, None]:
    """Yield Server-Sent Events (SSE) chunks for the agent response.

    Args:
        prompt: The user's input message.
        provider: Optional provider override.
        instructions: Optional system prompt override.

    Yields:
        bytes: SSE-formatted bytes: b"data: {json}\n\n"
    """
    settings = get_settings()
    try:
        agent = build_agent(
            settings,
            provider_override=provider,
            instructions_override=instructions,
            template_name=template,
            template_variables=variables,
        )
    except ValueError as exc:
        # Convert to SSE error event then end stream
        payload = {"error": str(exc)}
        yield f"data: {json.dumps(payload)}\n\n".encode("utf-8")
        return

    async for chunk in agent.run_stream(prompt):
        payload = {"text": chunk}
        # each event as a JSON object line
        yield f"data: {json.dumps(payload)}\n\n".encode("utf-8")


@app.post("/v1/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}})
async def chat(request: ChatRequest) -> ChatResponse:
    """Non-streaming chat with the agent.

    Returns full response text after the agent finishes.
    """
    settings = get_settings()
    try:
        agent = build_agent(
            settings,
            provider_override=request.provider,
            instructions_override=request.instructions,
            template_name=request.template,
            template_variables=request.variables,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result_text = await agent.run(request.message)
    return ChatResponse(text=result_text)


@app.post("/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using SSE (Server-Sent Events).

    Yields JSON events of the shape: {"text": "..."}
    """
    generator = _sse_event_stream(
        prompt=request.message,
        provider=request.provider,
        instructions=request.instructions,
        template=request.template,
        variables=request.variables,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@app.get("/healthz")
async def healthz() -> JSONResponse:
    """Liveness probe."""
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=False)
