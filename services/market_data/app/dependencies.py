from fastapi import Request
from app.core.provider import MarketDataProvider


def get_client(request: Request):
    return request.app.state.market_client


def get_provider(request: Request) -> MarketDataProvider:
    return request.app.state.market_provider
