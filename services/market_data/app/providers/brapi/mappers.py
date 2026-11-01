from __future__ import annotations

from typing import Any, Dict, List

from app.core.contracts import (
    CashDividend,
    Dividends,
    FinancialData,
    HistoricalCandle,
    HistoricalSeries,
    MarketDataResult,
    Quote,
    Statistics,
    StockDividend,
)


def _results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return payload.get("results", [])


def _envelope(item: Dict[str, Any], data: Any) -> Dict[str, Any]:
    return {
        "requested_symbol": item["requestedSymbol"],
        "symbol": item["symbol"],
        "changed": item["changed"],
        "data": data,
    }


def to_quote_results(payload: Dict[str, Any]) -> List[MarketDataResult[Quote]]:
    out = []
    for item in _results(payload):
        d = item["data"]
        quote = Quote(
            short_name=d.get("shortName"),
            long_name=d.get("longName"),
            currency=d.get("currency"),
            regular_market_price=d.get("regularMarketPrice"),
            regular_market_day_high=d.get("regularMarketDayHigh"),
            regular_market_day_low=d.get("regularMarketDayLow"),
            regular_market_change=d.get("regularMarketChange"),
            regular_market_change_percent=d.get("regularMarketChangePercent"),
            regular_market_time=d.get("regularMarketTime"),
            regular_market_volume=d.get("regularMarketVolume"),
            regular_market_previous_close=d.get("regularMarketPreviousClose"),
            regular_market_open=d.get("regularMarketOpen"),
            fifty_two_week_low=d.get("fiftyTwoWeekLow"),
            fifty_two_week_high=d.get("fiftyTwoWeekHigh"),
            market_cap=d.get("marketCap"),
            logo_url=d.get("logourl"),
        )
        out.append(MarketDataResult[Quote](**_envelope(item, quote)))
    return out


def to_historical_results(payload: Dict[str, Any]) -> List[MarketDataResult[HistoricalSeries]]:
    out = []
    for item in _results(payload):
        d = item["data"]
        candles = [
            HistoricalCandle(
                date=point["date"],
                open=point.get("open"),
                high=point.get("high"),
                low=point.get("low"),
                close=point.get("close"),
                volume=point.get("volume"),
                adjusted_close=point.get("adjustedClose"),
            )
            for point in d.get("historicalDataPrice", [])
        ]
        series = HistoricalSeries(
            used_interval=d.get("usedInterval"),
            used_range=d.get("usedRange"),
            candles=candles,
        )
        out.append(MarketDataResult[HistoricalSeries](**_envelope(item, series)))
    return out


def to_dividends_results(payload: Dict[str, Any]) -> List[MarketDataResult[Dividends]]:
    out = []
    for item in _results(payload):
        d = item["data"]
        cash = [
            CashDividend(
                payment_date=c.get("paymentDate"),
                last_date_prior=c.get("lastDatePrior"),
                approved_on=c.get("approvedOn"),
                rate=c.get("rate"),
                label=c.get("label"),
                related_to=c.get("relatedTo"),
                isin_code=c.get("isinCode"),
            )
            for c in d.get("cashDividends", [])
        ]
        stock = [
            StockDividend(
                factor=s.get("factor"),
                complete_factor=s.get("completeFactor"),
                approved_on=s.get("approvedOn"),
                label=s.get("label"),
                isin_code=s.get("isinCode"),
            )
            for s in d.get("stockDividends", [])
        ]
        dividends = Dividends(cash_dividends=cash, stock_dividends=stock)
        out.append(MarketDataResult[Dividends](**_envelope(item, dividends)))
    return out


def _statistics_fields(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "market_cap": d.get("marketCap"),
        "enterprise_value": d.get("enterpriseValue"),
        "trailing_pe": d.get("trailingPE"),
        "forward_pe": d.get("forwardPE"),
        "price_to_book": d.get("priceToBook"),
        "beta": d.get("beta"),
        "dividend_yield": d.get("dividendYield"),
        "earnings_per_share": d.get("earningsPerShare"),
        "shares_outstanding": d.get("sharesOutstanding"),
        "book_value": d.get("bookValue"),
        "profit_margins": d.get("profitMargins"),
    }


def to_statistics_results(payload: Dict[str, Any]) -> List[MarketDataResult[Statistics]]:
    out = []
    for item in _results(payload):
        stats = Statistics(**_statistics_fields(item["data"]))
        out.append(MarketDataResult[Statistics](**_envelope(item, stats)))
    return out


def _financial_data_fields(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "total_revenue": d.get("totalRevenue"),
        "total_cash": d.get("totalCash"),
        "total_debt": d.get("totalDebt"),
        "ebitda": d.get("ebitda"),
        "gross_profits": d.get("grossProfits"),
        "free_cashflow": d.get("freeCashflow"),
        "operating_cashflow": d.get("operatingCashflow"),
        "return_on_assets": d.get("returnOnAssets"),
        "return_on_equity": d.get("returnOnEquity"),
        "debt_to_equity": d.get("debtToEquity"),
        "current_ratio": d.get("currentRatio"),
        "quick_ratio": d.get("quickRatio"),
        "gross_margins": d.get("grossMargins"),
        "operating_margins": d.get("operatingMargins"),
        "profit_margins": d.get("profitMargins"),
    }


def to_financial_data_results(payload: Dict[str, Any]) -> List[MarketDataResult[FinancialData]]:
    out = []
    for item in _results(payload):
        financial = FinancialData(**_financial_data_fields(item["data"]))
        out.append(MarketDataResult[FinancialData](**_envelope(item, financial)))
    return out