# Resiliência do microserviço de mercado

O microserviço responde a chamadas HTTP; o Airflow será responsável por agendar
coletas e persistir/reprocessar falhas. Configurações são lidas na inicialização;
reinicie o serviço após alterar o .env. Consulte ../.env.example.

## Configuração

| Variável | Padrão | Efeito |
|---|---:|---|
| BRAPI_CONNECT_TIMEOUT | 5 s | Timeout de conexão |
| BRAPI_READ_TIMEOUT | 20 s | Timeout de leitura/escrita |
| BRAPI_TOTAL_TIMEOUT | 45 s | Prazo total, incluindo fila, tentativas e esperas |
| BRAPI_QUEUE_TIMEOUT | 1 s | Espera máxima para obter uma vaga |
| BRAPI_MAX_RETRIES | 2 | Até três tentativas no total; configuração aceita 0 a 5 |
| BRAPI_BACKOFF_SECONDS | 0.5 s | Base da espera exponencial com jitter |
| BRAPI_MAX_BACKOFF | 8 s | Máxima espera entre tentativas |
| BRAPI_MAX_CONCURRENCY | 4 | Requisições ativas por processo, incluindo retentativas |
| BRAPI_MAX_SYMBOLS | 10 | Máximo de símbolos distintos por consulta |
| BRAPI_MAX_RESPONSE_BYTES | 10000000 | Limite de bytes descomprimidos por resposta |

São limites locais escolhidos para desenvolvimento, não garantias do plano
Brapi. Ajuste ao contrato do provedor. Vários workers ou réplicas multiplicam
concorrência; não há rate limiter distribuído nem controle mensal de cota.
Airflow deve limitar seu paralelismo. Requests aguardando vaga têm timeout;
um proxy/servidor com controle de admissão continua necessário para exposição pública.

## Retentativas e erros

Somente GETs são utilizados. Erros de transporte e timeout, além de HTTP
429/500/502/503/504, têm tentativas limitadas. 400/401/403/404 e redirecionamentos
não são repetidos. Retry-After numérico ou HTTP-date é respeitado: se exceder
a espera máxima, a chamada falha sem tentar antes do prazo do fornecedor.
O orçamento total também pode interromper a chamada antes da próxima tentativa.

Erros têm envelope error com code/message em inglês. 503 indica serviço ocupado,
provedor indisponível ou rate limit; 504 indica timeout; 502 indica rejeição,
resposta inválida ou grande demais. Erros locais de parâmetros usam 400/422
com detail do FastAPI. Corpos, credenciais e URLs internas do fornecedor não
são devolvidos. JSON sem results, resultados sem campos obrigatórios e dados
incompatíveis com os modelos não são tratados como sucesso vazio.

Símbolos são normalizados, deduplicados e validados. Datas devem ser datas ISO,
com início não posterior ao fim. Outros parâmetros têm tamanho limitado;
valores específicos continuam sujeitos à validação do provedor.

## Segurança e ciclo de vida

O cliente é criado e encerrado pelo lifespan do FastAPI. Usa HTTPS, verificação
TLS padrão, não segue redirects e não herda proxies do ambiente. A URL deve
ser configurada apenas por operadores confiáveis. O token fica no header e não
aparece no repr das configurações. Não registrar headers/corpos de resposta.
O Compose publica a porta 8001 apenas em 127.0.0.1. O serviço ainda não possui
autenticação de consumidores; para uso externo, implantar autenticação e limites
no gateway. O health é liveness local e não faz consultas à Brapi.

## Testes

Na pasta services/market_data, execute poetry run pytest. Os testes usam mocks
HTTP, sem token ou chamadas reais. Rebuild local: make market-data-rebuild.

Referências: https://www.python-httpx.org/advanced/transports/ e
https://brapi.dev/docs (tratamento de 429 e Retry-After).

