"""Tests for chat endpoints (non-streaming and streaming)."""
from __future__ import annotations

import asyncio
import json
import re

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_chat_non_streaming_success(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"message": "hello world", "provider": "mock"}
        r = await client.post("/v1/chat", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "text" in data
        # Should include our prompt in the echoed mock output
        assert "hello world" in data["text"]
        assert "mock:" in data["text"]


@pytest.mark.asyncio
async def test_chat_invalid_provider_returns_400(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"message": "hi", "provider": "unknown"}
        r = await client.post("/v1/chat", json=payload)
        assert r.status_code == 400
        data = r.json()
        assert data.get("detail")


@pytest.mark.asyncio
async def test_chat_streaming_sse(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"message": "stream please", "provider": "mock"}
        async with client.stream("POST", "/v1/chat/stream", json=payload) as r:
            assert r.status_code == 200
            assert r.headers.get("content-type", "").startswith("text/event-stream")
            full_text = ""
            async for line in r.aiter_lines():
                if not line:
                    continue
                # Expect SSE data lines like: data: {"text": "..."}
                if not line.startswith("data: "):
                    continue
                try:
                    obj = json.loads(line[len("data: "):])
                except json.JSONDecodeError:
                    continue
                chunk = obj.get("text")
                if chunk:
                    full_text += chunk
            assert "stream please" in full_text
            assert "mock:" in full_text


@pytest.mark.asyncio
async def test_chat_empty_message_validation(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"message": ""}
        r = await client.post("/v1/chat", json=payload)
        # FastAPI/Pydantic validation error
        assert r.status_code == 422
