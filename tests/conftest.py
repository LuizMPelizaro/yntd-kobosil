from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fake_cursor() -> MagicMock:
    return MagicMock()


@pytest.fixture
def fake_db(fake_cursor: MagicMock) -> MagicMock:
    db = MagicMock()
    db.cursor.return_value.__enter__.return_value = fake_cursor
    db.cursor.return_value.__exit__.return_value = False
    return db
@pytest.fixture
def integration_database_config():
    """Run against a fresh database on the configured development server."""
    import os
    from dataclasses import replace
    from pathlib import Path
    from uuid import uuid4
    import psycopg2
    from psycopg2 import sql
    from ingestion.catalog.config import DATABASE_CONFIG

    if os.getenv("APP_ENV", "").strip().lower() not in {"dev", "test"}:
        pytest.skip("Database integration requires APP_ENV=dev or test")
    config = DATABASE_CONFIG
    admin = psycopg2.connect(
        host=config.host, port=config.port, user=config.username,
        password=config.password, dbname=config.database, connect_timeout=10)
    admin.autocommit = True
    name = "yntd_test_" + uuid4().hex
    created = False
    try:
        with admin.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        created = True
        conn = psycopg2.connect(
            host=config.host, port=config.port, user=config.username,
            password=config.password, dbname=name)
        try:
            with conn, conn.cursor() as cur:
                schema = Path(__file__).resolve().parents[1] / "docker/init/oltp_schema.sql"
                cur.execute(schema.read_text(encoding="utf-8"))
                cur.execute("INSERT INTO markets(market_name) VALUES ('TEST')")
                cur.execute("INSERT INTO stock_types(type_name,sub_type_name) VALUES ('stock','test')")
                cur.execute("INSERT INTO stocks(stock_code,stock_name,id_market,id_type) VALUES ('PETR4','test',1,1),('LREN3','test',1,1)")
        finally:
            conn.close()
        yield replace(config, database=name)
    finally:
        try:
            if created:
                with admin.cursor() as cur:
                    cur.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
        finally:
            admin.close()
