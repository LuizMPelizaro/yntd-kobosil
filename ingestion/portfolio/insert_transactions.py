from __future__ import annotations

import argparse
import json
import logging
from ingestion.portfolio.validation import validate_transactions
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

