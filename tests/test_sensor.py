"""Tests for the Teison sensor platform."""

from __future__ import annotations

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
import pytest

from .conftest import setup_integration
from .const import MOCK_DETAIL


@pytest.mark.parametrize(
    ("conn_status", "expected"),
    [
        (0, "available"),
        (1, "preparing"),
        (2, "charging"),
        (3, "suspended_evse"),
        (4, "suspended_ev"),
        (5, "finished"),
        (8, "faulted"),
        (88, "faulted"),
        (999, STATE_UNKNOWN),  # unmapped
    ],
)
async def test_status_enum_mapping(
    hass: HomeAssistant,
    mock_config_entry,
    mock_client,
    conn_status: int,
    expected: str,
) -> None:
    """The status sensor maps connStatus onto the OCPP-style vocabulary."""
    mock_client.async_get_device_detail.return_value = {
        **MOCK_DETAIL,
        "connStatus": conn_status,
    }
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get("sensor.garage_wallbox_status").state == expected


async def test_numeric_sensors(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """Power, energy, total energy, temperature and duration read from detail."""
    await setup_integration(hass, mock_config_entry)

    assert hass.states.get("sensor.garage_wallbox_power").state == "7200"
    assert hass.states.get("sensor.garage_wallbox_session_energy").state == "3.5"
    assert hass.states.get("sensor.garage_wallbox_total_energy").state == "1234.5"
    assert hass.states.get("sensor.garage_wallbox_temperature").state == "28"
    # spendTime 3661000 ms -> 3661 s
    assert hass.states.get("sensor.garage_wallbox_session_duration").state == "3661"


async def test_per_phase_sensors(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """L1 reports on a single-phase unit; unwired L2/L3 read unknown."""
    await setup_integration(hass, mock_config_entry)

    assert hass.states.get("sensor.garage_wallbox_voltage_l1").state == "230"
    assert hass.states.get("sensor.garage_wallbox_current_l1").state == "32"
    for entity_id in (
        "sensor.garage_wallbox_voltage_l2",
        "sensor.garage_wallbox_voltage_l3",
        "sensor.garage_wallbox_current_l2",
        "sensor.garage_wallbox_current_l3",
    ):
        assert hass.states.get(entity_id).state == STATE_UNKNOWN


@pytest.mark.parametrize("spend_time", [None, "", "not-a-number"])
async def test_duration_handles_bad_values(
    hass: HomeAssistant, mock_config_entry, mock_client, spend_time
) -> None:
    """Missing or non-numeric spendTime yields an unknown duration."""
    mock_client.async_get_device_detail.return_value = {
        **MOCK_DETAIL,
        "spendTime": spend_time,
    }
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get("sensor.garage_wallbox_session_duration").state == (
        STATE_UNKNOWN
    )
