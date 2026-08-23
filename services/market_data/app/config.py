from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH)


@dataclass(frozen=True)
class BrapiSettings:
    base_url: str = field(
        default_factory=lambda: os.environ.get("BRAPI_BASE_URL", "https://brapi.dev/api")
    )
    api_key: str = field(default_factory=lambda: os.environ.get("BRAPI_TOKEN", ""))
    timeout_seconds: float = 30.0
    max_retries: int = 3


BRAPI_SETTINGS = BrapiSettings()