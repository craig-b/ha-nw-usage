"""Neural Watt API client."""

from __future__ import annotations

from datetime import date
from typing import Any

import aiohttp

from .const import API_BASE_URL, API_ENERGY_ENDPOINT, API_SUMMARY_ENDPOINT


class NeuralWattApiError(Exception):
    pass


class NeuralWattAuthError(Exception):
    pass


class NeuralWattClient:
    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self._session = session
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    async def async_get_energy(self, start_date: date, end_date: date) -> dict[str, Any]:
        url = f"{API_BASE_URL}{API_ENERGY_ENDPOINT}"
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        return await self._request(url, params=params)

    async def async_get_summary(self) -> dict[str, Any]:
        url = f"{API_BASE_URL}{API_SUMMARY_ENDPOINT}"
        return await self._request(url)

    async def _request(self, url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        try:
            async with self._session.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 401:
                    raise NeuralWattAuthError("Invalid API key")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            raise NeuralWattApiError(str(err)) from err
        except NeuralWattAuthError:
            raise
        except Exception as err:
            raise NeuralWattApiError(str(err)) from err
