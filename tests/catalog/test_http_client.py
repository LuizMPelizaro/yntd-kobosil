from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ingestion.catalog.config import BrapiConfig
from ingestion.catalog.http_client import BrapiApiError, BrapiHttpClient


def _fake_response(
    *, ok: bool = True, status_code: int = 200, json_data: dict | None = None, text: str = ""
) -> MagicMock:
    response = MagicMock()
    response.ok = ok
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = text
    return response


def test_session_sends_bearer_token() -> None:
    client = BrapiHttpClient(BrapiConfig(api_key="my-token"))
    assert client.session.headers["Authorization"] == "Bearer my-token"


@patch("requests.Session.get")
def test_get_returns_parsed_json_on_success(mock_get: MagicMock) -> None:
    mock_get.return_value = _fake_response(json_data={"results": [{"symbol": "PETR4"}]})
    client = BrapiHttpClient(BrapiConfig(api_key="fake-token"))

    result = client.get("/v2/tickers", params={"page": 1})

    assert result == {"results": [{"symbol": "PETR4"}]}
    mock_get.assert_called_once()


@patch("requests.Session.get")
def test_get_builds_full_url_from_base_and_path(mock_get: MagicMock) -> None:
    mock_get.return_value = _fake_response(json_data={})
    config = BrapiConfig(api_key="fake-token")
    client = BrapiHttpClient(config)

    client.get("/v2/tickers")

    called_url = mock_get.call_args.args[0]
    assert called_url == f"{config.base_url}/v2/tickers"


@patch("requests.Session.get")
def test_get_raises_brapi_api_error_on_non_ok_status(mock_get: MagicMock) -> None:
    mock_get.return_value = _fake_response(ok=False, status_code=500, text="server error")
    client = BrapiHttpClient(BrapiConfig(api_key="fake-token"))

    with pytest.raises(BrapiApiError):
        client.get("/v2/tickers")