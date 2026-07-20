"""Tests for Energy dashboard correctness of the energy sensors."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant

from .conftest import setup_integration


async def test_total_energy_is_dashboard_eligible(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """Total energy must be a TOTAL_INCREASING energy sensor in kWh."""
    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.garage_wallbox_total_energy")
    assert state is not None
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENERGY
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.TOTAL_INCREASING
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfEnergy.KILO_WATT_HOUR


async def test_session_energy_kept_out_of_statistics(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """Session energy is an energy sensor with no state class (no long-term stats)."""
    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.garage_wallbox_session_energy")
    assert state is not None
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENERGY
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfEnergy.KILO_WATT_HOUR
    # No state class -> excluded from long-term statistics.
    assert ATTR_STATE_CLASS not in state.attributes


async def test_no_impossible_state_class_warning(
    hass: HomeAssistant, mock_config_entry, mock_client, caplog
) -> None:
    """Neither energy sensor triggers HA's invalid state-class warning."""
    with caplog.at_level(logging.WARNING, logger="homeassistant.components.sensor"):
        await setup_integration(hass, mock_config_entry)

    assert "impossible considering device class" not in caplog.text
