from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ingestion.catalog.database import Database
from ingestion.portfolio.repositories import StockLookupRepository, TransactionRepository, UserRepository

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)


def validate_transactions(payload):
    transactions = []
    for original in payload["transactions"]:
        tx = dict(original)
        for name in ("source", "operation_id"):
            value = tx.get(name)
            if not isinstance(value, str) or not value.strip() or len(value) > 128:
                raise ValueError(f"{name} must be a nonempty string of at most 128 characters")
            if value != value.strip():
                raise ValueError(f"{name} must not contain surrounding whitespace")
        tx["symbol"] = tx["symbol"].strip().upper()
        tx["type"] = tx["type"].upper()
        if tx["type"] not in ("BUY", "SELL"):
            raise ValueError("type must be BUY or SELL")
        for name, scale in (("quantity", 6), ("price", 4)):
            value = Decimal(str(tx[name]))
            if (not value.is_finite() or value <= 0 or
                    value >= Decimal(10) ** (18 - scale) or
                    value != value.quantize(Decimal(10) ** -scale)):
                raise ValueError(f"Invalid {name} or precision")
            tx[name] = value
        tx["date"] = datetime.fromisoformat(tx["date"])
        if tx["date"].tzinfo is not None:
            raise ValueError("Use a timezone-free trade date until timezone migration")
        transactions.append(tx)
    return transactions


def process_payload(payload: dict[str, Any], db: Database) -> dict[str, int]:
    transactions = validate_transactions(payload)
    with db.transaction() as session:
        id_user = UserRepository(session).get_or_create(
            email=payload["email"], first_name=payload["first_name"],
            last_name=payload.get("last_name"))
        stocks = StockLookupRepository(session).resolve_many(
            [tx["symbol"] for tx in transactions])
        result = TransactionRepository(session).insert_many(id_user, transactions, stocks)
    return result

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a user's portfolio transactions from a JSON file."
    )
    parser.add_argument("payload", type=Path, help="Path to the JSON payload file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_payload(args.payload)

    with Database() as db:
        count = process_payload(payload, db)

    logger.info("Committed: %s", count)


if __name__ == "__main__":
    main()

