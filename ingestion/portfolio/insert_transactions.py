from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from ingestion.catalog.database import Database
from ingestion.portfolio.repositories import StockLookupRepository, TransactionRepository, UserRepository

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def process_payload(payload: dict[str, Any], db: Database) -> int:
    user_repo = UserRepository(db)
    stock_repo = StockLookupRepository(db)
    tx_repo = TransactionRepository(db)

    id_user = user_repo.get_or_create(
        email=payload["email"],
        first_name=payload["first_name"],
        last_name=payload.get("last_name"),
    )

    transactions = payload["transactions"]
    symbols = [tx["symbol"] for tx in transactions]
    stock_id_by_code = stock_repo.resolve_many(symbols)

    return tx_repo.insert_many(id_user, transactions, stock_id_by_code)


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

    logger.info("Done: %s transactions inserted for %s", count, payload["email"])


if __name__ == "__main__":
    main()
