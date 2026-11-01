"""
Syncs the asset catalog (stock_types, markets, stocks) from the
/api/v2/tickers endpoint on brapi.dev.

Usage:
    python -m ingestion.catalog.sync_tickers
    python -m ingestion.catalog.sync_tickers --from-cache
    python -m ingestion.catalog.sync_tickers --from-cache --cache-file data/raw/tickers/tickers_20260809T010000Z.json
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ingestion.catalog.config import BRAPI_CONFIG
from ingestion.catalog.database import Database
from ingestion.catalog.http_client import BrapiHttpClient
from ingestion.catalog.repositories import MarketRepository, StockRepository, StockTypeRepository
from ingestion.catalog.tickers_client import TickersClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

_RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "tickers"


def save_raw_json(tickers: list[dict[str, Any]]) -> Path:
    """Persists the raw API response to disk before any transformation."""
    _RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = _RAW_DATA_DIR / f"tickers_{timestamp}.json"
    output_path.write_text(
        json.dumps(tickers, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Raw JSON saved to %s (%s tickers)", output_path, len(tickers))
    return output_path


def load_cached_tickers(explicit_path: Path | None = None) -> list[dict[str, Any]]:
    """
    Loads tickers from a previously saved JSON file instead of calling the API.

    If `explicit_path` is provided, loads that exact file. Otherwise, picks
    the most recently modified file under data/raw/tickers/.
    """
    if explicit_path is not None:
        target = explicit_path
    else:
        candidates = sorted(
            _RAW_DATA_DIR.glob("tickers_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise FileNotFoundError(
                f"No cached ticker file found in {_RAW_DATA_DIR}. "
                "Run once without --from-cache first to create one."
            )
        target = candidates[0]

    if not target.exists():
        raise FileNotFoundError(f"Cache file not found: {target}")

    logger.info("Loading cached tickers from %s", target)
    tickers: list[dict[str, Any]] = json.loads(target.read_text(encoding="utf-8"))
    logger.info("Loaded %s tickers from cache", len(tickers))
    return tickers


def fetch_tickers_from_api() -> list[dict[str, Any]]:
    """Fetches the full, paginated ticker list from the brapi.dev API."""
    with BrapiHttpClient(BRAPI_CONFIG) as http_client:
        tickers = TickersClient(http_client).fetch_all()
    save_raw_json(tickers)
    return tickers


def populate_catalog(tickers: list[dict[str, Any]], db: Database) -> None:
    """Populates stock_types, markets and stocks from the ticker list."""
    stock_type_repo = StockTypeRepository(db)
    market_repo = MarketRepository(db)
    stock_repo = StockRepository(db)

    for ticker in tickers:
        id_type = stock_type_repo.get_or_create(ticker["assetType"], ticker["subType"])
        id_market = market_repo.get_or_create(ticker["exchange"], ticker.get("currency"))
        stock_repo.upsert(ticker, id_market=id_market, id_type=id_type)

    logger.info("Catalog populated: %s assets processed", len(tickers))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync the asset catalog from brapi.dev into the OLTP database."
    )
    parser.add_argument(
        "--from-cache",
        action="store_true",
        default=False,
        help="Skip the API call and reuse a previously saved JSON file instead.",
    )
    parser.add_argument(
        "--cache-file",
        type=Path,
        default=None,
        help="Specific cached JSON file to use with --from-cache "
        "(defaults to the most recently saved one).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    tickers = (
        load_cached_tickers(explicit_path=args.cache_file)
        if args.from_cache
        else fetch_tickers_from_api()
    )

    with Database() as db:
        populate_catalog(tickers, db)


if __name__ == "__main__":
    main()