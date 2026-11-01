from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extensions import cursor as PgCursor
from psycopg2.pool import SimpleConnectionPool

from ingestion.catalog.config import DATABASE_CONFIG, DatabaseConfig

logger = logging.getLogger(__name__)


class Database:
    """
    Manages a connection pool to Postgres.

    Usage:
        with Database() as _db, _db.cursor() as cur:
            cur.execute("SELECT 1")
    """

    def __init__(self, config: DatabaseConfig = DATABASE_CONFIG) -> None:
        self._config = config
        self._pool = SimpleConnectionPool(
            minconn=config.min_connections,
            maxconn=config.max_connections,
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            dbname=config.database,
        )
        logger.info(
            "Connection pool created for %s:%s/%s", config.host, config.port, config.database
        )

    def _get_healthy_connection(self, max_attempts: int = 3) -> PgConnection:
        """
        Pulls a connection from the pool and validates it with SELECT 1
        before returning it. If it comes back dead, discard it and try
        another instead of handing a broken connection to the caller.
        """
        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            conn = self._pool.getconn()
            try:
                with conn.cursor() as probe:
                    probe.execute("SELECT 1")
                return conn
            except (psycopg2.InterfaceError, psycopg2.OperationalError) as exc:
                last_error = exc
                logger.warning(
                    "Invalid connection (attempt %s/%s) — discarding: %s",
                    attempt, max_attempts, exc,
                )
                self._pool.putconn(conn, close=True)
        raise last_error  # type: ignore[misc]

    @contextmanager
    def connection(self) -> Iterator[PgConnection]:
        conn = self._get_healthy_connection()
        discard_connection = False
        try:
            yield conn
            conn.commit()
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            discard_connection = True
            logger.exception("Connection to Postgres was lost during transaction")
            raise
        except Exception:
            conn.rollback()
            logger.exception("Error in transaction — rollback applied")
            raise
        finally:
            self._pool.putconn(conn, close=discard_connection)

    @contextmanager
    def cursor(self) -> Iterator[PgCursor]:
        with self.connection() as conn:
            cur = conn.cursor()
            try:
                yield cur
            finally:
                cur.close()

    @contextmanager
    def transaction(self):
        """Expose a cursor factory bound to one commit/rollback boundary."""
        with self.connection() as conn:
            yield TransactionSession(conn)

    def close(self) -> None:
        self._pool.closeall()
        logger.info("Connection pool closed")

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

class TransactionSession:
    def __init__(self, conn):
        self._conn = conn

    @contextmanager
    def cursor(self):
        with self._conn.cursor() as cursor:
            yield cursor
