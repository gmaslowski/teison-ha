"""Data update coordinator for the Teison EV Charger integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    TeisonApiClient,
    TeisonAuthError,
    TeisonConnectionError,
    TeisonError,
)
from .const import (
    CONF_SCAN_INTERVAL,
    CONFIG_POLL_INTERVAL,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
)

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
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(interval)),
        )
        self.client = client
        self.device_id = device_id
        # ``getCpConfig`` is polled lazily; keep the last result and when it was
        # fetched so it can be reused between config polls.
        self._config: dict[str, Any] = {}
        self._config_fetched_at: datetime | None = None
        self._force_config_refresh = False

    async def async_request_config_refresh(self) -> None:
        """Force ``getCpConfig`` to be re-fetched on the next update.

        Called after a config write so the number entities reflect the change
        without waiting for the periodic config poll.
        """
        self._force_config_refresh = True
        await self.async_request_refresh()

    def _config_is_stale(self, now: datetime) -> bool:
        """Return True when the cached config should be re-fetched."""
        return (
            self._force_config_refresh
            or self._config_fetched_at is None
            or now - self._config_fetched_at >= CONFIG_POLL_INTERVAL
        )

    async def _async_update_data(self) -> TeisonData:
        """Fetch telemetry every cycle; refresh config only occasionally."""
        try:
            detail = await self.client.async_get_device_detail(self.device_id)
            now = dt_util.utcnow()
            if self._config_is_stale(now):
                self._config = await self.client.async_get_cp_config(self.device_id)
                self._config_fetched_at = now
                self._force_config_refresh = False
        except TeisonAuthError as err:
            # Triggers Home Assistant's reauth flow.
            raise ConfigEntryAuthFailed(str(err)) from err
        except (TeisonConnectionError, TeisonError) as err:
            raise UpdateFailed(str(err)) from err
        return TeisonData(detail=detail, config=self._config)
