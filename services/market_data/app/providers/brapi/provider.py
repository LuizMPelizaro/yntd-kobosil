from __future__ import annotations

from typing import List, Optional

from app.core.contracts import MarketDataResult, Quote, HistoricalSeries, Dividends, Statistics, FinancialData
from app.core.provider import MarketDataProvider
from app.providers.brapi import mappers
from app.providers.brapi.client import BrapiStocksClient


class BrapiProvider(MarketDataProvider):
    def __init__(self, client: BrapiStocksClient) -> None:
        self._client = client

    async def get_quote(self, symbols: List[str]) -> List[MarketDataResult[Quote]]:
        payload = await self._client.fetch("quote", symbols)
        return mappers.to_quote_results(payload)

    async def get_historical(
        self,
        symbols: List[str],
        *,
        range_: Optional[str] = None,
        interval: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[MarketDataResult[HistoricalSeries]]:
        payload = await self._client.fetch(
            "historical",
            symbols,
            params={
                "range": range_,
                "interval": interval,
                "startDate": start_date,
                "endDate": end_date,
                "sortOrder": sort_order,
            },
        )
        return mappers.to_historical_results(payload)

    async def get_dividends(
        self,
        symbols: List[str],
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[MarketDataResult[Dividends]]:
        payload = await self._client.fetch(
            "dividends",
            symbols,
            params={
                "startDate": start_date,
                "endDate": end_date,
                "sortBy": sort_by,
                "sortOrder": sort_order,
            },
        )
        return mappers.to_dividends_results(payload)

    async def get_statistics(
        self,
        symbols: List[str],
        *,
        period: Optional[str] = None,
        mode: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[MarketDataResult[Statistics]]:
        payload = await self._client.fetch(
            "statistics",
            symbols,
            params={
                "period": period,
                "mode": mode,
                "startDate": start_date,
                "endDate": end_date,
            },
        )
        return mappers.to_statistics_results(payload)

    async def get_financial_data(
        self,
        symbols: List[str],
        *,
        period: Optional[str] = None,
        mode: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[MarketDataResult[FinancialData]]:
        payload = await self._client.fetch(
            "financial-data",
            symbols,
            params={
                "period": period,
                "mode": mode,
                "startDate": start_date,
                "endDate": end_date,
            },
        )
        return mappers.to_financial_data_results(payload)