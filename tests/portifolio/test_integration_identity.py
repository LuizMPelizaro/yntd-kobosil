"""Integration coverage; uses only a disposable database created by the runner."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest

from ingestion.catalog.database import Database
from ingestion.portfolio.insert_transactions import process_payload
from ingestion.portfolio.repositories import IdempotencyConflict


def test_atomic_idempotency_and_concurrency(integration_database_config):
    payload = {
        "email": "integration@example.com", "first_name": "Integration",
        "transactions": [
            dict(source="test", operation_id="one", symbol="PETR4",
                 type="BUY", quantity=100, price="36.65", date="2026-07-15"),
            dict(source="test", operation_id="two", symbol="LREN3",
                 type="BUY", quantity=50, price="12.39", date="2026-07-20"),
        ]}
    for tx in payload["transactions"]:
        tx["source"] = "test"

    def submit(p):
        with Database(integration_database_config) as db:
            return process_payload(p, db)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(submit, [payload] * 4))
    assert sum(r["inserted"] for r in results) == 2
    assert sum(r["existing"] for r in results) == 6
    changed = deepcopy(payload)
    changed["transactions"][0]["price"] = 99
    with pytest.raises(IdempotencyConflict):
        submit(changed)
    rollback = deepcopy(payload)
    rollback["transactions"][0]["operation_id"] = "aaa-new"
    rollback["transactions"][1]["price"] = 99
    with pytest.raises(IdempotencyConflict):
        submit(rollback)
    with Database(integration_database_config) as db, db.cursor() as cur:
        cur.execute("SELECT count(*) FROM stock_transactions")
        assert cur.fetchone()[0] == 2
        cur.execute("SELECT count(*) FROM users")
        assert cur.fetchone()[0] == 1
    assert submit(payload) == {"inserted": 0, "existing": 2}
