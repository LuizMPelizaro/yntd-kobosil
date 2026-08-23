from __future__ import annotations

from functools import lru_cache

from app.core.provider import MarketDataProvider
from app.providers.brapi.client import BrapiStocksClient
from app.providers.brapi.provider import BrapiProvider


@lru_cache
def get_client() -> BrapiStocksClient:
    return BrapiStocksClient()


def get_provider() -> MarketDataProvider:
    return BrapiProvider(get_client())