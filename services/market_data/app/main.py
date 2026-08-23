from __future__ import annotations

import logging

from fastapi import FastAPI

from app.routers.market_data import router as market_data_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Market Data Service",
    description="Provider-agnostic market data API. Currently backed by brapi.dev (B3).",
    version="0.1.0",
)

app.include_router(market_data_router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}