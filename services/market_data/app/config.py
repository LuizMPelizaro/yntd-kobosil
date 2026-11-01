from dataclasses import dataclass, field
import math
import os
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')


def setting(name, default, cast=float):
    return field(default_factory=lambda: cast(os.getenv(name, str(default))))


@dataclass(frozen=True)
class BrapiSettings:
    base_url: str = setting('BRAPI_BASE_URL', 'https://brapi.dev/api', str)
    api_key: str = field(default_factory=lambda: os.getenv('BRAPI_TOKEN', ''), repr=False)
    timeout_seconds: float = setting('BRAPI_READ_TIMEOUT', 20)
    connect_timeout: float = setting('BRAPI_CONNECT_TIMEOUT', 5)
    total_timeout: float = setting('BRAPI_TOTAL_TIMEOUT', 45)
    queue_timeout: float = setting('BRAPI_QUEUE_TIMEOUT', 1)
    max_retries: int = setting('BRAPI_MAX_RETRIES', 2, int)
    backoff_seconds: float = setting('BRAPI_BACKOFF_SECONDS', 0.5)
    max_backoff: float = setting('BRAPI_MAX_BACKOFF', 8)
    max_concurrency: int = setting('BRAPI_MAX_CONCURRENCY', 4, int)
    max_symbols: int = setting('BRAPI_MAX_SYMBOLS', 10, int)
    max_response_bytes: int = setting('BRAPI_MAX_RESPONSE_BYTES', 10000000, int)

    def __post_init__(self):
        url = urlsplit(self.base_url)
        if url.scheme != 'https' or not url.netloc or url.username or url.password or url.query or url.fragment:
            raise ValueError('BRAPI_BASE_URL must be an HTTPS URL without credentials, query or fragment')
        for name in ('timeout_seconds', 'connect_timeout', 'total_timeout', 'queue_timeout',
                     'backoff_seconds', 'max_backoff', 'max_concurrency', 'max_symbols', 'max_response_bytes'):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be positive and finite')
        if not 0 <= self.max_retries <= 5:
            raise ValueError('max_retries must be between 0 and 5')


BRAPI_SETTINGS = BrapiSettings()
