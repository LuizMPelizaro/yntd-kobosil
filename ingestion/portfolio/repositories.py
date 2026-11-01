from __future__ import annotations

import logging

from ingestion.catalog.database import Database

logger = logging.getLogger(__name__)


class UnknownStockError(Exception):
    """Raised when an unknown stock is requested"""


class UserRepository:
    def __init__(self, db):
        self._db = db

    def get_or_create(self, email, first_name, last_name=None):
        with self._db.cursor() as cursor:
            cursor.execute(
                """INSERT INTO users (first_name, last_name, email)
                   VALUES (%s, %s, %s) ON CONFLICT (email) DO NOTHING
                   RETURNING id_user""", (first_name, last_name, email))
            row = cursor.fetchone()
            if row is None:
                cursor.execute("SELECT id_user FROM users WHERE email = %s", (email,))
                row = cursor.fetchone()
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


class IdempotencyConflict(ValueError):
    """An operation identifier was reused with different business data."""


class TransactionRepository:
    def __init__(self, db):
        self._db = db

    def insert_many(self, id_user, transactions, stock_id_by_code):
        inserted = existing = 0
        with self._db.cursor() as cursor:
            # Stable lock acquisition order across overlapping concurrent batches.
            for tx in sorted(transactions, key=lambda t: (t["source"], t["operation_id"])):
                values = (stock_id_by_code[tx["symbol"]], tx["type"],
                          tx["quantity"], tx["price"], tx["date"])
                key = (id_user, tx["source"], tx["operation_id"])
                cursor.execute(
                    """INSERT INTO stock_transactions
                       (id_user, source, operation_id, id_stock, transaction_type,
                        quantity, price, transaction_date)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (id_user, source, operation_id) DO NOTHING
                       RETURNING id_transaction""", key + values)
                if cursor.fetchone() is not None:
                    inserted += 1
                    continue
                cursor.execute(
                    """SELECT id_stock, transaction_type, quantity, price, transaction_date
                       FROM stock_transactions
                       WHERE id_user=%s AND source=%s AND operation_id=%s
                       FOR SHARE""", key)
                if tuple(cursor.fetchone()) != values:
                    raise IdempotencyConflict(
                        f"Operation {tx['source']}/{tx['operation_id']} has different data")
                existing += 1
        return {"inserted": inserted, "existing": existing}
