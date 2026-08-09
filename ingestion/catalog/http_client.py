from __future__ import annotations

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ingestion.catalog.config import BRAPI_CONFIG, BrapiConfig

logger = logging.getLogger(__name__)


class BrapiApiError(Exception):
    pass


class BrapiHttpClient:
    def __init__(self, config: BrapiConfig = BRAPI_CONFIG) -> None:
        self.config = config
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {self.config.api_key}"})

        retry = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.config.base_url}{path}"
        logger.debug(f"GET %s params %s", url, params)

        response = self.session.get(url, params=params, timeout=self.config.timeout_seconds)

        if not response.ok:
            raise BrapiApiError(
                f"Error {response.status_code} to call: {response.text}"
            )
        return response.json()

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "BrapiHttpClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
