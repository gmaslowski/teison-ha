"""Common fixtures for Teison tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.teison.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_DETAIL, MOCK_DEVICE, MOCK_ENTRY_DATA


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading of the custom integration in every test."""


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry for one charger."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_ENTRY_DATA,
        unique_id=MOCK_DEVICE["chargePointSerialNumber"],
        title=MOCK_DEVICE["pileName"],
    )


@pytest.fixture
def mock_client() -> Generator[AsyncMock, None, None]:
    """Patch the API client with canned responses."""
    with (
        patch("custom_components.teison.TeisonApiClient", autospec=True) as init_mock,
        patch("custom_components.teison.config_flow.TeisonApiClient", new=init_mock),
    ):
        client = init_mock.return_value
        client.async_login = AsyncMock(return_value="token-123")
        client.async_get_devices = AsyncMock(return_value=[MOCK_DEVICE])
        client.async_get_device_detail = AsyncMock(return_value=MOCK_DETAIL)
        client.async_get_cp_config = AsyncMock(return_value=MOCK_CONFIG)
        client.async_set_cp_config = AsyncMock()
        client.async_start_charge = AsyncMock()
        client.async_stop_charge = AsyncMock()
        yield client


async def setup_integration(
    hass: HomeAssistant, entry: MockConfigEntry
) -> MockConfigEntry:
    """Add and set up the config entry."""
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
