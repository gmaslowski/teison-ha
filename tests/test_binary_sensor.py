"""Tests for the Teison binary_sensor platform."""

from __future__ import annotations

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
import pytest

from .conftest import setup_integration
from .const import MOCK_DETAIL

PLUGGED_IN = "binary_sensor.garage_wallbox_cable_connected"
CHARGING = "binary_sensor.garage_wallbox_charging"
PROBLEM = "binary_sensor.garage_wallbox_problem"


@pytest.mark.parametrize(
    ("conn_status", "expected"),
    [
        # (plugged_in, charging, problem)
        (0, (STATE_OFF, STATE_OFF, STATE_OFF)),  # available
        (1, (STATE_ON, STATE_OFF, STATE_OFF)),  # preparing
        (2, (STATE_ON, STATE_ON, STATE_OFF)),  # charging
        (5, (STATE_ON, STATE_OFF, STATE_OFF)),  # finished
        (7, (STATE_OFF, STATE_OFF, STATE_OFF)),  # unavailable
        (8, (STATE_ON, STATE_OFF, STATE_ON)),  # faulted
        (88, (STATE_ON, STATE_OFF, STATE_ON)),  # vendor fault code
        (999, (STATE_UNKNOWN, STATE_OFF, STATE_UNKNOWN)),  # unmapped
    ],
)
async def test_binary_sensor_states(
    hass: HomeAssistant,
    mock_config_entry,
    mock_client,
    conn_status: int,
    expected: tuple[str, str, str],
) -> None:
    """Each binary sensor tracks the mapped ``connStatus``."""
    mock_client.async_get_device_detail.return_value = {
        **MOCK_DETAIL,
        "connStatus": conn_status,
    }
    await setup_integration(hass, mock_config_entry)

    plugged, charging, problem = expected
    assert hass.states.get(PLUGGED_IN).state == plugged
    assert hass.states.get(CHARGING).state == charging
    assert hass.states.get(PROBLEM).state == problem


async def test_binary_sensor_device_classes(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """The three binary sensors expose the expected device classes."""
    await setup_integration(hass, mock_config_entry)

    assert hass.states.get(PLUGGED_IN).attributes["device_class"] == "plug"
    assert hass.states.get(CHARGING).attributes["device_class"] == "battery_charging"
    assert hass.states.get(PROBLEM).attributes["device_class"] == "problem"
