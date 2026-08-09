# yntd-kobosil

Projeto pessoal de engenharia de dados ponta a ponta: um lakehouse de carteira de ações construído sobre a API pública da [brapi.dev](https://brapi.dev). O objetivo é praticar, num único projeto, os principais componentes de um pipeline de dados moderno: banco transacional, captura de mudanças (CDC), lakehouse em camadas (Bronze, Silver, Gold), orquestração, e consumo via dashboard e agente de insights.

Status atual: versão de desenvolvimento (0.1.0). A base de ingestão e o banco OLTP com CDC já estão funcionais; as camadas do lakehouse, orquestração, dashboard e agente ainda estão em construção. Veja a seção Status e roadmap no final deste documento.

## Arquitetura

O pipeline é dividido em duas partes: ingestão e transformação/consumo.

**Ingestão**
- O usuário envia um JSON com seu e-mail e as transações de compra/venda (símbolo, quantidade, preço, data).
- A brapi.dev fornece o catálogo de ativos negociados (nome, setor, tipo, mercado) e as cotações.
- Ambas as fontes alimentam o banco OLTP em Postgres.
- O Postgres propaga mudanças via CDC (Debezium) para o Redpanda (compatível com a API do Kafka), que alimenta a camada Bronze do lakehouse.

**Transformação e consumo**
- Bronze (Iceberg): dados brutos, como chegaram da origem.
- Silver (Iceberg): dados validados e conformados, processados com Spark em Scala.
- Gold (Iceberg): métricas de negócio (rendimento da carteira ao longo do tempo), modeladas com dbt.
- A camada Gold é consumida por um dashboard e por um agente de insights baseado em LLM.
- O Airflow orquestra as etapas do pipeline (ingestão agendada, jobs Spark, execução do dbt).

## Stack técnica

| Camada | Tecnologia |
|---|---|
| Banco transacional (OLTP) | PostgreSQL |
| Captura de mudanças (CDC) | Debezium |
| Streaming | Redpanda |
| Formato de tabelas do lakehouse | Apache Iceberg |
| Processamento Bronze/Silver | Apache Spark (Scala) |
| Transformação Gold | dbt |
| Orquestração | Apache Airflow |
| Dashboard | Streamlit |
| Agente de insights | LLM sobre a camada Gold |
| Ingestão (scripts) | Python |
| Gerenciamento de dependências Python | Poetry |
| Ambiente local | Docker Compose |

## Estrutura do projeto

```
yntd_kobosil/
    docker/
        docker-compose.yml
        init/                  schema SQL aplicado na primeira subida do Postgres
        connectors/            configuração do conector Debezium e arquivo de secrets
    ingestion/
        catalog/               sincroniza o catálogo de ativos a partir da brapi.dev
        portfolio/              carrega as transações que o usuário envia
    spark/                     jobs Bronze -> Silver (Scala)
    dbt/                       modelos Silver -> Gold
    orchestration/
        airflow/                DAGs de orquestração
    dashboard/                 aplicação Streamlit
    agent/                      agente de insights
    docs/
        architecture/            diagramas de arquitetura
        der/                     modelo de dados do OLTP
    pyproject.toml
    Makefile
    .env.example
```

## Pré-requisitos

- Docker Desktop
- Python 3.11 ou superior
- Poetry

## Configuração inicial

1. Copie o arquivo de variáveis de ambiente e preencha os valores:
```
cp .env.example .env
```

2. Instale as dependências Python:
```
poetry install --no-root
```

3. Suba o ambiente local (Postgres, Redpanda, Debezium Connect):
```
make up
```

4. Registre o conector do Debezium para iniciar a captura de mudanças:
```
make register-connector
```

5. Confirme que o conector está ativo:
```
make connector-status
```

## Uso

**Sincronizar o catálogo de ativos a partir da brapi.dev:**
```
poetry run python -m ingestion.catalog.sync_tickers
```

Para reutilizar o último JSON já baixado, sem chamar a API novamente:
```
poetry run python -m ingestion.catalog.sync_tickers --from-cache
```

**Carregar as transações de um usuário a partir de um arquivo JSON:**
```
poetry run python -m ingestion.portfolio.insert_transactions ingestion/portfolio/example_payload.json
```

## Comandos do Makefile

| Comando | Descrição |
|---|---|
| `make up` | Sobe o ambiente local |
| `make down` | Derruba o ambiente local |
| `make reset` | Recria o ambiente do zero (apaga os volumes) e reregistra o conector |
| `make register-connector` | Registra o conector do Debezium |
| `make delete-connector` | Remove o conector do Debezium |
| `make reconnect` | Remove e registra o conector novamente |
| `make connector-status` | Consulta o status do conector |
| `make logs` | Acompanha os logs dos containers |

## Modelo de dados

O banco OLTP é composto por cinco tabelas, normalizadas até a terceira forma normal: `users`, `markets`, `stock_types`, `stocks` e `stock_transactions`. A tabela `stock_transactions` funciona como um ledger append-only de compras e vendas, o que permite reconstruir a posição da carteira em qualquer data no processamento posterior, em vez de armazenar apenas o estado atual.

<img src="docs/der/der.png"/>

## Status e roadmap

Concluído:
- Modelagem e schema do banco OLTP
- Ambiente Docker local com Postgres, Redpanda e Debezium Connect
- Captura de mudanças (CDC) validada ponta a ponta
- Sincronização do catálogo de ativos a partir da brapi.dev, com paginação e cache local
- Carga de transações do usuário, com resolução de usuário por e-mail e de ativos por símbolo

Em andamento ou pendente:
- Ingestão de dados de cotação, dividendos e balanços a partir da brapi.dev
- Jobs Spark para as camadas Bronze e Silver em Iceberg
- Modelos dbt para a camada Gold
- Orquestração com Airflow
- Dashboard
- Agente de insights
- Preparação para deploy em nuvem (AWS ou GCP)