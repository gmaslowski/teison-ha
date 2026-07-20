"""Contract tests for the Teison API client against mocked HTTP responses."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest

from custom_components.teison.api import (
    TeisonApiClient,
    TeisonAuthError,
    _encrypt_password,
)
from custom_components.teison.const import APP_MYTEISON, APP_TEISONME, BASE_URLS

MYTEISON = BASE_URLS[APP_MYTEISON]
TEISONME = BASE_URLS[APP_TEISONME]


def _client(hass: HomeAssistant, app: str) -> TeisonApiClient:
    return TeisonApiClient(async_get_clientsession(hass), app, "user", "pass")


def test_encrypt_password() -> None:
    """RSA/PKCS1v15 output is base64 text that is not the plaintext."""
    out = _encrypt_password("secret")
    assert isinstance(out, str)
    assert out and out != "secret"


async def test_login_myteison(hass: HomeAssistant, aioclient_mock) -> None:
    """My Teison nests the token under ``data``."""
    aioclient_mock.post(
        f"{MYTEISON}api/v1/login/login", json={"code": 200, "data": {"token": "abc"}}
    )
    client = _client(hass, APP_MYTEISON)
    assert await client.async_login() == "abc"
    assert client.token == "abc"


async def test_login_teisonme(hass: HomeAssistant, aioclient_mock) -> None:
    """Teison Me returns the token at the root of the body."""
    aioclient_mock.post(f"{TEISONME}cpAm2/login", json={"code": 200, "token": "xyz"})
    assert await _client(hass, APP_TEISONME).async_login() == "xyz"


async def test_login_failure_raises(hass: HomeAssistant, aioclient_mock) -> None:
    """A tokenless login response is an auth error."""
    aioclient_mock.post(
        f"{MYTEISON}api/v1/login/login", json={"code": 401, "message": "bad creds"}
    )
    with pytest.raises(TeisonAuthError):
        await _client(hass, APP_MYTEISON).async_login()


async def test_device_detail_parses_bizdata(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Telemetry is unwrapped from ``bizData`` after an implicit login."""
    aioclient_mock.post(
        f"{MYTEISON}api/v1/login/login", json={"code": 200, "data": {"token": "tok"}}
    )
    aioclient_mock.get(
        f"{MYTEISON}cpAm2/cp/deviceDetail/5", json={"bizData": {"power": 42}}
    )
    detail = await _client(hass, APP_MYTEISON).async_get_device_detail(5)
    assert detail == {"power": 42}


async def test_device_list_parses_bizdata(hass: HomeAssistant, aioclient_mock) -> None:
    """The device list is unwrapped from ``bizData.deviceList``."""
    aioclient_mock.post(
        f"{MYTEISON}api/v1/login/login", json={"code": 200, "data": {"token": "tok"}}
    )
    aioclient_mock.get(
        f"{MYTEISON}cpAm2/cp/deviceList",
        json={"bizData": {"deviceList": [{"id": 1}, {"id": 2}]}},
    )
    devices = await _client(hass, APP_MYTEISON).async_get_devices()
    assert [d["id"] for d in devices] == [1, 2]
