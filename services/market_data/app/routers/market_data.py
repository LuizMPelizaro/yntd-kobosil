"""
Generic market data endpoints.

This router only depends on the MarketDataProvider interface — it has
no idea brapi.dev exists. Swapping or adding a provider never touches
this file; only `app.dependencies.get_provider` would change.
"""
from __future__ import annotations

from typing import List, Optional
import re
from datetime import date
from app.config import BRAPI_SETTINGS

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.contracts import (
    Dividends,
    FinancialData,
    HistoricalSeries,
    MarketDataResult,
    Quote,
    Statistics,
)
from app.core.provider import MarketDataProvider
from app.dependencies import get_provider


router = APIRouter(prefix="/v1", tags=["market-data"])


def _parse_symbols(symbols: str) -> List[str]:
    parsed = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not parsed:
        raise HTTPException(status_code=400, detail="'symbols' must have at least one ticker")
    parsed = list(dict.fromkeys(parsed))
    if len(parsed) > BRAPI_SETTINGS.max_symbols:
        raise HTTPException(status_code=400, detail='Too many symbols')
    if any(not re.fullmatch(r'[A-Z0-9^][A-Z0-9.^_-]{0,19}', symbol) for symbol in parsed):
        raise HTTPException(status_code=400, detail='Invalid symbol')
    return parsed


@router.get("/quote", response_model=List[MarketDataResult[Quote]])
async def get_quote(
    symbols: str = Query(..., max_length=4096, description="Comma-separated tickers, e.g. PETR4,VALE3"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[Quote]]:
    return await provider.get_quote(_parse_symbols(symbols))


@router.get("/historical", response_model=List[MarketDataResult[HistoricalSeries]])
async def get_historical(
    symbols: str = Query(..., max_length=4096),
    range_: Optional[str] = Query(None, max_length=32, alias="range"),
    interval: Optional[str] = Query(None, max_length=32),
    start_date: Optional[str] = Query(None, max_length=32, alias="startDate"),
    end_date: Optional[str] = Query(None, max_length=32, alias="endDate"),
    sort_order: Optional[str] = Query(None, max_length=32, alias="sortOrder"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[HistoricalSeries]]:
    _validate_dates(start_date, end_date)
    return await provider.get_historical(
        _parse_symbols(symbols),
        range_=range_,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        sort_order=sort_order,
    )


@router.get("/dividends", response_model=List[MarketDataResult[Dividends]])
async def get_dividends(
    symbols: str = Query(..., max_length=4096),
    start_date: Optional[str] = Query(None, max_length=32, alias="startDate"),
    end_date: Optional[str] = Query(None, max_length=32, alias="endDate"),
    sort_by: Optional[str] = Query(None, max_length=32, alias="sortBy"),
    sort_order: Optional[str] = Query(None, max_length=32, alias="sortOrder"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[Dividends]]:
    _validate_dates(start_date, end_date)
    return await provider.get_dividends(
        _parse_symbols(symbols),
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/statistics", response_model=List[MarketDataResult[Statistics]])
async def get_statistics(
    symbols: str = Query(..., max_length=4096),
    period: Optional[str] = Query(None, max_length=32),
    mode: Optional[str] = Query(None, max_length=32),
    start_date: Optional[str] = Query(None, max_length=32, alias="startDate"),
    end_date: Optional[str] = Query(None, max_length=32, alias="endDate"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[Statistics]]:
    _validate_dates(start_date, end_date)
    return await provider.get_statistics(
        _parse_symbols(symbols),
        period=period,
        mode=mode,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/financial-data", response_model=List[MarketDataResult[FinancialData]])
async def get_financial_data(
    symbols: str = Query(..., max_length=4096),
    period: Optional[str] = Query(None, max_length=32),
    mode: Optional[str] = Query(None, max_length=32),
    start_date: Optional[str] = Query(None, max_length=32, alias="startDate"),
    end_date: Optional[str] = Query(None, max_length=32, alias="endDate"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[FinancialData]]:
    _validate_dates(start_date, end_date)
    return await provider.get_financial_data(
        _parse_symbols(symbols),
        period=period,
        mode=mode,
        start_date=start_date,
        end_date=end_date,
    )

def _validate_dates(start, end):
    try:
        if any(value and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) for value in (start, end)):
            raise ValueError('Invalid date format')
        start_value = date.fromisoformat(start) if start else None
        end_value = date.fromisoformat(end) if end else None
    except ValueError:
        raise HTTPException(status_code=400, detail='Dates must use YYYY-MM-DD') from None
    if start_value and end_value and start_value > end_value:
        raise HTTPException(status_code=400, detail='startDate must not exceed endDate')
