from __future__ import annotations

import logging
from typing import Any

from ingestion.catalog.database import Database

logger = logging.getLogger(__name__)


class StockTypeRepository:
    def __init__(self, db: Database) -> None:
        self._db = db
        self._cache: dict[tuple[str, str], int] = {}

    def get_or_create(self, type_name: str, sub_type_name: str) -> int:
        key = (type_name, sub_type_name)
        if key in self._cache:
            return self._cache[key]

        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO stock_types (type_name, sub_type_name)
                VALUES (%s, %s) ON CONFLICT (type_name, sub_type_name) DO NOTHING
                RETURNING id_type
                """,
                key,
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "SELECT id_type FROM stock_types "
                    "WHERE type_name = %s AND sub_type_name = %s",
                    key,
                )
                row = cur.fetchone()

        self._cache[key] = row[0]
        return row[0]


class MarketRepository:
    def __init__(self, db: Database) -> None:
        self._db = db
        self._cache: dict[str, int] = {}

    def get_or_create(self, market_name: str, currency: str | None = None) -> int:
        if market_name in self._cache:
            return self._cache[market_name]

        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO markets (market_name, currency)
                VALUES (%s, %s) ON CONFLICT (market_name) DO NOTHING
                RETURNING id_market
                """,
                (market_name, currency),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "SELECT id_market FROM markets WHERE market_name = %s", (market_name,)
                )
                row = cur.fetchone()

        self._cache[market_name] = row[0]
        return row[0]


class StockRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def upsert(self, ticker: dict[str, Any], id_market: int, id_type: int) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO stocks
                (stock_code, stock_name, sector, subsector,
                 logo_url, is_active, id_market, id_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (stock_code) DO
                UPDATE SET
                    stock_name = EXCLUDED.stock_name,
                    sector = EXCLUDED.sector,
                    subsector = EXCLUDED.subsector,
                    logo_url = EXCLUDED.logo_url,
                    is_active = EXCLUDED.is_active,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    ticker["symbol"],
                    ticker.get("longName") or ticker["name"],
                    ticker.get("sector"),
                    ticker.get("subsector"),
                    ticker.get("logoUrl"),
                    ticker.get("isActive", True),
                    id_market,
                    id_type,
                ),
            )
