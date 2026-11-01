from __future__ import annotations

from unittest.mock import MagicMock

from ingestion.catalog.repositories import MarketRepository, StockRepository, StockTypeRepository


def test_stock_type_insert_path_returns_new_id(fake_db: MagicMock, fake_cursor: MagicMock) -> None:
    fake_cursor.fetchone.return_value = (1,)

    result = StockTypeRepository(fake_db).get_or_create("stock", "stock")

    assert result == 1
    fake_cursor.execute.assert_called_once()
    assert "INSERT INTO stock_types" in fake_cursor.execute.call_args.args[0]


def test_stock_type_falls_back_to_select_on_conflict(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    # First call (INSERT ... RETURNING) finds a conflict and returns nothing;
    # the repository must then SELECT the existing row.
    fake_cursor.fetchone.side_effect = [None, (7,)]

    result = StockTypeRepository(fake_db).get_or_create("fund", "fii")

    assert result == 7
    assert fake_cursor.execute.call_count == 2


def test_stock_type_uses_in_memory_cache_on_repeat_call(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    fake_cursor.fetchone.return_value = (1,)
    repo = StockTypeRepository(fake_db)

    repo.get_or_create("stock", "stock")
    repo.get_or_create("stock", "stock")

    fake_cursor.execute.assert_called_once()


def test_market_insert_path_returns_new_id(fake_db: MagicMock, fake_cursor: MagicMock) -> None:
    fake_cursor.fetchone.return_value = (3,)

    result = MarketRepository(fake_db).get_or_create("B3", "BRL")

    assert result == 3


def test_market_uses_in_memory_cache_on_repeat_call(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    fake_cursor.fetchone.return_value = (3,)
    repo = MarketRepository(fake_db)

    repo.get_or_create("B3", "BRL")
    repo.get_or_create("B3", "BRL")

    fake_cursor.execute.assert_called_once()


def test_stock_upsert_sends_expected_params(fake_db: MagicMock, fake_cursor: MagicMock) -> None:
    ticker = {
        "symbol": "PETR4",
        "longName": "Petroleo Brasileiro S.A.",
        "sector": "Energy Minerals",
        "subsector": "Petroleo, Gas e Biocombustiveis",
        "logoUrl": "https://icons.brapi.dev/icons/PETR4.svg",
        "isActive": True,
    }

    StockRepository(fake_db).upsert(ticker, id_market=1, id_type=2)

    fake_cursor.execute.assert_called_once()
    sql, params = fake_cursor.execute.call_args.args
    assert "INSERT INTO stocks" in sql
    assert params[0] == "PETR4"
    assert params[-2:] == (1, 2)


def test_stock_upsert_falls_back_to_name_when_long_name_missing(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    ticker = {"symbol": "XPTO3", "name": "Xpto SA", "isActive": True}

    StockRepository(fake_db).upsert(ticker, id_market=1, id_type=1)

    _, params = fake_cursor.execute.call_args.args
    assert params[1] == "Xpto SA"