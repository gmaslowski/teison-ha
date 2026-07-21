"""Tests for the fault repair issue."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
import pytest

from custom_components.teison.const import DOMAIN

from .conftest import setup_integration
from .const import MOCK_DETAIL, MOCK_DEVICE

ISSUE_ID = f"charger_faulted_{MOCK_DEVICE['id']}"


@pytest.mark.parametrize("fault_status", [8, 88])
async def test_fault_raises_issue(
    hass: HomeAssistant, mock_config_entry, mock_client, fault_status: int
) -> None:
    """A faulted connStatus (8/88) raises an ERROR repair issue for the device."""
    mock_client.async_get_device_detail.return_value = {
        **MOCK_DETAIL,
        "connStatus": fault_status,
    }
    await setup_integration(hass, mock_config_entry)

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID)
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.ERROR
    assert issue.translation_key == "charger_faulted"
    assert issue.translation_placeholders["name"] == MOCK_DEVICE["pileName"]


async def test_no_issue_when_healthy(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """A normal status raises no repair issue."""
    await setup_integration(hass, mock_config_entry)  # MOCK_DETAIL is connStatus 2
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID) is None


async def test_issue_cleared_on_recovery(
    hass: HomeAssistant, mock_config_entry, mock_client
) -> None:
    """The issue is deleted once the charger returns to a normal status."""
    mock_client.async_get_device_detail.return_value = {
        **MOCK_DETAIL,
        "connStatus": 88,
    }
    entry = await setup_integration(hass, mock_config_entry)
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID) is not None

    mock_client.async_get_device_detail.return_value = {
        **MOCK_DETAIL,
        "connStatus": 2,
    }
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID) is None
