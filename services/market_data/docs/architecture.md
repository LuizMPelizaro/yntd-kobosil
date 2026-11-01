# Arquitetura interna

Fluxo: router → MarketDataProvider → BrapiProvider → BrapiStocksClient → Brapi.

| Arquivo/pasta | Responsabilidade |
|---|---|
| app/main.py | FastAPI, lifespan e tratamento padronizado de falhas de integração |
| app/dependencies.py | Injeta o provider criado no lifespan |
| app/config.py | Configurações de ambiente e validação na inicialização |
| app/routers/market_data.py | Validação dos parâmetros e endpoints /v1 |
| app/core/provider.py | Interface assíncrona de provedores |
| app/core/contracts.py | Modelos das respostas normalizadas |
| app/core/errors.py | Falhas independentes do fornecedor |
| app/providers/brapi/client.py | HTTP, limites, prazos e retentativas |
| app/providers/brapi/provider.py | Chamadas por recurso e tradução das falhas de mapeamento |
| app/providers/brapi/mappers.py | Conversão do JSON do fornecedor para contratos |

Cada processo possui um cliente HTTP compartilhado, criado no startup e fechado
no shutdown. Não há cache persistente, banco ou agendamento interno.

Para outro provedor, implemente MarketDataProvider e injete-o no lifespan,
adequando a configuração. As rotas e seus contratos podem ser reutilizados se
os dados forem compatíveis. Não basta trocar a URL da Brapi.

A normalização seleciona campos; a preservação integral do bruto para replay
no lakehouse é uma responsabilidade pendente do fluxo de ingestão de mercado.
