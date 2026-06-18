"""Tests for the neuralwatt.backfill_statistics service handler.

The handler is defined inline in async_setup_entry. We exercise the handler
body by replicating its logic against a stubbed coordinator and verifying
the call path on the API client. This avoids spinning up a full HA for
service registration.
"""
from __future__ import annotations

import re
from datetime import date
from unittest.mock import MagicMock

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from custom_components.neuralwatt.api import NeuralWattClient

API_BASE = "https://api.neuralwatt.com/v1"
ENERGY_URL = re.compile(r"^https://api\.neuralwatt\.com/v1/usage/energy(\?.*)?$")


@pytest_asyncio.fixture
async def session() -> aiohttp.ClientSession:
    s = aiohttp.ClientSession()
    yield s
    await s.close()


async def _run_backfill(
    session: aiohttp.ClientSession,
    start: date,
    end: date,
) -> dict:
    """Mirror the inline handler in __init__.async_setup_entry."""
    from custom_components.neuralwatt.statistics import async_import_statistics

    client = NeuralWattClient(session, "sk-test-key")

    if end < start:
        return {"ok": False, "error": "end_date must not be before start_date"}

    try:
        energy = await client.async_get_energy(start, end)
    except Exception as err:
        return {"ok": False, "error": str(err)}

    daily = energy.get("daily") or []
    if not daily:
        return {"ok": True, "imported_days": 0}

    import_hass = MagicMock()
    async_import_statistics(import_hass, daily)
    return {"ok": True, "imported_days": len(daily)}


@pytest.mark.asyncio
async def test_backfill_success(session: aiohttp.ClientSession) -> None:
    payload = {
        "period": {"start": "2024-01-01", "end": "2024-11-30"},
        "totals": {"requests": 100, "requests_with_energy": 100, "energy_kwh": 1.0, "energy_joules": 3_600_000},
        "daily": [
            {"date": "2024-01-15", "energy_kwh": 0.5, "energy_joules": 1_800_000, "requests": 50, "requests_with_energy": 50},
            {"date": "2024-01-16", "energy_kwh": 0.5, "energy_joules": 1_800_000, "requests": 50, "requests_with_energy": 50},
        ],
    }
    with aioresponses() as m:
        m.get(ENERGY_URL, payload=payload)
        result = await _run_backfill(session, date(2024, 1, 1), date(2024, 11, 30))
    assert result == {"ok": True, "imported_days": 2}


@pytest.mark.asyncio
async def test_backfill_empty_daily(session: aiohttp.ClientSession) -> None:
    payload = {
        "period": {"start": "2024-01-01", "end": "2024-01-02"},
        "totals": {"requests": 0, "requests_with_energy": 0, "energy_kwh": 0, "energy_joules": 0},
        "daily": [],
    }
    with aioresponses() as m:
        m.get(ENERGY_URL, payload=payload)
        result = await _run_backfill(session, date(2024, 1, 1), date(2024, 1, 2))
    assert result == {"ok": True, "imported_days": 0}


@pytest.mark.asyncio
async def test_backfill_inverted_range_returns_error(
    session: aiohttp.ClientSession,
) -> None:
    result = await _run_backfill(session, date(2024, 11, 30), date(2024, 1, 1))
    assert result["ok"] is False
    assert "end_date must not be before start_date" in result["error"]


@pytest.mark.asyncio
async def test_backfill_api_error_is_surfaced(session: aiohttp.ClientSession) -> None:
    with aioresponses() as m:
        m.get(ENERGY_URL, status=500, payload={"error": "boom"})
        result = await _run_backfill(session, date(2024, 1, 1), date(2024, 1, 2))
    assert result["ok"] is False
    assert result["error"]
