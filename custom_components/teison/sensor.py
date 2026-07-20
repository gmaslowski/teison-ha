"""Sensor platform for the Teison EV Charger integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CHARGE_POINT_STATUS, STATUS_OPTIONS
from .coordinator import TeisonConfigEntry, TeisonCoordinator, TeisonData
from .entity import TeisonEntity


def _status(data: TeisonData) -> str | None:
    """Map the numeric ``connStatus`` onto a translated enum value."""
    return CHARGE_POINT_STATUS.get(data.detail.get("connStatus"))


def _duration_seconds(data: TeisonData) -> float | None:
    """Convert the millisecond ``spendTime`` into whole seconds."""
    raw = data.detail.get("spendTime")
    if raw in (None, ""):
        return None
    try:
        return int(raw) // 1000
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, kw_only=True)
class TeisonSensorDescription(SensorEntityDescription):
    """Describes a Teison sensor and how to read its value."""

    value_fn: Callable[[TeisonData], Any]


SENSORS: tuple[TeisonSensorDescription, ...] = (
    TeisonSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=STATUS_OPTIONS,
        icon="mdi:ev-station",
        value_fn=_status,
    ),
    TeisonSensorDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.detail.get("power"),
    ),
    TeisonSensorDescription(
        key="energy",
        translation_key="energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        # Energy delivered in the current session; resets to 0 each session,
        # which TOTAL_INCREASING handles (MEASUREMENT is invalid for energy).
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.detail.get("energy"),
    ),
    TeisonSensorDescription(
        key="total_energy",
        translation_key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.detail.get("accEnergy"),
    ),
    TeisonSensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.detail.get("temperature"),
    ),
    TeisonSensorDescription(
        key="duration",
        translation_key="duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_display_precision=0,
        value_fn=_duration_seconds,
    ),
)

# Per-phase voltage/current. Phases 2 and 3 read ``None`` on single-phase units,
# which surfaces the entity as "unavailable" rather than a bogus zero.
for _phase, _suffix in ((1, ""), (2, "2"), (3, "3")):
    SENSORS += (
        TeisonSensorDescription(
            key=f"voltage_l{_phase}",
            translation_key=f"voltage_l{_phase}",
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda d, s=_suffix: d.detail.get(f"voltage{s}"),
        ),
        TeisonSensorDescription(
            key=f"current_l{_phase}",
            translation_key=f"current_l{_phase}",
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda d, s=_suffix: d.detail.get(f"current{s}"),
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeisonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Teison sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        TeisonSensor(coordinator, description) for description in SENSORS
    )


class TeisonSensor(TeisonEntity, SensorEntity):
    """A single read-only value reported by the charger."""

    entity_description: TeisonSensorDescription

    def __init__(
        self, coordinator: TeisonCoordinator, description: TeisonSensorDescription
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the current value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
