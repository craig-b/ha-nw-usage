"""Statistics backfill for Neural Watt integration."""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_STATISTIC_ID = f"{DOMAIN}:energy_consumed_daily"
_STATISTIC_NAME = "Neural Watt energy"
_UNIT_CLASS = "energy"


def _metadata() -> StatisticMetaData:
    return {
        "has_mean": False,
        "mean_type": StatisticMeanType.NONE,
        "has_sum": True,
        "name": _STATISTIC_NAME,
        "source": DOMAIN,
        "statistic_id": _STATISTIC_ID,
        "unit_class": _UNIT_CLASS,
        "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
    }


def _build_rows(daily: list[dict[str, Any]]) -> list[StatisticData]:
    rows: list[StatisticData] = []
    cumulative = 0.0
    sorted_daily = sorted(daily, key=lambda entry: entry.get("date", ""))
    for entry in sorted_daily:
        try:
            day = date.fromisoformat(entry["date"])
        except (KeyError, ValueError, TypeError):
            continue
        try:
            kwh = float(entry.get("energy_kwh", 0) or 0)
        except (TypeError, ValueError):
            continue
        cumulative += kwh
        start = dt_util.as_utc(dt_util.start_of_local_day(day))
        rows.append(
            {
                "start": start,
                "state": kwh,
                "sum": cumulative,
                "last_reset": start,
            }
        )
    return rows


def async_import_statistics(
    hass: HomeAssistant, daily: list[dict[str, Any]] | None
) -> None:
    if not daily:
        return
    rows = _build_rows(daily)
    if not rows:
        return
    try:
        async_add_external_statistics(hass, _metadata(), rows)
    except Exception as err:
        _LOGGER.warning("Failed to import Neural Watt statistics: %s", err)
