"""Data update coordinator for the Teison EV Charger integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    TeisonApiClient,
    TeisonAuthError,
    TeisonConnectionError,
    TeisonError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# The config entry stores its runtime coordinator in ``entry.runtime_data``.
type TeisonConfigEntry = ConfigEntry[TeisonCoordinator]


@dataclass
class TeisonData:
    """Container for a single poll of the charger."""

    detail: dict[str, Any]
    config: dict[str, Any]


class TeisonCoordinator(DataUpdateCoordinator[TeisonData]):
    """Polls live telemetry and configuration for one charger."""

    config_entry: TeisonConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: TeisonConfigEntry,
        client: TeisonApiClient,
        device_id: int | str,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.device_id = device_id

    async def _async_update_data(self) -> TeisonData:
        """Fetch telemetry and configuration in one cycle."""
        try:
            detail = await self.client.async_get_device_detail(self.device_id)
            config = await self.client.async_get_cp_config(self.device_id)
        except TeisonAuthError as err:
            # Triggers Home Assistant's reauth flow.
            raise ConfigEntryAuthFailed(str(err)) from err
        except (TeisonConnectionError, TeisonError) as err:
            raise UpdateFailed(str(err)) from err
        return TeisonData(detail=detail, config=config)
