"""The Neural Watt integration."""

from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv

from .api import NeuralWattApiError, NeuralWattAuthError
from .const import DOMAIN
from .coordinator import NeuralWattDataUpdateCoordinator
from .statistics import async_import_statistics

_PLATFORMS = ["sensor"]

SERVICE_BACKFILL_STATISTICS = "backfill_statistics"

BACKFILL_SCHEMA = vol.Schema(
    {
        vol.Required("start_date"): cv.date,
        vol.Optional("end_date"): cv.date,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = NeuralWattDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    async def _handle_backfill(call: ServiceCall) -> Any:
        start_date: date = call.data["start_date"]
        end_date: date = call.data.get("end_date", date.today())
        if end_date < start_date:
            return {"ok": False, "error": "end_date must not be before start_date"}
        coordinator_: NeuralWattDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        try:
            energy = await coordinator_.client.async_get_energy(start_date, end_date)
        except NeuralWattAuthError as err:
            return {"ok": False, "error": f"authentication failed: {err}"}
        except NeuralWattApiError as err:
            return {"ok": False, "error": str(err)}
        daily = energy.get("daily") or []
        if not daily:
            return {"ok": True, "imported_days": 0}
        async_import_statistics(hass, daily)
        return {"ok": True, "imported_days": len(daily)}

    hass.services.async_register(
        DOMAIN,
        SERVICE_BACKFILL_STATISTICS,
        _handle_backfill,
        schema=BACKFILL_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_BACKFILL_STATISTICS)
    return unload_ok
