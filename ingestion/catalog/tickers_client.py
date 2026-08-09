from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from ingestion.catalog.http_client import BrapiHttpClient

logger = logging.getLogger(__name__)

_TICKERS_PATH = "/v2/tickers"


class TickersClient:
    def __init__(self, http_client: BrapiHttpClient, page_size: int = 100) -> None:
        self._http_client = http_client
        self._page_size = page_size

    def fetch_all(self) -> list[dict[str, Any]]:
        return list(self.iter_all())

    def iter_all(self) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            payload = self._http_client.get(
                _TICKERS_PATH, params={"page": page, "page_size": self._page_size}
            )

            results: list[dict[str, Any]] = payload.get("results", [])
            pagination = payload.get("pagination", {})

            logger.info(
                "page %s/%s - %s ticker in page",
                pagination.get("page", page),
                pagination.get("totalPages", "?"),
                len(results)
            )
            yield from results

            if not pagination.get("hasNextPage"):
                break
            page += 1
