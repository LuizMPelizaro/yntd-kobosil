from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import BRAPI_SETTINGS, BrapiSettings

logger = logging.getLogger(__name__)


class BrapiApiError(Exception):
    """Raised when brapi.dev returns a non-2xx response after retries."""


class BrapiStocksClient:
    """Thin async client for /api/v2/stocks/{resource}."""

    def __init__(self, settings: BrapiSettings = BRAPI_SETTINGS) -> None:
        self._settings = settings
        transport = httpx.AsyncHTTPTransport(retries=settings.max_retries)
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            headers={"Authorization": f"Bearer {settings.api_key}"},
            timeout=settings.timeout_seconds,
            transport=transport,
        )

    async def fetch(
        self,
        resource: str,
        symbols: List[str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        GET /api/v2/stocks/{resource}?symbols=A,B&<params>

        `resource` is one of: quote, historical, dividends, statistics,
        financial-data. `params` entries with value None are dropped,
        so callers can pass every optional field unconditionally.
        """
        query: Dict[str, Any] = {"symbols": ",".join(symbols)}
        if params:
            query.update({key: value for key, value in params.items() if value is not None})

        url = f"/v2/stocks/{resource}"
        logger.debug("GET %s params=%s", url, query)

        response = await self._client.get(url, params=query)
        if response.is_error:
            raise BrapiApiError(
                f"Error {response.status_code} calling {resource}: {response.text[:300]}"
            )
        return response.json()

    async def aclose(self) -> None:
        await self._client.aclose()