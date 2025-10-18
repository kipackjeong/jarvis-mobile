"""Tests for the health endpoint."""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_healthz(app):  # app fixture from conftest
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
