"""Tests for the Neural Watt API client."""

from __future__ import annotations

from datetime import date

import aiohttp
import pytest
from conftest import mock_session

from custom_components.neuralwatt.api import (
    NeuralWattApiError,
    NeuralWattAuthError,
    NeuralWattClient,
)

API_BASE = "https://api.neuralwatt.com/v1"
ENERGY_URL = f"{API_BASE}/usage/energy"
SUMMARY_URL = f"{API_BASE}/usage/summary"


@pytest.mark.asyncio
async def test_async_get_energy_returns_json() -> None:
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
    session = mock_session(status=200, json_data=payload)
    client = NeuralWattClient(session, "sk-test-key")
    result = await client.async_get_energy(
        start_date=date(2024, 11, 1), end_date=date(2024, 11, 30)
    )
    assert result == payload
    session.get.assert_called_once()
    call_kwargs = session.get.call_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer sk-test-key"
    assert call_kwargs["params"]["start_date"] == "2024-11-01"
    assert call_kwargs["params"]["end_date"] == "2024-11-30"


@pytest.mark.asyncio
async def test_async_get_summary_returns_json() -> None:
    payload = {
        "energy_kwh_consumed": 0.001,
        "energy_kwh_charged": 0.001,
        "total_cost_usd": 0.0001,
        "accounting_method": "energy",
    }
    session = mock_session(status=200, json_data=payload)
    client = NeuralWattClient(session, "sk-test-key")
    result = await client.async_get_summary()
    assert result == payload


@pytest.mark.asyncio
async def test_401_raises_auth_error() -> None:
    session = mock_session(status=401, json_data={"error": "unauthorized"})
    client = NeuralWattClient(session, "sk-test-key")
    with pytest.raises(NeuralWattAuthError):
        await client.async_get_summary()


@pytest.mark.asyncio
async def test_500_raises_api_error() -> None:
    session = mock_session(status=500, json_data={"error": "boom"})
    client = NeuralWattClient(session, "sk-test-key")
    with pytest.raises(NeuralWattApiError):
        await client.async_get_summary()


@pytest.mark.asyncio
async def test_connection_error_raises_api_error() -> None:
    session = mock_session(exception=aiohttp.ClientError("boom"))
    client = NeuralWattClient(session, "sk-test-key")
    with pytest.raises(NeuralWattApiError):
        await client.async_get_summary()
