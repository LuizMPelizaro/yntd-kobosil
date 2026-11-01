# market-data-service

Provider-agnostic market data microservice. Exposes quote, historical
prices, dividends, statistics and financial data over HTTP, backed
today by brapi.dev (B3). Consumed by the Spark/Scala Bronze layer and,
later, orchestrated by Airflow. Holds no state of its own — every
request is a live pass-through to the upstream provider.

## Why this shape

Every route only depends on the `MarketDataProvider` interface
(`app/core/provider.py`), never on brapi.dev directly. Adding a second
data source later (a US-market API, for example) means:

1. Create `app/providers/<new_provider>/` implementing
   `MarketDataProvider`, mapping its raw responses into the same
   contracts in `app/core/contracts.py`.
2. Point `app/dependencies.get_provider` at it (or stand up a sibling
   service, e.g. `services/market_data_us/`, that reuses the same
   `app/core` module).

Routers, contracts, and every consumer of this API stay unchanged.

## Running locally

```
poetry install --no-root
cp .env.example .env   # fill in BRAPI_TOKEN
poetry run uvicorn app.main:app --reload --port 8001
```

Interactive docs: http://localhost:8001/docs

## Endpoints

| Endpoint | Brapi resource | Notes |
|---|---|---|
| `GET /v1/quote?symbols=PETR4,VALE3` | `/v2/stocks/quote` | Current price snapshot |
| `GET /v1/historical?symbols=PETR4&range=1mo&interval=1d` | `/v2/stocks/historical` | OHLCV series |
| `GET /v1/dividends?symbols=PETR4` | `/v2/stocks/dividends` | Cash and stock dividend events |
| `GET /v1/statistics?symbols=PETR4&mode=current` | `/v2/stocks/statistics` | Valuation and share statistics |
| `GET /v1/financial-data?symbols=PETR4&mode=current` | `/v2/stocks/financial-data` | Revenue, cash flow, margins |
| `GET /health` | — | Liveness check |

`symbols` accepts multiple comma-separated tickers on every endpoint —
one request can cover a user's whole portfolio.

Every response wraps its payload in the same envelope:

```json
{
  "requested_symbol": "PETR4",
  "symbol": "PETR4",
  "changed": false,
  "data": { ... }
}
```

`changed` is true when brapi.dev resolved an old/renamed ticker to its
current one — worth checking downstream before assuming the requested
symbol is what actually got matched.
Reliability settings and error behavior: [resilience guide](../../docs/architecture/market-data-resilience.md).

From the repository root, `make market-data` installs this service's own Poetry
dependencies and starts the local server on port 8001. Use
`make market-data-rebuild` for Docker instead. Stop the Docker service before
starting locally on the same port.
