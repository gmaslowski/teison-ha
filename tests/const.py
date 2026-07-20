"""Shared fixtures data for tests."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.teison.const import (
    APP_MYTEISON,
    CONF_APP,
    CONF_DEVICE_ID,
    DATA_DEVICE_INFO,
)

MOCK_DEVICE = {
    "id": 4242,
    "pileName": "Garage Wallbox",
    "chargePointModel": "Mini",
    "chargePointSerialNumber": "TSN-0001",
    "chargePointVendor": "Teison",
    "firmwareVersion": "1.2.3",
    "connStatus": 2,
}

MOCK_DETAIL = {
    "connStatus": 2,
    "power": 7200,
    "energy": 3.5,
    "accEnergy": 1234.5,
    "temperature": 28,
    "spendTime": "3661000",
    "voltage": 230,
    "voltage2": None,
    "voltage3": None,
    "current": 32,
    "current2": None,
    "current3": None,
}

MOCK_CONFIG = {
    "maxCurrent": 16,
    "directlyScheduleConstraintInfo": 63,
}

MOCK_ENTRY_DATA = {
    CONF_APP: APP_MYTEISON,
    CONF_USERNAME: "user@example.com",
    CONF_PASSWORD: "hunter2",
    CONF_DEVICE_ID: MOCK_DEVICE["id"],
    DATA_DEVICE_INFO: {
        "name": MOCK_DEVICE["pileName"],
        "model": MOCK_DEVICE["chargePointModel"],
        "vendor": MOCK_DEVICE["chargePointVendor"],
        "firmware": MOCK_DEVICE["firmwareVersion"],
        "serial": MOCK_DEVICE["chargePointSerialNumber"],
    },
}
