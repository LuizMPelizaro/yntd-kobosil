from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

load_dotenv(dotenv_path=_ENV_PATH)

@dataclass(frozen=True)
class BrapiConfig:
    base_url: str = field(default_factory=lambda: os.environ.get("BRAPI_BASE_URL"))
    api_key: str = field(default_factory=lambda: os.environ.get("BRAPI_TOKEN"))
    timeout_seconds: int = 30
    max_retries: int = 3
    backoff_factor: float = 0.5


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = field(default_factory=lambda: os.environ.get("POSTGRES_HOST"))
    port: int = field(default_factory=lambda: os.environ.get("POSTGRES_PORT"))
    username: str = field(default_factory=lambda: os.environ.get("POSTGRES_USER"))
    password: str = field(default_factory=lambda: os.environ.get("POSTGRES_PASSWORD"))
    database: str = field(default_factory=lambda: os.environ.get("POSTGRES_DB"))
    min_connections: int = 1
    max_connections: int = 5


BRAPI_CONFIG = BrapiConfig()
DATABASE_CONFIG = DatabaseConfig()
