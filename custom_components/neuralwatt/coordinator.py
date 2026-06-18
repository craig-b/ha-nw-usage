"""Data update coordinator for Neural Watt."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import NeuralWattApiError, NeuralWattAuthError, NeuralWattClient
from .const import (
    CONF_API_KEY,
    DEFAULT_POLL_INTERVAL_SECONDS,
    DOMAIN,
    PERIOD_LAST_30_DAYS,
    PERIOD_THIS_MONTH,
    PERIOD_TODAY,
)
from .statistics import async_import_statistics

_LOGGER = logging.getLogger(__name__)


def _local_midnight(now: datetime) -> datetime:
    return now.astimezone().replace(hour=0, minute=0, second=0, microsecond=0)


class NeuralWattDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL_SECONDS),
        )
        self.entry = entry
        self.client = NeuralWattClient(
            async_get_clientsession(hass),
            entry.data[CONF_API_KEY],
        )

    async def _async_update_data(self) -> dict[str, Any]:
        today = date.today()
        month_start = today.replace(day=1)
        rolling_start = today - timedelta(days=29)
        earliest_start = min(month_start, rolling_start)

        try:
            energy = await self.client.async_get_energy(earliest_start, today)
            summary = await self.client.async_get_summary()
        except NeuralWattAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except NeuralWattApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        daily = energy.get("daily") or []

        today_totals = self._slice_daily(daily, today, today)
        month_totals = self._slice_daily(daily, month_start, today)
        rolling_totals = self._slice_daily(daily, rolling_start, today)

        async_import_statistics(self.hass, daily)

        return {
            PERIOD_TODAY: today_totals,
            PERIOD_THIS_MONTH: month_totals,
            PERIOD_LAST_30_DAYS: rolling_totals,
            "summary": summary,
            "daily": daily,
            "fetched_at": datetime.now().astimezone(),
        }

    @staticmethod
    def _slice_daily(daily: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
        requests = 0
        requests_with_energy = 0
        energy_kwh = 0.0
        energy_joules = 0
        for entry in daily:
            try:
                entry_date = date.fromisoformat(entry["date"])
            except KeyError, ValueError, TypeError:
                continue
            if not (start <= entry_date <= end):
                continue
            try:
                requests += int(entry.get("requests", 0))
                requests_with_energy += int(entry.get("requests_with_energy", 0))
                energy_kwh += float(entry.get("energy_kwh", 0) or 0)
                energy_joules += int(entry.get("energy_joules", 0) or 0)
            except TypeError, ValueError:
                continue

        midnight = _local_midnight(datetime.now())
        if start == end:
            last_reset = midnight.isoformat()
        elif start.day == 1 and end >= start:
            last_reset = midnight.replace(day=1).isoformat()
        else:
            last_reset = None

        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "requests": requests,
            "requests_with_energy": requests_with_energy,
            "energy_kwh": energy_kwh,
            "energy_joules": energy_joules,
            "last_reset": last_reset,
        }
