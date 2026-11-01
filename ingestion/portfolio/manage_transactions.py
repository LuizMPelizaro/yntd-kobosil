"""Interactive maintenance of manually entered portfolio transactions."""
import argparse
import json
from psycopg2 import Error as DatabaseError
from ingestion.catalog.database import Database
from ingestion.portfolio.repositories import MaintenanceRepository, StockLookupRepository, UnknownStockError
from ingestion.portfolio.validation import validate_transaction


def prepare_update(db, snapshot, changes):
    allowed = {'symbol', 'type', 'quantity', 'price', 'date'}
    if not changes or set(changes) - allowed:
        raise ValueError('Supply at least one editable field')
    with db.cursor() as cur:
        cur.execute('SELECT stock_code FROM stocks WHERE id_stock=%s', (snapshot['id_stock'],))
        symbol = cur.fetchone()[0]
    original = dict(snapshot, symbol=symbol)
    values = validate_transaction(dict(original, **changes))
    values['id_stock'] = StockLookupRepository(db).resolve_many([values['symbol']])[values['symbol']]
    return values


def execute(db, args, confirm=None):
    repo = MaintenanceRepository(db)
    if args.command == 'list':
        print(json.dumps(repo.list(args.user_id, args.limit, args.offset), default=str, indent=2))
        return False
    snapshot = repo.get(args.user_id, args.id)
    values = None
    if args.command == 'update':
        changes = {name: getattr(args, name) for name in ('symbol', 'type', 'quantity', 'price', 'date')
                   if getattr(args, name) is not None}
        values = prepare_update(db, snapshot, changes)
    print('Current:', json.dumps(snapshot, default=str, ensure_ascii=False))
    print('Proposed:', json.dumps(values, default=str, ensure_ascii=False) if values else 'DELETE permanently')
    answer = (confirm or input)('Type CONFIRM to apply: ')
    if answer.strip() != 'CONFIRM':
        print('Cancelled; no changes applied.')
        return False
    with db.transaction() as session:
        MaintenanceRepository(session).apply(snapshot, values)
    print('Change committed to the database.')
    return True


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be positive')
    return number


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('list', 'update', 'delete'):
        sub = commands.add_parser(command)
        sub.add_argument('--user-id', required=True, type=positive)
        if command == 'list':
            sub.add_argument('--limit', type=positive, default=50)
            sub.add_argument('--offset', type=int, default=0)
        else:
            sub.add_argument('--id', required=True, type=positive)
        if command == 'update':
            for name in ('symbol', 'type', 'quantity', 'price', 'date'):
                sub.add_argument('--' + name)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    try:
        with Database() as db:
            execute(db, args)
    except (ValueError, UnknownStockError, DatabaseError) as exc:
        raise SystemExit(f'Failed: {exc}') from exc
    except (EOFError, KeyboardInterrupt):
        raise SystemExit('Cancelled.')


if __name__ == '__main__':
    main()

