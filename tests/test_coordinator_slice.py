"""Tests for Neural Watt coordinator slicing logic."""
from __future__ import annotations

from datetime import date

from custom_components.neuralwatt.coordinator import (
    NeuralWattDataUpdateCoordinator,
)


def _daily_entry(d: str, kwh: float, requests: int = 1, with_energy: int = 1) -> dict:
    return {
        "date": d,
        "energy_kwh": kwh,
        "energy_joules": int(kwh * 3_600_000),
        "requests": requests,
        "requests_with_energy": with_energy,
    }


def test_slice_single_day() -> None:
    daily = [
        _daily_entry("2024-11-30", 0.00078, 52, 52),
        _daily_entry("2024-11-29", 0.00072, 48, 48),
    ]
    result = NeuralWattDataUpdateCoordinator._slice_daily(
        daily, date(2024, 11, 30), date(2024, 11, 30)
    )
    assert result["requests"] == 52
    assert result["requests_with_energy"] == 52
    assert result["energy_kwh"] == 0.00078
    assert result["energy_joules"] == 2808
    assert result["last_reset"] is not None


def test_slice_range_sums_multiple_days() -> None:
    daily = [
        _daily_entry("2024-11-01", 0.0010, 10, 10),
        _daily_entry("2024-11-15", 0.0020, 20, 20),
        _daily_entry("2024-11-30", 0.0030, 30, 30),
        _daily_entry("2024-12-01", 0.0040, 40, 40),
    ]
    result = NeuralWattDataUpdateCoordinator._slice_daily(
        daily, date(2024, 11, 1), date(2024, 11, 30)
    )
    assert result["requests"] == 60
    assert result["requests_with_energy"] == 60
    assert result["energy_kwh"] == 0.0060
    assert result["energy_joules"] == 21600


def test_slice_skips_out_of_range_days() -> None:
    daily = [
        _daily_entry("2024-10-31", 0.0001, 1, 1),
        _daily_entry("2024-11-15", 0.0010, 10, 10),
        _daily_entry("2024-12-01", 0.0001, 1, 1),
    ]
    result = NeuralWattDataUpdateCoordinator._slice_daily(
        daily, date(2024, 11, 1), date(2024, 11, 30)
    )
    assert result["requests"] == 10
    assert result["energy_kwh"] == 0.0010


def test_slice_empty_daily() -> None:
    result = NeuralWattDataUpdateCoordinator._slice_daily(
        [], date(2024, 11, 1), date(2024, 11, 30)
    )
    assert result["requests"] == 0
    assert result["energy_kwh"] == 0.0
    assert result["energy_joules"] == 0


def test_slice_handles_malformed_entries() -> None:
    daily: list[dict] = [
        {"date": "not-a-date", "energy_kwh": 1.0},
        {"date": "2024-11-15"},  # missing values
        {"date": "2024-11-16", "energy_kwh": "bad"},
        _daily_entry("2024-11-17", 0.0010, 5, 5),
    ]
    result = NeuralWattDataUpdateCoordinator._slice_daily(
        daily, date(2024, 11, 1), date(2024, 11, 30)
    )
    # only the well-formed entry on 2024-11-17 contributes
    assert result["requests"] == 5
    assert result["energy_kwh"] == 0.0010


def test_slice_month_start_sets_last_reset_to_first_of_month() -> None:
    daily = [_daily_entry("2024-11-15", 0.0010, 10, 10)]
    result = NeuralWattDataUpdateCoordinator._slice_daily(
        daily, date(2024, 11, 1), date(2024, 11, 30)
    )
    assert result["last_reset"] is not None
    assert "-01T00:00:00" in result["last_reset"]


def test_slice_rolling_window_has_no_last_reset() -> None:
    daily = [_daily_entry("2024-11-15", 0.0010, 10, 10)]
    result = NeuralWattDataUpdateCoordinator._slice_daily(
        daily, date(2024, 11, 5), date(2024, 11, 30)
    )
    # rolling start (not 1st, not single day) -> no last_reset
    assert result["last_reset"] is None
