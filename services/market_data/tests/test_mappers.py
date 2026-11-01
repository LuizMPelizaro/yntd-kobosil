from __future__ import annotations

from app.providers.brapi import mappers


def test_to_quote_results_maps_envelope_and_fields(quote_payload):
    results = mappers.to_quote_results(quote_payload)

    assert len(results) == 1
    result = results[0]
    assert result.requested_symbol == "PETR4"
    assert result.symbol == "PETR4"
    assert result.changed is False
    assert result.data.regular_market_price == 41.18
    assert result.data.long_name == "Petróleo Brasileiro S.A. - Petrobras"
    assert result.data.logo_url == "https://icons.brapi.dev/icons/PETR4.svg"


def test_to_historical_results_maps_candles(historical_payload):
    results = mappers.to_historical_results(historical_payload)

    series = results[0].data
    assert series.used_interval == "1d"
    assert series.used_range == "1mo"
    assert len(series.candles) == 1
    candle = series.candles[0]
    assert candle.close == 41.18
    assert candle.volume == 34081000


def test_to_dividends_results_maps_cash_and_stock_events(dividends_payload):
    results = mappers.to_dividends_results(dividends_payload)

    dividends = results[0].data
    assert len(dividends.cash_dividends) == 1
    assert dividends.cash_dividends[0].label == "JCP"
    assert dividends.cash_dividends[0].rate == 0.024242
    assert len(dividends.stock_dividends) == 1
    assert dividends.stock_dividends[0].factor == 1.02


def test_to_statistics_results_maps_known_fields(statistics_payload):
    results = mappers.to_statistics_results(statistics_payload)

    stats = results[0].data
    assert stats.trailing_pe == 28.445553
    assert stats.dividend_yield == 0.03
    assert stats.forward_pe is None


def test_to_financial_data_results_maps_known_fields(financial_data_payload):
    results = mappers.to_financial_data_results(financial_data_payload)

    financial = results[0].data
    assert financial.total_revenue == 40193850000
    assert financial.return_on_equity == 0.378589


def test_mappers_handle_empty_results():
    empty_payload = {"results": [], "requestedAt": "2026-06-14T05:03:16.000Z", "took": 1}

    assert mappers.to_quote_results(empty_payload) == []
    assert mappers.to_historical_results(empty_payload) == []
    assert mappers.to_dividends_results(empty_payload) == []
    assert mappers.to_statistics_results(empty_payload) == []
    assert mappers.to_financial_data_results(empty_payload) == []