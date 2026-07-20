"""Constants for the Teison EV Charger integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "teison"

# --- Config entry keys ---------------------------------------------------
CONF_APP: Final = "app"
CONF_DEVICE_ID: Final = "device_id"
# Options-flow key: how often (seconds) to poll the charger.
CONF_SCAN_INTERVAL: Final = "scan_interval"
# Snapshot of the paired device's metadata, captured during the config flow
# and used to build the device registry entry without an extra API round-trip.
DATA_DEVICE_INFO: Final = "device_info"

# --- Supported clouds ("app" the charger is paired against) --------------
APP_MYTEISON: Final = "myteison"
APP_TEISONME: Final = "teisonme"

BASE_URLS: Final = {
    APP_MYTEISON: "https://cloud.teison.com/",
    APP_TEISONME: "https://teison-m3.x-cheng.com/",
}

DEFAULT_SCAN_INTERVAL_SECONDS: Final = 30
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS)
# Bounds for the user-configurable polling interval (seconds).
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 600

# ``getCpConfig`` changes rarely, so it is polled far less often than the live
# telemetry -- at most once per this interval, plus right after a config write.
CONFIG_POLL_INTERVAL: Final = timedelta(minutes=10)

# --- Charge point status -------------------------------------------------
# ``connStatus`` from the cloud, mapped onto the OCPP-style status vocabulary
# used by the official app. Value 88 is a vendor-specific fault code.
CHARGE_POINT_STATUS: Final[dict[int, str]] = {
    0: "available",
    1: "preparing",
    2: "charging",
    3: "suspended_evse",
    4: "suspended_ev",
    5: "finished",
    6: "reserved",
    7: "unavailable",
    8: "faulted",
    88: "faulted",
}

# Sorted, de-duplicated list of possible states for the enum sensor.
STATUS_OPTIONS: Final[list[str]] = sorted(set(CHARGE_POINT_STATUS.values()))

# ``connStatus`` value that means an active charging session.
STATUS_CHARGING: Final = 2

# --- changeCpConfig keys -------------------------------------------------
CONFIG_KEY_MAX_CURRENT: Final = "VendorMaxWorkCurrent"
CONFIG_KEY_HOUSEHOLD_CURRENT: Final = "DirectlyScheduleConstraintInfo"
