# Manutenção de operações

Implementado: CLI de listagem, edição e exclusão de operações manuais.

## Uso

Execute na raiz do projeto, com o Postgres configurado no .env:

    poetry run python -m ingestion.portfolio.manage_transactions list --user-id 1 --limit 50 --offset 0
    poetry run python -m ingestion.portfolio.manage_transactions update --user-id 1 --id 12 --quantity 50
    poetry run python -m ingestion.portfolio.manage_transactions delete --user-id 1 --id 12

A listagem aceita limit entre 1 e 200 e offset não negativo. Os resultados incluem
id_stock, identificadores da operação e seus valores. Para consultar símbolos,
use o catálogo (stocks).

Edição e exclusão exibem a prévia e exigem digitar CONFIRM. Qualquer outra
resposta cancela. Não há transação aberta enquanto o usuário responde.
Após confirmar, a aplicação bloqueia e relê o registro em uma transação curta.
Se o conteúdo ou a versão Postgres xmin mudou desde a prévia, a alteração é
rejeitada. Esse token é transitório e não é uma versão persistente de negócio.

## Campos e validação

A edição permite symbol, type, quantity, price e date. A validação é compartilhada
com a inserção: símbolo deve existir, tipo BUY/SELL, valores positivos e finitos,
precisão compatível com NUMERIC e data explícita sem fuso nesta etapa.
IDs, proprietário, source e operation_id são imutáveis. Toda mutação filtra
usuário e operação conjuntamente; isso não substitui autenticação futura.
Não há validação histórica de posição nesta etapa.

## Reenvios e exclusão física

A exclusão remove fisicamente o registro. O JSON original não é atualizado:
para reutilizá-lo, corrija também seu conteúdo. Após editar, o conteúdo antigo
provoca conflito de idempotência. Após excluir, reenviar pode recriar a operação.
O envio de inserções continua atômico. Cancelamentos formais, quarentena e
aceitação parcial permanecem adiados.

## Arquivos

- ingestion/portfolio/manage_transactions.py: CLI e prévia.
- ingestion/portfolio/repositories.py: consultas e mutações transacionais.
- ingestion/portfolio/validation.py: validação compartilhada.
- ingestion/portfolio/insert_transactions.py: reutiliza a validação.
- tests/portifolio/test_maintenance.py: integração usando banco temporário.

Schema, microserviço Brapi e configuração CDC não exigem alteração.
Debezium captura UPDATE/DELETE. A futura Bronze preservará eventos e a Silver
precisará aplicar mudanças e recalcular a carteira. Esse processamento ainda
não foi implementado.

