from __future__ import annotations

import httpx
import pytest

from app.domain.enums.context_request import OperationType
from app.domain.exceptions.provider_exceptions import (ProviderAuthError,
                                                       ProviderClientError,
                                                       ProviderNetworkError,
                                                       ProviderParsingError,
                                                       ProviderRateLimitError,
                                                       ProviderServerError,
                                                       ProviderTimeoutError,
                                                       ProviderUnexpectedError)
from app.providers.enums.provider import Provider
from app.providers.shared.http import http_get_json


class MockAsyncClient:
    def __init__(self, response=None, exc: Exception | None = None):
        self._response = response
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *args, **kwargs):
        if self._exc:
            raise self._exc
        return self._response


class DummyResponse:
    def __init__(
        self, status_code=200, json_data=None, json_exc: Exception | None = None
    ):
        self.status_code = status_code
        self._json_data = json_data
        self._json_exc = json_exc
        self.request = httpx.Request("GET", "http://example.com")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=self.request,
                response=self,
            )

    def json(self):
        if self._json_exc:
            raise self._json_exc
        return self._json_data


def _patch_client(monkeypatch, response=None, exc: Exception | None = None):
    def _factory(*args, **kwargs):
        return MockAsyncClient(response=response, exc=exc)

    monkeypatch.setattr("app.providers.shared.http.httpx.AsyncClient", _factory)


@pytest.mark.asyncio
async def test_http_get_json_success(monkeypatch):
    payload = {"ok": True}
    resp = DummyResponse(json_data=payload)
    _patch_client(monkeypatch, response=resp)

    result = await http_get_json(
        url="http://example.com",
        params={},
        headers=None,
        timeout=1.0,
        operation=OperationType.SALES,
        provider=Provider.RENTCAST,
    )

    assert result == payload


@pytest.mark.asyncio
async def test_http_get_json_timeout(monkeypatch):
    _patch_client(monkeypatch, exc=httpx.TimeoutException("boom"))

    with pytest.raises(ProviderTimeoutError):
        await http_get_json(
            "http://example.com",
            {},
            None,
            1.0,
            OperationType.SALES,
            Provider.RENTCAST,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "expected_exception"),
    [
        (429, ProviderRateLimitError),
        (401, ProviderAuthError),
        (400, ProviderClientError),
        (500, ProviderServerError),
        (418, ProviderUnexpectedError),
    ],
)
async def test_http_get_json_http_status_errors(
    monkeypatch, status_code, expected_exception
):
    resp = DummyResponse(status_code=status_code, json_data={})
    _patch_client(monkeypatch, response=resp)

    with pytest.raises(expected_exception):
        await http_get_json(
            "http://example.com",
            {},
            None,
            1.0,
            OperationType.SALES,
            Provider.RENTCAST,
        )


@pytest.mark.asyncio
async def test_http_get_json_network_error(monkeypatch):
    _patch_client(monkeypatch, exc=httpx.HTTPError("network"))

    with pytest.raises(ProviderNetworkError):
        await http_get_json(
            "http://example.com",
            {},
            None,
            1.0,
            OperationType.SALES,
            Provider.RENTCAST,
        )


@pytest.mark.asyncio
async def test_http_get_json_unexpected_error(monkeypatch):
    _patch_client(monkeypatch, exc=RuntimeError("unexpected"))

    with pytest.raises(ProviderUnexpectedError):
        await http_get_json(
            "http://example.com",
            {},
            None,
            1.0,
            OperationType.SALES,
            Provider.RENTCAST,
        )


@pytest.mark.asyncio
async def test_http_get_json_invalid_json(monkeypatch):
    resp = DummyResponse(json_exc=ValueError("bad json"))
    _patch_client(monkeypatch, response=resp)

    with pytest.raises(ProviderParsingError):
        await http_get_json(
            "http://example.com",
            {},
            None,
            1.0,
            OperationType.SALES,
            Provider.RENTCAST,
        )


@pytest.mark.asyncio
async def test_http_get_json_schema_mismatch(monkeypatch):
    resp = DummyResponse(json_data={"not": "a list"})
    _patch_client(monkeypatch, response=resp)

    with pytest.raises(ProviderParsingError):
        await http_get_json(
            "http://example.com",
            {},
            None,
            1.0,
            OperationType.SALES,
            Provider.RENTCAST,
            expected_type=list,
        )
