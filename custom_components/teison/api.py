"""Async client for the Teison cloud HTTP API.

The protocol was reverse-engineered from the official *My Teison* / *Teison Me*
mobile apps. Both clouds expose the same ``cpAm2/*`` REST surface; they differ
only in their base URL and in how the login endpoint is shaped:

* **My Teison** (``cloud.teison.com``) posts JSON with the password
  RSA-encrypted against a well-known public key.
* **Teison Me** (``teison-m3.x-cheng.com``) posts a plain form.

Authenticated requests carry the session token in a ``token`` header. The cloud
returns ``403`` to clients that do not look like a browser, hence the spoofed
``User-Agent``/``Origin``/``Referer`` headers.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

import aiohttp
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from .const import APP_MYTEISON, BASE_URLS

_LOGGER = logging.getLogger(__name__)

# Public key the My Teison cloud uses to encrypt the password at login.
_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDKzH8tu+lGYMkT61r7FCdBZ/ez
lLg22grOvvuQ76NtwGPeAUklREWJqArQgd4U6RCx0vVCT6gtBOtXUK2NkSJvKjUW
BhRp6in5VJikMp1+KxyO2vgjIrKMDWzucuoeozBQ89LhhyoB2Sp3jpxKpb83/Pqu
p0gQXJmL39hJ3O+HlwIDAQAB
-----END PUBLIC KEY-----"""

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)

_BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://cloud.teison.com",
    "Referer": "https://cloud.teison.com/",
}


class TeisonError(Exception):
    """Base exception for all Teison client errors."""


class TeisonConnectionError(TeisonError):
    """Raised on network/transport failures or non-JSON responses."""


class TeisonAuthError(TeisonError):
    """Raised when credentials or the session token are rejected."""


def _encrypt_password(password: str) -> str:
    """RSA/PKCS1v15-encrypt ``password`` and base64-encode it (My Teison)."""
    public_key = load_pem_public_key(_PUBLIC_KEY_PEM)
    encrypted = public_key.encrypt(password.encode("utf-8"), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode("utf-8")


class TeisonApiClient:
    """Thin async wrapper around the Teison cloud HTTP API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        app: str,
        username: str,
        password: str,
    ) -> None:
        """Initialise the client. No I/O happens here."""
        self._session = session
        self._app = app
        self._username = username
        self._password = password
        self._base_url = BASE_URLS[app]
        self._token: str | None = None

    @property
    def token(self) -> str | None:
        """Return the current session token, if any."""
        return self._token

    async def async_login(self) -> str:
        """Authenticate and cache the session token.

        Raises:
            TeisonAuthError: if the credentials are rejected.
            TeisonConnectionError: on transport failure.
        """
        if self._app == APP_MYTEISON:
            data = await self._request(
                "POST",
                "api/v1/login/login",
                authenticated=False,
                json={
                    "username": self._username,
                    "password": _encrypt_password(self._password),
                },
            )
            token = (data.get("data") or {}).get("token")
        else:
            data = await self._request(
                "POST",
                "cpAm2/login",
                authenticated=False,
                data={
                    "language": "en_US",
                    "username": self._username,
                    "password": self._password,
                },
            )
            token = data.get("token") or (data.get("data") or {}).get("token")

        if not token:
            reason = data.get("message", data) if isinstance(data, dict) else data
            raise TeisonAuthError(f"Login failed: {reason}")
        self._token = token
        return token

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return the list of chargers paired with the account."""
        data = await self._request("GET", "cpAm2/cp/deviceList")
        return (data.get("bizData") or {}).get("deviceList") or []

    async def async_get_device_detail(self, device_id: int | str) -> dict[str, Any]:
        """Return live telemetry (voltage, current, power, status, ...)."""
        data = await self._request("GET", f"cpAm2/cp/deviceDetail/{device_id}")
        return data.get("bizData") or {}

    async def async_get_cp_config(self, device_id: int | str) -> dict[str, Any]:
        """Return the charger configuration (max current, schedule, ...)."""
        data = await self._request("GET", f"cpAm2/cp/getCpConfig/{device_id}")
        return data.get("bizData") or {}

    async def async_set_cp_config(
        self, device_id: int | str, key: str, value: Any
    ) -> None:
        """Change a single configuration value on the charger."""
        await self._request(
            "POST",
            f"cpAm2/cp/changeCpConfig/{device_id}",
            json={"key": key, "value": value},
        )

    async def async_start_charge(self, device_id: int | str) -> None:
        """Start a charging session."""
        await self._request("POST", f"cpAm2/cp/startCharge/{device_id}")

    async def async_stop_charge(self, device_id: int | str) -> None:
        """Stop the active charging session."""
        # The cloud models this as a GET, oddly enough.
        await self._request("GET", f"cpAm2/cp/stopCharge/{device_id}")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool = True,
        _retry_auth: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Perform a request, transparently re-logging in on token expiry."""
        if authenticated and self._token is None:
            await self.async_login()

        headers = dict(_BASE_HEADERS)
        if authenticated and self._token:
            headers["token"] = self._token

        url = f"{self._base_url}{path}"
        payload: dict[str, Any] = {}
        try:
            async with self._session.request(
                method, url, headers=headers, timeout=_REQUEST_TIMEOUT, **kwargs
            ) as resp:
                auth_failed = resp.status in (401, 403)
                if not auth_failed:
                    resp.raise_for_status()
                    body = await resp.json(content_type=None)
                    if not isinstance(body, dict):
                        raise TeisonConnectionError(
                            f"Unexpected response for {path}: {body!r}"
                        )
                    payload = body
        except aiohttp.ClientError as err:
            raise TeisonConnectionError(
                f"Error talking to Teison cloud: {err}"
            ) from err

        # The cloud also signals auth problems in the JSON body, not just via
        # HTTP status codes.
        if not auth_failed:
            auth_failed = (
                payload.get("code") in (401, 403)
                or payload.get("message") == "token invalid"
            )

        if not auth_failed:
            return payload

        # Token expired: re-login once and replay, otherwise give up.
        if authenticated and _retry_auth:
            _LOGGER.debug("Token expired, re-authenticating and retrying %s", path)
            self._token = None
            await self.async_login()
            return await self._request(
                method, path, authenticated=authenticated, _retry_auth=False, **kwargs
            )
        raise TeisonAuthError(f"Authentication rejected for {path}")
