"""Tests for the Teison switch platform."""

from __future__ import annotations

from homeassistant.const import STATE_OFF, STATE_ON, Platform
from homeassistant.core import HomeAssistant
import pytest

from .conftest import setup_integration
from .const import MOCK_DETAIL

ENTITY_ID = "switch.garage_wallbox_charging"


@pytest.mark.parametrize(
    ("conn_status", "expected"),
    [
        (2, STATE_ON),  # charging
        (0, STATE_OFF),  # available
        (1, STATE_OFF),  # preparing
        (8, STATE_OFF),  # faulted
    ],
)
async def test_is_on_tracks_status(
    hass: HomeAssistant,
    mock_config_entry,
    mock_client,
    conn_status: int,
    expected: str,
) -> None:
    """The switch is on only while a charging session is active."""
    mock_client.async_get_device_detail.return_value = {
        **MOCK_DETAIL,
        "connStatus": conn_status,
    }
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(ENTITY_ID).state == expected


async def test_turn_on_starts_and_refreshes(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """turn_on calls async_start_charge and re-polls the charger."""
    await setup_integration(hass, mock_config_entry)
    calls_before = mock_client.async_get_device_detail.await_count

    await hass.services.async_call(
        Platform.SWITCH, "turn_on", {"entity_id": ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()

    mock_client.async_start_charge.assert_awaited_once()
    assert mock_client.async_get_device_detail.await_count > calls_before


async def test_turn_off_stops_and_refreshes(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """turn_off calls async_stop_charge and re-polls the charger."""
    await setup_integration(hass, mock_config_entry)
    calls_before = mock_client.async_get_device_detail.await_count

    await hass.services.async_call(
        Platform.SWITCH, "turn_off", {"entity_id": ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()

    mock_client.async_stop_charge.assert_awaited_once()
    assert mock_client.async_get_device_detail.await_count > calls_before
