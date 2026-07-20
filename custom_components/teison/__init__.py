"""The Teison EV Charger integration."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TeisonApiClient
from .const import CONF_APP, CONF_DEVICE_ID
from .coordinator import TeisonConfigEntry, TeisonCoordinator

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: TeisonConfigEntry) -> bool:
    """Set up Teison EV Charger from a config entry."""
    client = TeisonApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_APP],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = TeisonCoordinator(hass, entry, client, entry.data[CONF_DEVICE_ID])
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TeisonConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
