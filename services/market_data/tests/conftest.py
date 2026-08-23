from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def fake_client() -> AsyncMock:
    """Stands in for BrapiStocksClient — only `.fetch()` is ever awaited."""
    return AsyncMock()


@pytest.fixture
def quote_payload() -> Dict[str, Any]:
    return {
        "results": [
            {
                "requestedSymbol": "PETR4",
                "symbol": "PETR4",
                "changed": False,
                "data": {
                    "shortName": "PETROBRAS   PN  EX  N2",
                    "longName": "Petróleo Brasileiro S.A. - Petrobras",
                    "currency": "BRL",
                    "regularMarketPrice": 41.18,
                    "regularMarketDayHigh": 41.53,
                    "regularMarketDayLow": 40.82,
                    "regularMarketChange": -0.58,
                    "regularMarketChangePercent": -1.39,
                    "regularMarketTime": "2026-06-14T05:15:42.000Z",
                    "marketCap": None,
                    "regularMarketVolume": 34024700,
                    "regularMarketPreviousClose": 41.76,
                    "regularMarketOpen": 41.18,
                    "fiftyTwoWeekLow": 29.31,
                    "fiftyTwoWeekHigh": 50.69,
                    "logourl": "https://icons.brapi.dev/icons/PETR4.svg",
                },
            }
        ],
        "requestedAt": "2026-06-14T05:03:16.000Z",
        "took": 286,
    }


@pytest.fixture
def historical_payload() -> Dict[str, Any]:
    return {
        "results": [
            {
                "requestedSymbol": "PETR4",
                "symbol": "PETR4",
                "changed": False,
                "data": {
                    "usedInterval": "1d",
                    "usedRange": "1mo",
                    "historicalDataPrice": [
                        {
                            "date": "2026-06-13T00:00:00.000Z",
                            "open": 41.06,
                            "high": 41.53,
                            "low": 40.82,
                            "close": 41.18,
                            "volume": 34081000,
                            "adjustedClose": 41.18,
                        }
                    ],
                },
            }
        ],
        "requestedAt": "2026-06-14T05:03:16.000Z",
        "took": 907,
    }


@pytest.fixture
def dividends_payload() -> Dict[str, Any]:
    return {
        "results": [
            {
                "requestedSymbol": "ITSA4",
                "symbol": "ITSA4",
                "changed": False,
                "data": {
                    "cashDividends": [
                        {
                            "assetIssued": "BRITSAACNPR7",
                            "paymentDate": "2026-10-01T03:00:00.000Z",
                            "rate": 0.024242,
                            "relatedTo": "",
                            "approvedOn": None,
                            "isinCode": "BRITSAACNPR7",
                            "label": "JCP",
                            "lastDatePrior": "2026-08-31T03:00:00.000Z",
                            "remarks": "",
                        }
                    ],
                    "stockDividends": [
                        {
                            "assetIssued": "BRITSAACNPR7",
                            "factor": 1.02,
                            "completeFactor": "1,02 para 1",
                            "approvedOn": "2025-12-15T03:00:00.000Z",
                            "isinCode": "BRITSAACNPR7",
                            "label": "BONIFICACAO",
                            "lastDatePrior": "2025-12-18T03:00:00.000Z",
                            "remarks": "",
                        }
                    ],
                    "subscriptions": [],
                },
            }
        ],
        "requestedAt": "2026-06-14T05:03:16.000Z",
        "took": 203,
    }


@pytest.fixture
def statistics_payload() -> Dict[str, Any]:
    return {
        "results": [
            {
                "requestedSymbol": "WEGE3",
                "symbol": "WEGE3",
                "changed": False,
                "data": {
                    "marketCap": 178847730000,
                    "enterpriseValue": 181192740000,
                    "trailingPE": 28.445553,
                    "forwardPE": None,
                    "priceToBook": 10.078141,
                    "beta": 0.6503127,
                    "dividendYield": 0.03,
                    "earningsPerShare": 1.4979494,
                    "sharesOutstanding": 4197318000,
                    "bookValue": 4.227962,
                    "profitMargins": 0.16715191,
                },
            }
        ],
        "requestedAt": "2026-06-14T05:03:16.000Z",
        "took": 207,
    }


@pytest.fixture
def financial_data_payload() -> Dict[str, Any]:
    return {
        "results": [
            {
                "requestedSymbol": "WEGE3",
                "symbol": "WEGE3",
                "changed": False,
                "data": {
                    "totalRevenue": 40193850000,
                    "totalCash": 7385768000,
                    "totalDebt": 9730790000,
                    "ebitda": 8929845000,
                    "grossProfits": 13361430000,
                    "freeCashflow": 2974247000,
                    "operatingCashflow": 7172939000,
                    "returnOnAssets": 0.15488343,
                    "returnOnEquity": 0.378589,
                    "debtToEquity": 0.54833394,
                    "currentRatio": 1.5479537,
                    "quickRatio": 0.98023725,
                    "grossMargins": 0.3324247,
                    "operatingMargins": 0.19664963,
                    "profitMargins": 0.16715191,
                },
            }
        ],
        "requestedAt": "2026-06-14T05:03:16.000Z",
        "took": 31,
    }