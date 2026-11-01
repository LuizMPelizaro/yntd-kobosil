# Market Data Service

Microserviço HTTP de dados de mercado, atualmente integrado à Brapi. As respostas
são normalizadas; não são cópias integrais da API de origem. O serviço não grava
dados nem agenda coletas: essas responsabilidades ficam no pipeline e no futuro Airflow.

## Inicialização

Na raiz do repositório, configure services/market_data/.env a partir de
[.env.example](.env.example) e preencha BRAPI_TOKEN conforme seu acesso.

    make market-data-rebuild

Para executar em Python local, com Poetry instalado:

    make market-data

Esse alvo instala as dependências próprias do serviço e inicia com reload na
porta 8001. Use somente uma execução por porta.

- [Swagger UI](http://127.0.0.1:8001/docs)
- [ReDoc](http://127.0.0.1:8001/redoc)
- [OpenAPI JSON](http://127.0.0.1:8001/openapi.json)

## Documentação

- [Endpoints, parâmetros e respostas](docs/api.md)
- [Importação e uso no Postman](postman/README.md)
- [Configuração, limites, retentativas e segurança](docs/resilience.md)
- [Arquitetura interna](docs/architecture.md)

## Testes

Na pasta services/market_data:

    poetry install --no-root
    poetry run pytest

Os testes HTTP simulam a Brapi e não consomem sua cota. As requisições de mercado
executadas manualmente no Postman fazem chamadas reais pelo serviço.
