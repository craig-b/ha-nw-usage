"""Tests for the Neural Watt API client."""
from __future__ import annotations

import re
from datetime import date

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from custom_components.neuralwatt.api import (
    NeuralWattApiError,
    NeuralWattAuthError,
    NeuralWattClient,
)

API_BASE = "https://api.neuralwatt.com/v1"
ENERGY_URL = re.compile(r"^https://api\.neuralwatt\.com/v1/usage/energy(\?.*)?$")
SUMMARY_URL = f"{API_BASE}/usage/summary"


@pytest_asyncio.fixture
async def session() -> aiohttp.ClientSession:
    """Create an aiohttp session."""
    s = aiohttp.ClientSession()
    yield s
    await s.close()


@pytest.mark.asyncio
async def test_async_get_energy_returns_json(
    session: aiohttp.ClientSession,
) -> None:
    payload = {
        "period": {"start": "2024-11-01", "end": "2024-11-30"},
        "totals": {
            "requests": 2,
            "requests_with_energy": 2,
            "energy_kwh": 0.001,
            "energy_joules": 3600,
        },
        "daily": [
            {
                "date": "2024-11-30",
                "requests": 1,
                "requests_with_energy": 1,
                "energy_kwh": 0.0005,
                "energy_joules": 1800,
            }
        ],
    }
    with aioresponses() as m:
        m.get(ENERGY_URL, payload=payload)
        client = NeuralWattClient(session, "sk-test-key")
        result = await client.async_get_energy(
            start_date=date(2024, 11, 1), end_date=date(2024, 11, 30)
        )
    assert result == payload
    # Authorization header should be present
    request_key = list(m.requests.keys())[0]
    sent_kwargs = m.requests[request_key][0].kwargs
    assert sent_kwargs.get("headers", {}).get("Authorization") == "Bearer sk-test-key"
    assert sent_kwargs.get("params", {}).get("start_date") == "2024-11-01"
    assert sent_kwargs.get("params", {}).get("end_date") == "2024-11-30"


@pytest.mark.asyncio
async def test_async_get_summary_returns_json(
    session: aiohttp.ClientSession,
) -> None:
    payload = {
        "energy_kwh_consumed": 0.001,
        "energy_kwh_charged": 0.001,
        "total_cost_usd": 0.0001,
        "accounting_method": "energy",
    }
    with aioresponses() as m:
        m.get(SUMMARY_URL, payload=payload)
        client = NeuralWattClient(session, "sk-test-key")
        result = await client.async_get_summary()
    assert result == payload


@pytest.mark.asyncio
async def test_401_raises_auth_error(session: aiohttp.ClientSession) -> None:
    with aioresponses() as m:
        m.get(SUMMARY_URL, status=401, payload={"error": "unauthorized"})
        client = NeuralWattClient(session, "sk-test-key")
        with pytest.raises(NeuralWattAuthError):
            await client.async_get_summary()


@pytest.mark.asyncio
async def test_500_raises_api_error(session: aiohttp.ClientSession) -> None:
    with aioresponses() as m:
        m.get(SUMMARY_URL, status=500, payload={"error": "boom"})
        client = NeuralWattClient(session, "sk-test-key")
        with pytest.raises(NeuralWattApiError):
            await client.async_get_summary()


@pytest.mark.asyncio
async def test_connection_error_raises_api_error(
    session: aiohttp.ClientSession,
) -> None:
    with aioresponses() as m:
        m.get(SUMMARY_URL, exception=aiohttp.ClientError("boom"))
        client = NeuralWattClient(session, "sk-test-key")
        with pytest.raises(NeuralWattApiError):
            await client.async_get_summary()
