from __future__ import annotations

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class MarketDataResult(BaseModel, Generic[T]):
    requested_symbol: str
    symbol: str
    changed: bool
    data: T


class Quote(BaseModel):
    model_config = ConfigDict(extra="allow")

    short_name: Optional[str] = None
    long_name: Optional[str] = None
    currency: Optional[str] = None
    regular_market_price: Optional[float] = None
    regular_market_day_high: Optional[float] = None
    regular_market_day_low: Optional[float] = None
    regular_market_change: Optional[float] = None
    regular_market_change_percent: Optional[float] = None
    regular_market_time: Optional[datetime] = None
    regular_market_volume: Optional[int] = None
    regular_market_previous_close: Optional[float] = None
    regular_market_open: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    market_cap: Optional[float] = None
    logo_url: Optional[str] = None


class HistoricalCandle(BaseModel):
    model_config = ConfigDict(extra="allow")

    date: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    adjusted_close: Optional[float] = None


class HistoricalSeries(BaseModel):
    used_interval: Optional[str] = None
    used_range: Optional[str] = None
    candles: List[HistoricalCandle] = []


class CashDividend(BaseModel):
    model_config = ConfigDict(extra="allow")

    payment_date: Optional[datetime] = None
    last_date_prior: Optional[datetime] = None
    approved_on: Optional[datetime] = None
    rate: Optional[float] = None
    label: Optional[str] = None
    related_to: Optional[str] = None
    isin_code: Optional[str] = None


class StockDividend(BaseModel):
    model_config = ConfigDict(extra="allow")

    factor: Optional[float] = None
    complete_factor: Optional[str] = None
    approved_on: Optional[datetime] = None
    label: Optional[str] = None
    isin_code: Optional[str] = None


class Dividends(BaseModel):
    cash_dividends: List[CashDividend] = []
    stock_dividends: List[StockDividend] = []


class Statistics(BaseModel):
    model_config = ConfigDict(extra="allow")

    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    earnings_per_share: Optional[float] = None
    shares_outstanding: Optional[float] = None
    book_value: Optional[float] = None
    profit_margins: Optional[float] = None


class FinancialData(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_revenue: Optional[float] = None
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    ebitda: Optional[float] = None
    gross_profits: Optional[float] = None
    free_cashflow: Optional[float] = None
    operating_cashflow: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    gross_margins: Optional[float] = None
    operating_margins: Optional[float] = None
    profit_margins: Optional[float] = None