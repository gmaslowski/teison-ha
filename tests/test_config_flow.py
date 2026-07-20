"""Tests for the Teison config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.teison.api import TeisonAuthError, TeisonConnectionError
from custom_components.teison.const import (
    APP_MYTEISON,
    CONF_APP,
    CONF_DEVICE_ID,
    DOMAIN,
)

from .const import MOCK_DEVICE

USER_INPUT = {
    CONF_APP: APP_MYTEISON,
    CONF_USERNAME: "user@example.com",
    CONF_PASSWORD: "hunter2",
}


async def test_user_flow_single_device(hass: HomeAssistant, mock_client) -> None:
    """A single-charger account creates the entry directly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_DEVICE["pileName"]
    assert result["data"][CONF_DEVICE_ID] == MOCK_DEVICE["id"]
    assert result["result"].unique_id == MOCK_DEVICE["chargePointSerialNumber"]


async def test_user_flow_multiple_devices(hass: HomeAssistant, mock_client) -> None:
    """A multi-charger account gets a device-selection step."""
    second = {**MOCK_DEVICE, "id": 99, "chargePointSerialNumber": "TSN-0002"}
    mock_client.async_get_devices.return_value = [MOCK_DEVICE, second]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: "99"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_DEVICE_ID] == 99


async def test_invalid_auth(hass: HomeAssistant, mock_client) -> None:
    """Bad credentials surface as a form error."""
    mock_client.async_login = AsyncMock(side_effect=TeisonAuthError("nope"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_cannot_connect(hass: HomeAssistant, mock_client) -> None:
    """Transport failure surfaces as a form error."""
    mock_client.async_login = AsyncMock(side_effect=TeisonConnectionError("down"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_no_devices(hass: HomeAssistant, mock_client) -> None:
    """An account with no chargers is rejected."""
    mock_client.async_get_devices.return_value = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["errors"] == {"base": "no_devices"}


async def test_duplicate_aborts(hass: HomeAssistant, mock_client) -> None:
    """Re-adding the same charger aborts."""
    for expected in (FlowResultType.CREATE_ENTRY, FlowResultType.ABORT):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
        assert result["type"] is expected
