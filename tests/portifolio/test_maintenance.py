from argparse import Namespace
from decimal import Decimal
import pytest
from ingestion.catalog.database import Database
from ingestion.portfolio.insert_transactions import process_payload
from ingestion.portfolio.repositories import MaintenanceRepository, ConcurrentModification, OperationNotFound
from ingestion.portfolio.manage_transactions import execute, prepare_update

@pytest.fixture
def populated(integration_database_config):
    with Database(integration_database_config) as db:
        process_payload(dict(email='maintenance@example.com', first_name='Test', transactions=[
            dict(source='manual', operation_id='one', symbol='PETR4', type='BUY',
                 quantity=100, price='36.65', date='2026-07-15')]), db)
        yield db


def test_update_delete_and_replay(populated):
    db = populated
    repo = MaintenanceRepository(db)
    before = repo.list(1)[0]
    values = prepare_update(db, before, {'quantity': '50', 'symbol': 'lren3'})
    with db.transaction() as session:
        MaintenanceRepository(session).apply(before, values)
    after = repo.get(1, before['id_transaction'])
    assert after['quantity'] == Decimal('50')
    assert after['id_stock'] == 2
    for key in ('source', 'operation_id', 'id_user', 'id_transaction'):
        assert after[key] == before[key]
    with pytest.raises(ConcurrentModification), db.transaction() as session:
        MaintenanceRepository(session).apply(before)
    with pytest.raises(OperationNotFound):
        repo.get(2, before['id_transaction'])
    with db.transaction() as session:
        MaintenanceRepository(session).apply(after)
    assert repo.list(1) == []
    with pytest.raises(OperationNotFound):
        repo.get(1, before['id_transaction'])


def test_validation_confirmation_and_concurrent_preview(populated):
    db = populated
    repo = MaintenanceRepository(db)
    before = repo.list(1)[0]
    args = Namespace(command='delete', user_id=1, id=before['id_transaction'])
    assert execute(db, args, confirm=lambda _: 'no') is False
    assert repo.get(1, args.id) == before
    for changes in ({'quantity': '-1'}, {'date': 'bad'}, {'source': 'other'}, {}):
        with pytest.raises(ValueError):
            prepare_update(db, before, changes)
    def concurrent(_):
        with db.transaction() as session:
            MaintenanceRepository(session).apply(before, prepare_update(db, before, {'price': '40'}))
        return 'CONFIRM'
    with pytest.raises(ConcurrentModification):
        execute(db, args, confirm=concurrent)
    assert repo.get(1, args.id)['price'] == 40
    assert execute(db, args, confirm=lambda _: 'CONFIRM') is True

