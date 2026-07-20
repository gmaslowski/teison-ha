"""Tests for the split detail/config poll cadence."""

from __future__ import annotations

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.teison.const import CONFIG_POLL_INTERVAL

from .conftest import setup_integration


async def test_config_polled_less_often_than_detail(
    hass: HomeAssistant,
    mock_config_entry,
    mock_client,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Detail is fetched every cycle; config at most once per CONFIG_POLL_INTERVAL."""
    entry = await setup_integration(hass, mock_config_entry)
    coordinator = entry.runtime_data

    # First refresh fetches both.
    assert mock_client.async_get_device_detail.await_count == 1
    assert mock_client.async_get_cp_config.await_count == 1

    # A cycle well within the config interval: detail again, config reused.
    freezer.tick(timedelta(seconds=30))
    await coordinator.async_refresh()
    assert mock_client.async_get_device_detail.await_count == 2
    assert mock_client.async_get_cp_config.await_count == 1

    # Another cycle, still within the window: still reused.
    freezer.tick(timedelta(seconds=30))
    await coordinator.async_refresh()
    assert mock_client.async_get_device_detail.await_count == 3
    assert mock_client.async_get_cp_config.await_count == 1

    # Past the config interval: config is re-fetched.
    freezer.tick(CONFIG_POLL_INTERVAL)
    await coordinator.async_refresh()
    assert mock_client.async_get_device_detail.await_count == 4
    assert mock_client.async_get_cp_config.await_count == 2


async def test_config_reused_value_is_stable(
    hass: HomeAssistant,
    mock_config_entry,
    mock_client,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Between config polls, the last-known config is reused unchanged."""
    entry = await setup_integration(hass, mock_config_entry)
    coordinator = entry.runtime_data
    first_config = coordinator.data.config

    freezer.tick(timedelta(seconds=30))
    await coordinator.async_refresh()
    assert coordinator.data.config == first_config


async def test_config_refetched_immediately_after_write(
    hass: HomeAssistant,
    mock_config_entry,
    mock_client,
    freezer: FrozenDateTimeFactory,
) -> None:
    """A number write forces a config re-fetch without waiting for the interval."""
    await setup_integration(hass, mock_config_entry)
    assert mock_client.async_get_cp_config.await_count == 1

    # Still well within the config interval.
    freezer.tick(timedelta(seconds=5))
    await hass.services.async_call(
        Platform.NUMBER,
        "set_value",
        {"entity_id": "number.garage_wallbox_max_charging_current", "value": 20},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_client.async_set_cp_config.assert_awaited_once()
    assert mock_client.async_get_cp_config.await_count == 2
