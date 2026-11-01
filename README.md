# yntd-kobosil

Pipeline de dados para análise de carteiras.

## Preparação

Instale Docker, Python 3.11+ e Poetry. Copie .env.example para .env e configure
Postgres e Brapi. Configure também os secrets do conector em docker/connectors
e o .env do microserviço conforme seu README.

    poetry install --no-root
    make up
    make register-connector
    make connector-status

## Uso

    poetry run python -m ingestion.catalog.sync_tickers
    poetry run python -m ingestion.catalog.sync_tickers --from-cache
    poetry run python -m ingestion.portfolio.insert_transactions ingestion/portfolio/example_payload.json
    poetry run python -m ingestion.portfolio.manage_transactions list --user-id 1
    poetry run python -m ingestion.portfolio.manage_transactions update --user-id 1 --id 12 --quantity 50
    poetry run python -m ingestion.portfolio.manage_transactions delete --user-id 1 --id 12

Edição e exclusão exigem confirmação interativa. Use identificadores da listagem.
Para novas operações, use source=manual e UUID estável em operation_id.

## Testes

Configure APP_ENV=dev ou test no .env e execute poetry run pytest.
Os testes de integração usam bancos temporários; o usuário precisa de CREATEDB.
Fora desses ambientes são ignorados.

## Documentação

- [Arquitetura](docs/architecture/visao-geral.md)
- [Ingestão e migração](docs/portfolio/ingestao.md)
- [Manutenção de operações](docs/portfolio/manutencao-operacoes.md)
- [Microserviço de mercado](services/market_data/README.md)

- [Resiliência do microserviço](docs/architecture/market-data-resilience.md)

## Executar o microserviço

- Docker: `make market-data-rebuild` reconstrói e inicia o serviço.
- Python local: `make market-data` instala as dependências do projeto
  services/market_data e executa o Uvicorn com reload na porta 8001.
- Apenas instalar as dependências locais: `make market-data-install`.

Use uma das formas por vez para evitar conflito de porta. A documentação HTTP
fica em http://127.0.0.1:8001/docs.
