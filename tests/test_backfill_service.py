"""Tests for the neuralwatt.backfill_statistics service handler.

The handler is defined inline in async_setup_entry. We exercise the handler
body by replicating its logic against a stubbed coordinator and verifying
the call path on the API client. This avoids spinning up a full HA for
service registration.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest
from conftest import mock_session

from custom_components.neuralwatt.api import NeuralWattClient


async def _run_backfill(
    session: MagicMock,
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
async def test_backfill_success() -> None:
    payload = {
        "period": {"start": "2024-01-01", "end": "2024-11-30"},
        "totals": {
            "requests": 100,
            "requests_with_energy": 100,
            "energy_kwh": 1.0,
            "energy_joules": 3_600_000,
        },
        "daily": [
            {
                "date": "2024-01-15",
                "energy_kwh": 0.5,
                "energy_joules": 1_800_000,
                "requests": 50,
                "requests_with_energy": 50,
            },
            {
                "date": "2024-01-16",
                "energy_kwh": 0.5,
                "energy_joules": 1_800_000,
                "requests": 50,
                "requests_with_energy": 50,
            },
        ],
    }
    session = mock_session(status=200, json_data=payload)
    result = await _run_backfill(session, date(2024, 1, 1), date(2024, 11, 30))
    assert result == {"ok": True, "imported_days": 2}


@pytest.mark.asyncio
async def test_backfill_empty_daily() -> None:
    payload = {
        "period": {"start": "2024-01-01", "end": "2024-01-02"},
        "totals": {
            "requests": 0,
            "requests_with_energy": 0,
            "energy_kwh": 0,
            "energy_joules": 0,
        },
        "daily": [],
    }
    session = mock_session(status=200, json_data=payload)
    result = await _run_backfill(session, date(2024, 1, 1), date(2024, 1, 2))
    assert result == {"ok": True, "imported_days": 0}


@pytest.mark.asyncio
async def test_backfill_inverted_range_returns_error() -> None:
    session = mock_session()
    result = await _run_backfill(session, date(2024, 11, 30), date(2024, 1, 1))
    assert result["ok"] is False
    assert "end_date must not be before start_date" in result["error"]


@pytest.mark.asyncio
async def test_backfill_api_error_is_surfaced() -> None:
    session = mock_session(status=500, json_data={"error": "boom"})
    result = await _run_backfill(session, date(2024, 1, 1), date(2024, 1, 2))
    assert result["ok"] is False
    assert result["error"]
