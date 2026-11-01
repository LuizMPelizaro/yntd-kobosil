# Postman

## Importação

1. Inicie o serviço na raiz do repositório com make market-data-rebuild (Docker)
   ou make market-data (Python local).
2. No Postman, abra Import e selecione os dois arquivos desta pasta:
   - market-data.postman_collection.json
   - local.postman_environment.json
3. Selecione o ambiente Market Data - Local.
4. Execute Health primeiro; depois abra uma consulta de mercado e clique Send.

O formato é Collection v2.1. A importação de coleções e ambientes está descrita
na [documentação oficial do Postman](https://learning.postman.com/docs/getting-started/importing-and-exporting/importing-data/).

## Variáveis

| Variável | Uso |
|---|---|
| base_url | Endereço do serviço; padrão http://127.0.0.1:8001, sem barra final |
| symbols | Símbolos separados por vírgulas; padrão PETR4 |
| range / interval | Janela e granularidade do histórico |
| startDate / endDate | Datas ISO explícitas; substitua os valores de exemplo |
| sortBy / sortOrder | Campo e direção de ordenação |
| period / mode | Parâmetros dos indicadores e dados financeiros |

As variáveis possuem valores padrão também na coleção. O ambiente selecionado
prevalece sobre eles. Alterar uma variável não ativa um parâmetro desmarcado:
abra a aba Params e marque os filtros desejados. Só symbols vem habilitado.
Os valores opcionais são exemplos editáveis, não garantia de suporte do plano.

## Verificações e cota

Cada requisição verifica HTTP 200 e JSON. Health verifica status=ok; as demais
verificam a lista de resultados. Falhas de plano, cota ou indisponibilidade
fazem essas verificações falharem, mesmo com a coleção corretamente configurada.

Enviar uma consulta /v1 consome chamadas reais ao provedor, possivelmente com
retentativas. Importar os arquivos não dispara chamadas. Evite rodar a coleção
inteira repetidamente; comece por requisições individuais. O timeout do Postman
deve ser superior ao BRAPI_TOTAL_TIMEOUT do servidor (padrão 45 segundos).

Não há token nos arquivos. BRAPI_TOKEN deve ficar no .env do microserviço.
Se usar Postman web para localhost, pode ser necessário selecionar o Desktop
Agent. A aplicação desktop também pode acessar o serviço local.

## Alternativa: OpenAPI

Com o serviço iniciado, importe no Postman:

    http://127.0.0.1:8001/openapi.json

Isso gera uma coleção a partir do contrato ativo. A coleção versionada nesta
pasta acrescenta valores de exemplo, variáveis e verificações de resposta.
Quando alterar rotas ou parâmetros, atualize a coleção versionada também.
Consulte o [contrato HTTP](../docs/api.md) para respostas e erros.
