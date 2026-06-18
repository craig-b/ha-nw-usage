"""Shared test helpers for neuralwatt tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp


class _FakeResponseCM:
    """Async context manager yielding a mock ClientResponse."""

    def __init__(self, status: int, json_data: dict[str, Any] | None) -> None:
        self._status = status
        self._json_data = json_data or {}

    async def __aenter__(self) -> MagicMock:
        resp = MagicMock()
        resp.status = self._status
        resp.json = AsyncMock(return_value=self._json_data)
        if self._status >= 400:
            resp.raise_for_status = MagicMock(
                side_effect=aiohttp.ClientError(f"HTTP {self._status}")
            )
        else:
            resp.raise_for_status = MagicMock()
        return resp

    async def __aexit__(self, *_args: object) -> bool:
        return False


def mock_session(
    status: int = 200,
    json_data: dict[str, Any] | None = None,
    exception: Exception | None = None,
) -> MagicMock:
    """Return a MagicMock session whose ``.get`` returns a fake response.

    If *exception* is given, ``session.get`` raises it directly (connection error).
    """
    session = MagicMock()
    if exception is not None:
        session.get = MagicMock(side_effect=exception)
    else:
        session.get = MagicMock(return_value=_FakeResponseCM(status, json_data))
    return session
