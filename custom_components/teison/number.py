"""Number platform for the Teison EV Charger integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONFIG_KEY_HOUSEHOLD_CURRENT, CONFIG_KEY_MAX_CURRENT
from .coordinator import TeisonConfigEntry, TeisonCoordinator, TeisonData
from .entity import TeisonEntity


@dataclass(frozen=True, kw_only=True)
class TeisonNumberDescription(NumberEntityDescription):
    """Describes a writable numeric charger setting."""

    value_fn: Callable[[TeisonData], float | None]
    config_key: str


NUMBERS: tuple[TeisonNumberDescription, ...] = (
    TeisonNumberDescription(
        key="max_current",
        translation_key="max_current",
        device_class=NumberDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=6,
        native_max_value=32,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda d: d.config.get("maxCurrent"),
        config_key=CONFIG_KEY_MAX_CURRENT,
    ),
    TeisonNumberDescription(
        key="household_current",
        translation_key="household_current",
        device_class=NumberDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=6,
        native_max_value=200,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda d: d.config.get("directlyScheduleConstraintInfo"),
        config_key=CONFIG_KEY_HOUSEHOLD_CURRENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeisonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Teison number entities from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        TeisonNumber(coordinator, description) for description in NUMBERS
    )


class TeisonNumber(TeisonEntity, NumberEntity):
    """A writable numeric charger configuration value."""

    entity_description: TeisonNumberDescription

    def __init__(
        self, coordinator: TeisonCoordinator, description: TeisonNumberDescription
    ) -> None:
        """Initialise the number entity."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        """Return the current value of the setting."""
        value = self.entity_description.value_fn(self.coordinator.data)
        return None if value is None else float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Push a new value to the charger and refresh."""
        await self.coordinator.client.async_set_cp_config(
            self.coordinator.device_id,
            self.entity_description.config_key,
            int(value),
        )
        # Force a config re-fetch so the new value is reflected immediately.
        await self.coordinator.async_request_config_refresh()
