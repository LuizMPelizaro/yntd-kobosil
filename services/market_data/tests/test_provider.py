from __future__ import annotations

from unittest.mock import AsyncMock

from app.providers.brapi.provider import BrapiProvider


async def test_get_quote_calls_client_with_quote_resource(fake_client: AsyncMock, quote_payload):
    fake_client.fetch.return_value = quote_payload
    provider = BrapiProvider(fake_client)

    results = await provider.get_quote(["PETR4"])

    fake_client.fetch.assert_awaited_once_with("quote", ["PETR4"])
    assert results[0].symbol == "PETR4"


async def test_get_historical_forwards_optional_params(
    fake_client: AsyncMock, historical_payload
):
    fake_client.fetch.return_value = historical_payload
    provider = BrapiProvider(fake_client)

    await provider.get_historical(["PETR4"], range_="1mo", interval="1d", sort_order="asc")

    fake_client.fetch.assert_awaited_once_with(
        "historical",
        ["PETR4"],
        params={
            "range": "1mo",
            "interval": "1d",
            "startDate": None,
            "endDate": None,
            "sortOrder": "asc",
        },
    )


async def test_get_dividends_forwards_optional_params(fake_client: AsyncMock, dividends_payload):
    fake_client.fetch.return_value = dividends_payload
    provider = BrapiProvider(fake_client)

    await provider.get_dividends(["ITSA4"], sort_by="rate", sort_order="desc")

    fake_client.fetch.assert_awaited_once_with(
        "dividends",
        ["ITSA4"],
        params={
            "startDate": None,
            "endDate": None,
            "sortBy": "rate",
            "sortOrder": "desc",
        },
    )


async def test_get_statistics_forwards_optional_params(fake_client: AsyncMock, statistics_payload):
    fake_client.fetch.return_value = statistics_payload
    provider = BrapiProvider(fake_client)

    await provider.get_statistics(["WEGE3"], period="quarterly", mode="history")

    fake_client.fetch.assert_awaited_once_with(
        "statistics",
        ["WEGE3"],
        params={
            "period": "quarterly",
            "mode": "history",
            "startDate": None,
            "endDate": None,
        },
    )


async def test_get_financial_data_forwards_optional_params(
    fake_client: AsyncMock, financial_data_payload
):
    fake_client.fetch.return_value = financial_data_payload
    provider = BrapiProvider(fake_client)

    await provider.get_financial_data(["WEGE3"], mode="current")

    fake_client.fetch.assert_awaited_once_with(
        "financial-data",
        ["WEGE3"],
        params={
            "period": None,
            "mode": "current",
            "startDate": None,
            "endDate": None,
        },
    )