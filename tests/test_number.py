"""Tests for the Teison number platform."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.teison.const import (
    CONFIG_KEY_HOUSEHOLD_CURRENT,
    CONFIG_KEY_MAX_CURRENT,
)

from .conftest import setup_integration

MAX_CURRENT = "number.garage_wallbox_max_charging_current"
HOUSEHOLD_CURRENT = "number.garage_wallbox_household_current_limit"


async def test_native_values(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """Number entities reflect the polled config values."""
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(MAX_CURRENT).state == "16.0"
    assert hass.states.get(HOUSEHOLD_CURRENT).state == "63.0"


async def test_set_max_current(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """Setting max current writes the vendor key and re-polls."""
    await setup_integration(hass, mock_config_entry)
    calls_before = mock_client.async_get_device_detail.await_count

    await hass.services.async_call(
        Platform.NUMBER,
        "set_value",
        {"entity_id": MAX_CURRENT, "value": 20},
        blocking=True,
    )
    await hass.async_block_till_done()

    device_id, key, value = mock_client.async_set_cp_config.await_args.args
    assert device_id == mock_config_entry.data["device_id"]
    assert key == CONFIG_KEY_MAX_CURRENT
    assert value == 20
    # The write is followed by a coordinator refresh.
    assert mock_client.async_get_device_detail.await_count > calls_before


async def test_set_household_current(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """Setting the household limit writes its own vendor key."""
    await setup_integration(hass, mock_config_entry)

    await hass.services.async_call(
        Platform.NUMBER,
        "set_value",
        {"entity_id": HOUSEHOLD_CURRENT, "value": 40},
        blocking=True,
    )
    await hass.async_block_till_done()

    _device_id, key, value = mock_client.async_set_cp_config.await_args.args
    assert key == CONFIG_KEY_HOUSEHOLD_CURRENT
    assert value == 40
