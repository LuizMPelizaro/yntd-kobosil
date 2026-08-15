from __future__ import annotations

from unittest.mock import MagicMock

import pytest

@pytest.fixture
def fake_cursor() -> MagicMock:
    return MagicMock()


@pytest.fixture
def fake_db(fake_cursor: MagicMock) -> MagicMock:
    db = MagicMock()
    db.cursor.return_value.__enter__.return_value = fake_cursor
    db.cursor.return_value.__exit__.return_value = False
    return db