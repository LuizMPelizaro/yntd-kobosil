from __future__ import annotations

import logging
from typing import Any

from ingestion.catalog.database import Database

logger = logging.getLogger(__name__)


class UnknownStockError(Exception):
    """Raised when an unknown stock is requested"""


class UserRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_or_create(self, email: str, first_name: str, last_name: str | None = None) -> int:
        with self._db.cursor() as cursor:
            cursor.execute('SELECT id_user FROM users WHERE email = %s', (email,))
            row = cursor.fetchone()
            if row is not None:
                return row[0]

            cursor.execute(
                """
                INSERT INTO users (first_name, last_name, email)
                VALUES (%s, %s, %s) RETURNING id_user
                """,
                (first_name, last_name, email)
            )
            row = cursor.fetchone()

        logger.info(f"New user created: {email} (id_user={row[0]}")
        return row[0]


class StockLookupRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def resolve_many(self, stock_codes: list[str]) -> dict[str, int]:
        unique_codes = sorted(set(stock_codes))

        with self._db.cursor() as cursor:
            cursor.execute("""
                           SELECT stock_code, id_stock
                           FROM stocks
                           WHERE stock_code = ANY (%s)
                           """,
                           (unique_codes,))
            found_stocks: dict[str, int] = dict(cursor.fetchall())

            missing_stocks = [code for code in unique_codes if code not in found_stocks]

            if missing_stocks:
                raise UnknownStockError(f"Stock code(s) not found in catalog: {missing_stocks}")
            return found_stocks


class TransactionRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert_many(self,
                    id_user: int,
                    transactions: list[dict[str, Any]],
                    stock_id_by_code: dict[str, int]) -> int:
        with self._db.cursor() as cursor:
            for tx in transactions:
                cursor.execute("""
                               INSERT INTO stock_transactions (id_user, id_stock, transaction_type, quantity, price, transaction_date)
                               VALUES (%s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
                               """, (
                                   id_user,
                                   stock_id_by_code[tx["symbol"]],
                                   tx["type"].upper(),
                                   tx["quantity"],
                                   tx["price"],
                                   tx.get("date"),
                               ),
                               )

        logger.info("%s transactions inserted for id_user=%s", len(transactions), id_user)
        return len(transactions)
