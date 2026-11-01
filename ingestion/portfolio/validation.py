"""Shared validation for manual inserts and corrections."""
from datetime import datetime
from decimal import Decimal, InvalidOperation


def validate_transaction(original):
    tx = dict(original)
    for name in ('source', 'operation_id'):
        value = tx.get(name)
        if not isinstance(value, str) or not value.strip() or len(value) > 128 or value != value.strip():
            raise ValueError(f'Invalid {name}')
    for name in ('symbol', 'type'):
        if not isinstance(tx.get(name), str) or not tx[name].strip():
            raise ValueError(f'Invalid {name}')
        tx[name] = tx[name].strip().upper()
    if tx['type'] not in ('BUY', 'SELL'):
        raise ValueError('type must be BUY or SELL')
    for name, scale in (('quantity', 6), ('price', 4)):
        try:
            value = Decimal(str(tx[name]))
            if (not value.is_finite() or value <= 0 or
                    value >= Decimal(10) ** (18 - scale) or
                    value != value.quantize(Decimal(10) ** -scale)):
                raise ValueError(f'Invalid {name} or precision')
        except (InvalidOperation, KeyError) as exc:
            raise ValueError(f'Invalid {name}') from exc
        tx[name] = value
    value = tx.get('date')
    try:
        tx['date'] = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValueError('Invalid date') from exc
    if tx['date'].tzinfo is not None:
        raise ValueError('Use a timezone-free trade date until timezone migration')
    return tx


def validate_transactions(payload):
    return [validate_transaction(tx) for tx in payload['transactions']]
