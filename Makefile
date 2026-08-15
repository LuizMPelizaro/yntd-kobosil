up:
	docker compose --env-file .env -f docker/docker-compose.yml up -d

down:
	docker compose -f docker/docker-compose.yml down

reset:
	docker compose --env-file .env -f docker/docker-compose.yml down -v
	docker compose --env-file .env -f docker/docker-compose.yml up -d --force-recreate

register-connector:
	curl -X POST -H "Content-Type: application/json" --data @docker/connectors/connector-postgres.json http://localhost:8083/connectors

delete-connector:
	curl -X DELETE http://localhost:8083/connectors/oltp-postgres-connector

reconnect: delete-connector register-connector

connector-status:
	curl http://localhost:8083/connectors/oltp-postgres-connector/status

install:
	poetry install --no-root

logs:
	docker compose -f docker/docker-compose.yml logs -f

populate_markets_stocks_and_types:
	poetry python -m ingestion.catalog.sync_tickers

populate_markets_stocks_and_types_using_cache:
	poetry python -m ingestion.catalog.sync_tickers --from-cache

insert_stock_transactions:
	poetry python -m ingestion.portfolio.insert_transactions ingestion/portfolio/example_payload.json

test:
	poetry run pytest -v