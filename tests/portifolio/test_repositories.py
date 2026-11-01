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
    assert "INSERT INTO users" in fake_cursor.execute.call_args.args[0]


def test_user_get_or_create_inserts_when_not_found(
    fake_db: MagicMock, fake_cursor: MagicMock
) -> None:
    fake_cursor.fetchone.return_value = (11,)

    result = UserRepository(fake_db).get_or_create("new@example.com", "New", "User")

    assert result == 11
    assert fake_cursor.execute.call_count == 1
    insert_sql = fake_cursor.execute.call_args_list[0].args[0]
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


def test_transaction_insert_result(fake_db, fake_cursor):
    from datetime import datetime
    from decimal import Decimal
    fake_cursor.fetchone.return_value = (1,)
    tx = dict(source="manual", operation_id="abc", symbol="PETR4",
              type="BUY", quantity=Decimal("1"), price=Decimal("2"),
              date=datetime(2026, 1, 1))
    assert TransactionRepository(fake_db).insert_many(1, [tx], {"PETR4": 1}) == {
        "inserted": 1, "existing": 0}
