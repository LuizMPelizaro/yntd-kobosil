from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.contracts import (
    Dividends,
    FinancialData,
    HistoricalSeries,
    MarketDataResult,
    Quote,
    Statistics,
)


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_quote(self, symbols: List[str]) -> List[MarketDataResult[Quote]]:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def get_dividends(
        self,
        symbols: List[str],
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[MarketDataResult[Dividends]]:
        ...

    @abstractmethod
    async def get_statistics(
        self,
        symbols: List[str],
        *,
        period: Optional[str] = None,
        mode: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[MarketDataResult[Statistics]]:
        ...

    @abstractmethod
    async def get_financial_data(
        self,
        symbols: List[str],
        *,
        period: Optional[str] = None,
        mode: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[MarketDataResult[FinancialData]]:
        ...