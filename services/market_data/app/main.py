from __future__ import annotations

import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.errors import MarketDataError
from app.providers.brapi.client import BrapiStocksClient
from app.providers.brapi.provider import BrapiProvider


@asynccontextmanager
async def lifespan(app):
    client = BrapiStocksClient()
    app.state.market_client = client
    app.state.market_provider = BrapiProvider(client)
    try:
        yield
    finally:
        await client.aclose()

from app.routers.market_data import router as market_data_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(lifespan=lifespan,
    title="Market Data Service",
    description="Provider-agnostic market data API. Currently backed by brapi.dev (B3).",
    version="0.1.0",
)

app.include_router(market_data_router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
@app.exception_handler(MarketDataError)
async def market_data_error(request: Request, exc: MarketDataError):
    return JSONResponse(status_code=exc.status_code, content={
        'error': {'code': exc.code, 'message': str(exc)}})
