# Ingestão de carteiras
## Idempotência das operações
Cada operação exige source e operation_id (strings não vazias de até 128
caracteres), além de date explícita. Use source=manual e um UUID persistido
no JSON para novas entradas. Reenvie os mesmos identificadores em retentativas.
Mesmo identificador com dados diferentes rejeita e reverte o envio inteiro.
process_payload retorna inserted e existing após o commit. Quarentena e
aceitação parcial ainda não estão implementadas.

Bancos existentes: aplicar docker/migrations/001_operation_identity.sql com
psql -v ON_ERROR_STOP=1. A migração preserva IDs e atribui legacy/legacy-ID.
O exemplo está vinculado às operações 1 e 2 do banco local existente.
A correspondência com importações antigas não é inferida pelo conteúdo.

Datas continuam sem fuso nesta etapa. Preços e quantidades usam Decimal e
precisão compatível com o schema. O catálogo mantém seu fluxo transacional
anterior. Cada worker deve possuir sua própria instância de Database:
o pool atual não deve ser compartilhado entre threads.

O próprio teste provisiona e remove seu banco descartável, conforme descrito abaixo.

### Testes de integração em desenvolvimento
Configure APP_ENV=dev (ou test) no .env e execute poetry run pytest.
O teste de idempotência cria um banco yntd_test_<UUID> no mesmo servidor
Postgres configurado, aplica o schema, insere fixtures próprias e remove
somente esse banco ao terminar. O usuário precisa de permissão CREATEDB.
Os registros da aplicação não são usados nem alterados.
Fora de dev/test o teste é ignorado. Em dev/test falhas de conexão ou
permissão fazem o teste falhar, em vez de ignorá-lo silenciosamente.
Esta configuração substitui RUN_ISOLATED_DB_TESTS e o runner antigo.


