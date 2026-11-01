import asyncio
from dataclasses import replace
import httpx
import pytest
from app.config import BrapiSettings
from app.core.errors import MarketDataError
from app.providers.brapi.client import BrapiStocksClient, retry_after


def settings(**kwargs):
    return replace(BrapiSettings(), backoff_seconds=0.001, **kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize('status', [429, 500, 502, 503, 504])
async def test_transient_status_retries(status):
    calls = []
    def respond(request):
        calls.append(request)
        assert request.url.path == '/api/v2/stocks/quote'
        return httpx.Response(status if len(calls) == 1 else 200,
                              json={'results': []}, headers={'Retry-After': '0'})
    client = BrapiStocksClient(settings(), transport=httpx.MockTransport(respond))
    try:
        assert await client.fetch('quote', ['PETR4']) == {'results': []}
        assert len(calls) == 2
    finally:
        await client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize('status', [400, 401, 403, 404, 302])
async def test_permanent_errors_do_not_retry_or_leak(status):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(status, text='SECRET PROVIDER DETAILS')
    client = BrapiStocksClient(settings(), transport=httpx.MockTransport(respond))
    try:
        with pytest.raises(MarketDataError) as exc:
            await client.fetch('quote', ['PETR4'])
        assert 'SECRET' not in str(exc.value)
        assert len(calls) == 1
    finally:
        await client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize('payload', [{}, {'results': None}, {'results': [{}]}])
async def test_invalid_envelope(payload):
    client = BrapiStocksClient(settings(), transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json=payload)))
    try:
        with pytest.raises(MarketDataError, match='Invalid provider'):
            await client.fetch('quote', ['PETR4'])
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_deadline_and_slot_release():
    async def respond(request):
        await asyncio.sleep(1)
        return httpx.Response(200, json={'results': []})
    client = BrapiStocksClient(settings(total_timeout=0.02), transport=httpx.MockTransport(respond))
    try:
        for _ in range(2):
            with pytest.raises(MarketDataError) as exc:
                await client.fetch('quote', ['PETR4'])
            assert exc.value.status_code == 504
        assert client._slots._value == client.settings.max_concurrency
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_retry_after_not_shortened_and_attempts_bounded():
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(429, headers={'Retry-After': '3600'})
    client = BrapiStocksClient(settings(), transport=httpx.MockTransport(respond))
    try:
        with pytest.raises(MarketDataError):
            await client.fetch('quote', ['PETR4'])
        assert len(calls) == 1
    finally:
        await client.aclose()
    assert retry_after('not-a-date') is None
    assert retry_after('NaN') is None


@pytest.mark.asyncio
async def test_size_limit():
    client = BrapiStocksClient(settings(max_response_bytes=8), transport=httpx.MockTransport(
        lambda r: httpx.Response(200, content=b'x' * 9)))
    try:
        with pytest.raises(MarketDataError) as exc:
            await client.fetch('quote', ['PETR4'])
        assert exc.value.code == 'upstream_response_too_large'
    finally:
        await client.aclose()

@pytest.mark.asyncio
async def test_concurrency_limit_rejects_excess_work():
    started, release = asyncio.Event(), asyncio.Event()
    async def respond(request):
        started.set()
        await release.wait()
        return httpx.Response(200, json={'results': []})
    client = BrapiStocksClient(settings(max_concurrency=1, queue_timeout=0.01),
                              transport=httpx.MockTransport(respond))
    task = asyncio.create_task(client.fetch('quote', ['PETR4']))
    try:
        await asyncio.wait_for(started.wait(), 1)
        with pytest.raises(MarketDataError) as exc:
            await client.fetch('quote', ['VALE3'])
        assert exc.value.code == 'service_busy'
        release.set()
        await task
    finally:
        release.set()
        await task
        await client.aclose()


@pytest.mark.asyncio
async def test_transport_failure_exhausts_retry_budget():
    calls = []
    def respond(request):
        calls.append(request)
        raise httpx.ReadTimeout('private data', request=request)
    client = BrapiStocksClient(settings(max_retries=1), transport=httpx.MockTransport(respond))
    try:
        with pytest.raises(MarketDataError) as exc:
            await client.fetch('quote', ['PETR4'])
        assert exc.value.code == 'upstream_timeout'
        assert 'private' not in str(exc.value)
        assert len(calls) == 2
    finally:
        await client.aclose()


def test_settings_reject_unsafe_values():
    for changes in ({'base_url': 'http://brapi.dev/api'}, {'max_concurrency': 0},
                    {'total_timeout': float('nan')}, {'max_retries': 6}):
        with pytest.raises(ValueError):
            settings(**changes)
