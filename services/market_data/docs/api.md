# Contrato HTTP

Base local: http://127.0.0.1:8001. Todos os endpoints usam GET, sem body.
O serviço local não exige autenticação do consumidor. O token da Brapi pertence
ao .env do servidor e não deve ser enviado pelo Postman. Consulte as medidas e
limitações de exposição em [resiliência](resilience.md).

## Endpoints

| Caminho | Consulta | Parâmetros opcionais |
|---|---|---|
| /health | Liveness local | Nenhum |
| /v1/quote | Cotação atual | Nenhum |
| /v1/historical | Série OHLCV | range, interval, startDate, endDate, sortOrder |
| /v1/dividends | Dividendos e bonificações | startDate, endDate, sortBy, sortOrder |
| /v1/statistics | Indicadores | period, mode, startDate, endDate |
| /v1/financial-data | Dados financeiros | period, mode, startDate, endDate |

Todos os endpoints /v1 exigem symbols, separado por vírgulas. Exemplo:

    GET /v1/quote?symbols=PETR4,VALE3
    GET /v1/historical?symbols=PETR4&range=1mo&interval=1d
    GET /v1/historical?symbols=PETR4&startDate=2026-01-01&endDate=2026-01-07

Esses exemplos não garantem cobertura do plano. Os valores específicos de
range, interval, period, mode e ordenação são encaminhados ao provedor.
Evite combinar range com datas explícitas sem conferir a semântica do provedor.

Símbolos são normalizados para maiúsculas e deduplicados. O limite padrão é
10 símbolos distintos por requisição, configurável em BRAPI_MAX_SYMBOLS.
O texto de symbols aceita até 4096 caracteres; os demais parâmetros, até 32.
Datas devem usar YYYY-MM-DD e startDate não pode superar endDate.

## Respostas

/health responde:

    {"status": "ok"}

Os endpoints /v1 retornam uma lista, inclusive para um único símbolo:

```json
[
  {
    "requested_symbol": "PETR4",
    "symbol": "PETR4",
    "changed": false,
    "data": {"regular_market_price": 36.65}
  }
]
```

Exemplo ilustrativo, não uma cotação real. Campos opcionais podem ser null.
changed indica que o provedor resolveu o símbolo solicitado para outro código.
A lista pode estar vazia. Um erro de estrutura do provedor não é convertido em
lista vazia pelo cliente HTTP.

| Endpoint | Conteúdo principal de data |
|---|---|
| quote | regular_market_price, currency, regular_market_time e demais campos de cotação |
| historical | used_interval, used_range, candles (date, open, high, low, close, volume, adjusted_close) |
| dividends | cash_dividends e stock_dividends |
| statistics | market_cap, trailing_pe, dividend_yield e outros indicadores |
| financial-data | total_revenue, total_cash, total_debt e outros fundamentos |

O contrato completo dos campos e tipos está no OpenAPI gerado em /openapi.json,
com base em app/core/contracts.py. Para indicadores, o mapeamento atual não
implementa um envelope próprio de séries históricas; não presuma que mode=history
produzirá uma série temporal completa. Respostas incompatíveis falham com 502.

## Erros

| HTTP | Significado |
|---|---|
| 400 | Símbolos ou datas inválidos, ou excesso de símbolos |
| 422 | Parâmetro obrigatório ausente ou limite de tamanho excedido |
| 502 | Rejeição do provedor, resposta inválida ou grande demais |
| 503 | Serviço ocupado, provedor indisponível ou rate limit |
| 504 | Timeout ou prazo total excedido |

Erros locais usam detail. Erros de integração usam:

    {"error": {"code": "upstream_timeout", "message": "Provider timed out"}}

Códigos possíveis: service_busy, upstream_timeout, upstream_rate_limited,
upstream_unavailable, upstream_rejected, upstream_invalid_response e
upstream_response_too_large. Não se deve assumir que todo 503 permite retentativa
imediata: respeite um intervalo no cliente/agendador.
