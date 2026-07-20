"""Diagnostics support for the Teison EV Charger integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import TeisonConfigEntry

TO_REDACT = {CONF_USERNAME, CONF_PASSWORD, "token", "idToken", "userId", "username"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: TeisonConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "detail": async_redact_data(data.detail, TO_REDACT),
        "config": async_redact_data(data.config, TO_REDACT),
    }
