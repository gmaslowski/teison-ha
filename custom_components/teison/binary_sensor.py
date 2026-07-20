"""Binary sensor platform for the Teison EV Charger integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CHARGE_POINT_STATUS, STATUS_CHARGING
from .coordinator import TeisonConfigEntry, TeisonCoordinator, TeisonData
from .entity import TeisonEntity

# ``connStatus`` values (as mapped by ``CHARGE_POINT_STATUS``) that mean no
# cable is present. Every other mapped state implies a plugged-in vehicle.
_UNPLUGGED_STATUSES = ("available", "unavailable")
_FAULTED_STATUS = "faulted"


def _status(data: TeisonData) -> str | None:
    """Map the numeric ``connStatus`` onto its OCPP-style state, if known."""
    return CHARGE_POINT_STATUS.get(data.detail.get("connStatus"))


def _plugged_in(data: TeisonData) -> bool | None:
    """Return True when a cable is present (any state bar available/unavailable)."""
    status = _status(data)
    if status is None:
        return None
    return status not in _UNPLUGGED_STATUSES


def _charging(data: TeisonData) -> bool:
    """Return True during an active charging session."""
    return data.detail.get("connStatus") == STATUS_CHARGING


def _problem(data: TeisonData) -> bool | None:
    """Return True when the charger reports a fault."""
    status = _status(data)
    if status is None:
        return None
    return status == _FAULTED_STATUS


@dataclass(frozen=True, kw_only=True)
class TeisonBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Teison binary sensor and how to read its state."""

    is_on_fn: Callable[[TeisonData], bool | None]


BINARY_SENSORS: tuple[TeisonBinarySensorDescription, ...] = (
    TeisonBinarySensorDescription(
        key="plugged_in",
        translation_key="plugged_in",
        device_class=BinarySensorDeviceClass.PLUG,
        is_on_fn=_plugged_in,
    ),
    TeisonBinarySensorDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        is_on_fn=_charging,
    ),
    TeisonBinarySensorDescription(
        key="problem",
        translation_key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_problem,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeisonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Teison binary sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        TeisonBinarySensor(coordinator, description) for description in BINARY_SENSORS
    )


class TeisonBinarySensor(TeisonEntity, BinarySensorEntity):
    """A boolean charger state derived from ``connStatus``."""

    entity_description: TeisonBinarySensorDescription

    def __init__(
        self,
        coordinator: TeisonCoordinator,
        description: TeisonBinarySensorDescription,
    ) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the current boolean state."""
        return self.entity_description.is_on_fn(self.coordinator.data)
