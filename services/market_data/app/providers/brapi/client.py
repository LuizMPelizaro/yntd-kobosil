"""Bounded async HTTP access to the market data provider."""
import asyncio
from contextlib import aclosing
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import math
import random
import httpx
from app.config import BRAPI_SETTINGS
from app.core.errors import MarketDataError

# Compatibility alias for existing provider consumers.
BrapiApiError = MarketDataError


def retry_after(value):
    if not value:
        return None
    try:
        delay = float(value)
    except ValueError:
        try:
            delay = (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return None
    return max(0, delay) if math.isfinite(delay) else None


class BrapiStocksClient:
    def __init__(self, settings=BRAPI_SETTINGS, *, transport=None):
        self.settings = settings
        self._slots = asyncio.Semaphore(settings.max_concurrency)
        self._client = httpx.AsyncClient(
            base_url=settings.base_url.rstrip('/') + '/',
            headers={'Authorization': f'Bearer {settings.api_key}'} if settings.api_key else {},
            timeout=httpx.Timeout(settings.timeout_seconds, connect=settings.connect_timeout,
                                  pool=settings.queue_timeout),
            limits=httpx.Limits(max_connections=settings.max_concurrency,
                               max_keepalive_connections=settings.max_concurrency),
            transport=transport, follow_redirects=False, trust_env=False)

    async def fetch(self, resource, symbols, params=None):
        if resource not in {'quote', 'historical', 'dividends', 'statistics', 'financial-data'}:
            raise ValueError('Unsupported resource')
        query = {key: value for key, value in (params or {}).items() if value is not None}
        query['symbols'] = ','.join(symbols)
        acquired = False
        try:
            async with asyncio.timeout(self.settings.total_timeout):
                try:
                    await asyncio.wait_for(self._slots.acquire(), self.settings.queue_timeout)
                except TimeoutError:
                    raise MarketDataError('Service is busy', code='service_busy', status_code=503) from None
                acquired = True
                return await self._fetch(resource, query)
        except TimeoutError:
            raise MarketDataError('Provider deadline exceeded', code='upstream_timeout', status_code=504) from None
        finally:
            if acquired:
                self._slots.release()

    async def _fetch(self, resource, query):
        for attempt in range(self.settings.max_retries + 1):
            delay = None
            try:
                async with self._client.stream('GET', f'v2/stocks/{resource}', params=query) as response:
                    status = response.status_code
                    if status in {429, 500, 502, 503, 504}:
                        delay = retry_after(response.headers.get('Retry-After'))
                        failure = MarketDataError('Provider rate limit reached' if status == 429 else 'Provider unavailable',
                            code='upstream_rate_limited' if status == 429 else 'upstream_unavailable', status_code=503)
                    elif not 200 <= status < 300:
                        raise MarketDataError('Provider rejected the request', code='upstream_rejected')
                    else:
                        body = bytearray()
                        async with aclosing(response.aiter_bytes()) as chunks:
                            async for chunk in chunks:
                                body.extend(chunk)
                                if len(body) > self.settings.max_response_bytes:
                                    raise MarketDataError('Provider response exceeded size limit', code='upstream_response_too_large')
                        try:
                            payload = json.loads(body)
                        except (ValueError, UnicodeError):
                            raise MarketDataError('Invalid provider JSON', code='upstream_invalid_response') from None
                        if not isinstance(payload, dict) or not isinstance(payload.get('results'), list):
                            raise MarketDataError('Invalid provider envelope', code='upstream_invalid_response')
                        for item in payload['results']:
                            if (not isinstance(item, dict) or not isinstance(item.get('data'), dict)
                                or not isinstance(item.get('symbol'), str)
                                or not isinstance(item.get('requestedSymbol'), str)
                                or not isinstance(item.get('changed'), bool)):
                                raise MarketDataError('Invalid provider result', code='upstream_invalid_response')
                        return payload
            except httpx.DecodingError:
                raise MarketDataError('Invalid provider encoding', code='upstream_invalid_response') from None
            except httpx.TimeoutException:
                failure = MarketDataError('Provider timed out', code='upstream_timeout', status_code=504)
            except httpx.TransportError:
                failure = MarketDataError('Provider connection failed', code='upstream_unavailable', status_code=503)
            if attempt == self.settings.max_retries:
                raise failure
            if delay is None:
                delay = random.uniform(0, min(self.settings.max_backoff, self.settings.backoff_seconds * 2 ** attempt))
            # Never retry before Retry-After; long delays are delegated to the scheduler.
            if delay > self.settings.max_backoff:
                raise failure
            await asyncio.sleep(delay)

    async def aclose(self):
        await self._client.aclose()

