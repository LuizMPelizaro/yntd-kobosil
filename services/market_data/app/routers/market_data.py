"""
Generic market data endpoints.

This router only depends on the MarketDataProvider interface — it has
no idea brapi.dev exists. Swapping or adding a provider never touches
this file; only `app.dependencies.get_provider` would change.
"""
from __future__ import annotations

from typing import List, Optional

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
from app.providers.brapi.client import BrapiApiError

router = APIRouter(prefix="/v1", tags=["market-data"])


def _parse_symbols(symbols: str) -> List[str]:
    parsed = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not parsed:
        raise HTTPException(status_code=400, detail="'symbols' must have at least one ticker")
    return parsed


@router.get("/quote", response_model=List[MarketDataResult[Quote]])
async def get_quote(
    symbols: str = Query(..., description="Comma-separated tickers, e.g. PETR4,VALE3"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[Quote]]:
    try:
        return await provider.get_quote(_parse_symbols(symbols))
    except BrapiApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/historical", response_model=List[MarketDataResult[HistoricalSeries]])
async def get_historical(
    symbols: str = Query(...),
    range_: Optional[str] = Query(None, alias="range"),
    interval: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, alias="startDate"),
    end_date: Optional[str] = Query(None, alias="endDate"),
    sort_order: Optional[str] = Query(None, alias="sortOrder"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[HistoricalSeries]]:
    try:
        return await provider.get_historical(
            _parse_symbols(symbols),
            range_=range_,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            sort_order=sort_order,
        )
    except BrapiApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/dividends", response_model=List[MarketDataResult[Dividends]])
async def get_dividends(
    symbols: str = Query(...),
    start_date: Optional[str] = Query(None, alias="startDate"),
    end_date: Optional[str] = Query(None, alias="endDate"),
    sort_by: Optional[str] = Query(None, alias="sortBy"),
    sort_order: Optional[str] = Query(None, alias="sortOrder"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[Dividends]]:
    try:
        return await provider.get_dividends(
            _parse_symbols(symbols),
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except BrapiApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/statistics", response_model=List[MarketDataResult[Statistics]])
async def get_statistics(
    symbols: str = Query(...),
    period: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, alias="startDate"),
    end_date: Optional[str] = Query(None, alias="endDate"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[Statistics]]:
    try:
        return await provider.get_statistics(
            _parse_symbols(symbols),
            period=period,
            mode=mode,
            start_date=start_date,
            end_date=end_date,
        )
    except BrapiApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/financial-data", response_model=List[MarketDataResult[FinancialData]])
async def get_financial_data(
    symbols: str = Query(...),
    period: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, alias="startDate"),
    end_date: Optional[str] = Query(None, alias="endDate"),
    provider: MarketDataProvider = Depends(get_provider),
) -> List[MarketDataResult[FinancialData]]:
    try:
        return await provider.get_financial_data(
            _parse_symbols(symbols),
            period=period,
            mode=mode,
            start_date=start_date,
            end_date=end_date,
        )
    except BrapiApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc