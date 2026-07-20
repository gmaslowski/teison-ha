"""Base entity for the Teison EV Charger integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_DEVICE_INFO, DOMAIN
from .coordinator import TeisonCoordinator


class TeisonEntity(CoordinatorEntity[TeisonCoordinator]):
    """Base class wiring every entity to the shared coordinator and device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TeisonCoordinator, key: str) -> None:
        """Initialise the entity for the given description key."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        info = entry.data.get(DATA_DEVICE_INFO, {})
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(coordinator.device_id))},
            manufacturer=info.get("vendor") or "Teison",
            model=info.get("model"),
            name=info.get("name") or "Teison EV Charger",
            sw_version=info.get("firmware"),
            serial_number=info.get("serial"),
        )
