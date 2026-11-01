from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_provider
from app.main import app
from app.providers.brapi.client import BrapiApiError


@pytest.fixture
def mock_provider() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(mock_provider: AsyncMock) -> TestClient:
    app.dependency_overrides[get_provider] = lambda: mock_provider
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_quote_parses_and_uppercases_symbols(client: TestClient, mock_provider: AsyncMock) -> None:
    mock_provider.get_quote.return_value = []

    client.get("/v1/quote?symbols=petr4, vale3")

    mock_provider.get_quote.assert_awaited_once_with(["PETR4", "VALE3"])


def test_quote_rejects_empty_symbols(client: TestClient) -> None:
    response = client.get("/v1/quote?symbols=")

    assert response.status_code == 400


def test_quote_maps_upstream_error_to_502(client: TestClient, mock_provider: AsyncMock) -> None:
    mock_provider.get_quote.side_effect = BrapiApiError("boom")

    response = client.get("/v1/quote?symbols=PETR4")

    assert response.status_code == 502


def test_historical_forwards_range_and_interval(
    client: TestClient, mock_provider: AsyncMock
) -> None:
    mock_provider.get_historical.return_value = []

    client.get("/v1/historical?symbols=PETR4&range=1mo&interval=1d&sortOrder=asc")

    mock_provider.get_historical.assert_awaited_once_with(
        ["PETR4"],
        range_="1mo",
        interval="1d",
        start_date=None,
        end_date=None,
        sort_order="asc",
    )


def test_dividends_forwards_sort_params(client: TestClient, mock_provider: AsyncMock) -> None:
    mock_provider.get_dividends.return_value = []

    client.get("/v1/dividends?symbols=ITSA4&sortBy=rate&sortOrder=desc")

    mock_provider.get_dividends.assert_awaited_once_with(
        ["ITSA4"],
        start_date=None,
        end_date=None,
        sort_by="rate",
        sort_order="desc",
    )


def test_statistics_forwards_period_and_mode(client: TestClient, mock_provider: AsyncMock) -> None:
    mock_provider.get_statistics.return_value = []

    client.get("/v1/statistics?symbols=WEGE3&period=quarterly&mode=history")

    mock_provider.get_statistics.assert_awaited_once_with(
        ["WEGE3"], period="quarterly", mode="history", start_date=None, end_date=None
    )


def test_financial_data_forwards_period_and_mode(
    client: TestClient, mock_provider: AsyncMock
) -> None:
    mock_provider.get_financial_data.return_value = []

    client.get("/v1/financial-data?symbols=WEGE3&mode=current")

    mock_provider.get_financial_data.assert_awaited_once_with(
        ["WEGE3"], period=None, mode="current", start_date=None, end_date=None
    )

def test_duplicate_symbols_are_removed(client, mock_provider):
    mock_provider.get_quote.return_value = []
    assert client.get('/v1/quote?symbols=petr4,PETR4').status_code == 200
    mock_provider.get_quote.assert_awaited_once_with(['PETR4'])


def test_invalid_dates_and_symbols_do_not_call_provider(client, mock_provider):
    assert client.get('/v1/quote?symbols=PETR4/secret').status_code == 400
    assert client.get('/v1/historical?symbols=PETR4&startDate=bad').status_code == 400
    assert client.get('/v1/historical?symbols=PETR4&startDate=2026-02-01&endDate=2026-01-01').status_code == 400
    mock_provider.get_quote.assert_not_awaited()
    mock_provider.get_historical.assert_not_awaited()


def test_busy_error_is_standardized(client, mock_provider):
    from app.core.errors import MarketDataError
    mock_provider.get_quote.side_effect = MarketDataError('Service is busy', code='service_busy', status_code=503)
    response = client.get('/v1/quote?symbols=PETR4')
    assert response.status_code == 503
    assert response.json() == {'error': {'code': 'service_busy', 'message': 'Service is busy'}}
