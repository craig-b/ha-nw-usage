"""Tests for Neural Watt statistics backfill."""

from __future__ import annotations

from homeassistant.util import dt as dt_util

from custom_components.neuralwatt.statistics import _build_rows


def _entry(d: str, kwh: float) -> dict:
    return {"date": d, "energy_kwh": kwh, "energy_joules": int(kwh * 3_600_000)}


def test_build_rows_sorts_and_accumulates() -> None:
    daily = [
        _entry("2024-11-30", 0.003),
        _entry("2024-11-29", 0.002),
        _entry("2024-11-28", 0.001),
    ]
    rows = _build_rows(daily)
    assert len(rows) == 3
    # sorted ascending by date
    starts = [r["start"] for r in rows]
    assert starts == sorted(starts)
    # cumulative sum
    assert rows[0]["state"] == 0.001
    assert rows[0]["sum"] == 0.001
    assert rows[1]["state"] == 0.002
    assert rows[1]["sum"] == 0.003
    assert rows[2]["state"] == 0.003
    assert rows[2]["sum"] == 0.006


def test_build_rows_start_is_utc_midnight_local_day() -> None:
    daily = [_entry("2024-11-15", 0.001)]
    rows = _build_rows(daily)
    start = rows[0]["start"]
    expected = dt_util.as_utc(dt_util.start_of_local_day(__import__("datetime").date(2024, 11, 15)))
    assert start == expected
    # must be top of the hour, utc, tz-aware
    assert start.minute == 0
    assert start.second == 0
    assert start.utcoffset() is not None


def test_build_rows_last_reset_equals_start() -> None:
    daily = [_entry("2024-11-15", 0.001)]
    rows = _build_rows(daily)
    assert rows[0]["last_reset"] == rows[0]["start"]


def test_build_rows_skips_malformed() -> None:
    daily = [
        {"date": "not-a-date", "energy_kwh": 1.0},
        {"date": "2024-11-15"},  # missing energy_kwh -> defaults to 0
        _entry("2024-11-16", 0.002),
        {"energy_kwh": 1.0},  # missing date entirely
    ]
    rows = _build_rows(daily)
    # only the entry with valid date and numeric energy_kwh contributes a non-zero state;
    # 2024-11-15 contributes state 0 (kwh defaults), 2024-11-16 contributes 0.002
    assert len(rows) == 2
    assert rows[0]["state"] == 0.0
    assert rows[1]["state"] == 0.002


def test_build_rows_empty_input() -> None:
    assert _build_rows([]) == []


def test_state_and_sum_match_for_single_day() -> None:
    daily = [_entry("2024-11-15", 0.001)]
    rows = _build_rows(daily)
    assert rows[0]["state"] == 0.001
    assert rows[0]["sum"] == 0.001
