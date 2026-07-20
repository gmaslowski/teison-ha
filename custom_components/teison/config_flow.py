"""Config flow for the Teison EV Charger integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import voluptuous as vol

from .api import (
    TeisonApiClient,
    TeisonAuthError,
    TeisonConnectionError,
    TeisonError,
)
from .const import (
    APP_MYTEISON,
    APP_TEISONME,
    CONF_APP,
    CONF_DEVICE_ID,
    DATA_DEVICE_INFO,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_APP, default=APP_MYTEISON): SelectSelector(
            SelectSelectorConfig(
                options=[APP_MYTEISON, APP_TEISONME],
                translation_key="app",
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


def _device_metadata(device: dict[str, Any]) -> dict[str, Any]:
    """Snapshot the fields used to build the device registry entry."""
    return {
        "name": device.get("pileName"),
        "model": device.get("chargePointModel"),
        "vendor": device.get("chargePointVendor"),
        "firmware": device.get("firmwareVersion"),
        "serial": device.get("chargePointSerialNumber"),
    }


class TeisonConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Teison EV Charger."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise transient flow state."""
        self._credentials: dict[str, Any] = {}
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: credentials + login."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = TeisonApiClient(
                async_get_clientsession(self.hass),
                user_input[CONF_APP],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                await client.async_login()
                devices = await client.async_get_devices()
            except TeisonAuthError:
                errors["base"] = "invalid_auth"
            except TeisonConnectionError:
                errors["base"] = "cannot_connect"
            except TeisonError:
                _LOGGER.exception("Unexpected error during Teison login")
                errors["base"] = "unknown"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    self._credentials = user_input
                    self._devices = devices
                    if len(devices) == 1:
                        return await self._async_create_entry(devices[0])
                    return await self.async_step_device()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle picking a charger when the account has several."""
        if user_input is not None:
            device = next(
                d for d in self._devices if str(d["id"]) == user_input[CONF_DEVICE_ID]
            )
            return await self._async_create_entry(device)

        options = {
            str(d["id"]): (
                d.get("pileName")
                or d.get("chargePointSerialNumber")
                or f"Charger {d['id']}"
            )
            for d in self._devices
        }
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE_ID): vol.In(options)}),
        )

    async def _async_create_entry(self, device: dict[str, Any]) -> ConfigFlowResult:
        """Create the config entry for the selected charger."""
        unique_id = str(device.get("chargePointSerialNumber") or device["id"])
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        title = device.get("pileName") or "Teison EV Charger"
        return self.async_create_entry(
            title=title,
            data={
                CONF_APP: self._credentials[CONF_APP],
                CONF_USERNAME: self._credentials[CONF_USERNAME],
                CONF_PASSWORD: self._credentials[CONF_PASSWORD],
                CONF_DEVICE_ID: device["id"],
                DATA_DEVICE_INFO: _device_metadata(device),
            },
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle re-authentication after the token/password stops working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the password again and validate it."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            client = TeisonApiClient(
                async_get_clientsession(self.hass),
                entry.data[CONF_APP],
                entry.data[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                await client.async_login()
            except TeisonAuthError:
                errors["base"] = "invalid_auth"
            except TeisonConnectionError:
                errors["base"] = "cannot_connect"
            except TeisonError:
                _LOGGER.exception("Unexpected error during Teison reauth")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={CONF_USERNAME: entry.data[CONF_USERNAME]},
            errors=errors,
        )
