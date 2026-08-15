from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ingestion.portfolio.repositories import (
    StockLookupRepository,
    TransactionRepository,
    UnknownStockError,
    UserRepository,
)


def test_user_get_or_create_returns_existing_user(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    fake_cursor.fetchone.return_value = (10,)

    result = UserRepository(fake_db).get_or_create("delta@example.com", "Delta")

    assert result == 10
    fake_cursor.execute.assert_called_once()
    assert "SELECT id_user" in fake_cursor.execute.call_args.args[0]


def test_user_get_or_create_inserts_when_not_found(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    fake_cursor.fetchone.side_effect = [None, (11,)]

    result = UserRepository(fake_db).get_or_create("new@example.com", "New", "User")

    assert result == 11
    assert fake_cursor.execute.call_count == 2
    insert_sql = fake_cursor.execute.call_args_list[1].args[0]
    assert "INSERT INTO users" in insert_sql


def test_stock_lookup_resolves_all_known_symbols(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    fake_cursor.fetchall.return_value = [("PETR4", 1), ("LREN3", 2)]

    result = StockLookupRepository(fake_db).resolve_many(["PETR4", "LREN3"])

    assert result == {"PETR4": 1, "LREN3": 2}


def test_stock_lookup_raises_unknown_stock_error_listing_missing_symbols(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    fake_cursor.fetchall.return_value = [("PETR4", 1)]

    with pytest.raises(UnknownStockError) as exc_info:
        StockLookupRepository(fake_db).resolve_many(["PETR4", "UNKNOWN9"])

    assert "UNKNOWN9" in str(exc_info.value)
    assert "PETR4" not in str(exc_info.value)


def test_transaction_insert_many_inserts_one_row_per_transaction(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    transactions = [
        {"symbol": "PETR4", "type": "buy", "quantity": 10, "price": 36.5, "date": "2026-08-01"},
        {"symbol": "LREN3", "type": "sell", "quantity": 5, "price": 12.0, "date": None},
    ]
    stock_id_by_code = {"PETR4": 1, "LREN3": 2}

    count = TransactionRepository(fake_db).insert_many(
        id_user=1, transactions=transactions, stock_id_by_code=stock_id_by_code
    )

    assert count == 2
    assert fake_cursor.execute.call_count == 2


def test_transaction_insert_many_uppercases_transaction_type(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    transactions = [{"symbol": "PETR4", "type": "buy", "quantity": 1, "price": 1.0, "date": None}]

    TransactionRepository(fake_db).insert_many(
        id_user=1, transactions=transactions, stock_id_by_code={"PETR4": 1}
    )

    _, params = fake_cursor.execute.call_args.args
    assert params[2] == "BUY"