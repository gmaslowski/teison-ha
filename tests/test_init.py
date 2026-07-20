"""Tests for setup, unload and entity state."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_ON, Platform
from homeassistant.core import HomeAssistant

from custom_components.teison.const import CONFIG_KEY_MAX_CURRENT

from .conftest import setup_integration


async def test_setup_and_unload(hass: HomeAssistant, mock_config_entry, mock_client):
    """The entry sets up, creates entities, and unloads cleanly."""
    entry = await setup_integration(hass, mock_config_entry)
    assert entry.state is ConfigEntryState.LOADED

    # A representative entity from each platform is created.
    assert hass.states.get("sensor.garage_wallbox_power").state == "7200"
    assert hass.states.get("switch.garage_wallbox_charging").state == STATE_ON
    assert hass.states.get("number.garage_wallbox_max_charging_current").state == "16.0"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_duration_conversion(hass: HomeAssistant, mock_config_entry, mock_client):
    """spendTime (ms) is exposed as whole seconds."""
    await setup_integration(hass, mock_config_entry)
    # 3661000 ms -> 3661 s
    assert hass.states.get("sensor.garage_wallbox_session_duration").state == "3661"


async def test_switch_calls_api(hass: HomeAssistant, mock_config_entry, mock_client):
    """Turning the switch off stops charging via the client."""
    await setup_integration(hass, mock_config_entry)
    await hass.services.async_call(
        Platform.SWITCH,
        "turn_off",
        {"entity_id": "switch.garage_wallbox_charging"},
        blocking=True,
    )
    mock_client.async_stop_charge.assert_awaited_once()


async def test_number_calls_api(hass: HomeAssistant, mock_config_entry, mock_client):
    """Setting the max current writes the vendor config key."""
    await setup_integration(hass, mock_config_entry)
    await hass.services.async_call(
        Platform.NUMBER,
        "set_value",
        {"entity_id": "number.garage_wallbox_max_charging_current", "value": 20},
        blocking=True,
    )
    mock_client.async_set_cp_config.assert_awaited_once()
    _device_id, key, value = mock_client.async_set_cp_config.await_args.args
    assert key == CONFIG_KEY_MAX_CURRENT
    assert value == 20
