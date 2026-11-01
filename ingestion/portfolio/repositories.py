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
class OperationNotFound(ValueError):
    pass


class ConcurrentModification(ValueError):
    pass


class MaintenanceRepository:
    """Snapshot-based maintenance; callers own the transaction boundary."""
    columns = ('id_transaction', 'id_user', 'source', 'operation_id', 'id_stock',
               'type', 'quantity', 'price', 'date', 'created_at', 'version')
    select = '''SELECT id_transaction, id_user, source, operation_id, id_stock,
                transaction_type, quantity, price, transaction_date, created_at,
                xmin::text FROM stock_transactions'''

    def __init__(self, db):
        self.db = db

    def get(self, user_id, transaction_id, lock=False):
        with self.db.cursor() as cur:
            cur.execute(self.select + ' WHERE id_user=%s AND id_transaction=%s' +
                        (' FOR UPDATE' if lock else ''), (user_id, transaction_id))
            row = cur.fetchone()
        if row is None:
            raise OperationNotFound('Operation not found for this user')
        return dict(zip(self.columns, row))

    def list(self, user_id, limit=50, offset=0):
        if not 1 <= limit <= 200 or offset < 0:
            raise ValueError('limit must be 1..200 and offset nonnegative')
        with self.db.cursor() as cur:
            cur.execute(self.select + ' WHERE id_user=%s ORDER BY id_transaction LIMIT %s OFFSET %s',
                        (user_id, limit, offset))
            return [dict(zip(self.columns, row)) for row in cur.fetchall()]

    def apply(self, expected, values=None):
        current = self.get(expected['id_user'], expected['id_transaction'], lock=True)
        if current != expected:
            raise ConcurrentModification('Operation changed; consult it again before confirming')
        with self.db.cursor() as cur:
            key = (expected['id_user'], expected['id_transaction'])
            if values is None:
                cur.execute('DELETE FROM stock_transactions WHERE id_user=%s AND id_transaction=%s', key)
            else:
                cur.execute('''UPDATE stock_transactions SET id_stock=%s, transaction_type=%s,
                               quantity=%s, price=%s, transaction_date=%s
                               WHERE id_user=%s AND id_transaction=%s''',
                            (values['id_stock'], values['type'], values['quantity'],
                             values['price'], values['date']) + key)
