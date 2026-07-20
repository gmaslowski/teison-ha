"""Switch platform for the Teison EV Charger integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import STATUS_CHARGING
from .coordinator import TeisonConfigEntry, TeisonCoordinator
from .entity import TeisonEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeisonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Teison charging switch from a config entry."""
    async_add_entities([TeisonChargeSwitch(entry.runtime_data)])


class TeisonChargeSwitch(TeisonEntity, SwitchEntity):
    """Starts and stops the charging session."""

    _attr_translation_key = "charging"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator: TeisonCoordinator) -> None:
        """Initialise the switch."""
        super().__init__(coordinator, "charging")

    @property
    def is_on(self) -> bool:
        """Return True when a charging session is active."""
        return self.coordinator.data.detail.get("connStatus") == STATUS_CHARGING

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start charging."""
        await self.coordinator.client.async_start_charge(self.coordinator.device_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop charging."""
        await self.coordinator.client.async_stop_charge(self.coordinator.device_id)
        await self.coordinator.async_request_refresh()
