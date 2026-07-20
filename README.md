# Teison EV Charger — Home Assistant integration

[![hacs][hacs-badge]][hacs] [![Validate][validate-badge]][validate-workflow]

A Home Assistant **custom integration** for [Teison](https://www.teison.com/) Mini
EV chargers (the WiFi "smart" wallboxes controlled through the *My Teison* /
*Teison Me* mobile apps). It talks to the vendor cloud over the same HTTP API the
apps use — no OCPP or local network access required.

> This is an unofficial, community project and is not affiliated with Teison.
> The cloud protocol was reverse-engineered from the mobile apps and may change
> without notice.

## Features

| Platform | Entities |
| --- | --- |
| `sensor` | Status, power, session energy, total energy, temperature, session duration, per-phase voltage (L1–L3) and current (L1–L3) |
| `switch` | Start / stop charging |
| `number` | Max charging current, household current limit |

Also provides **config-flow setup** (UI, no YAML), **re-authentication**,
multi-charger accounts, and **diagnostics** download.

## Requirements

- Home Assistant 2025.3 or newer.
- A Teison account with your charger paired in the *My Teison* or *Teison Me*
  mobile app (use the same username/password here).

## Installation

### HACS (recommended)

1. In HACS → **Integrations**, open the ⋮ menu → **Custom repositories**.
2. Add `https://github.com/gmaslowski/teison-ha` with category **Integration**.
3. Install **Teison EV Charger** and restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and search for
   *Teison EV Charger*.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=teison)

### Manual

Copy `custom_components/teison` into your Home Assistant `config/custom_components`
directory and restart.

## Configuration

All configuration is done in the UI:

1. Pick the cloud your app uses — **My Teison** (`cloud.teison.com`) or
   **Teison Me** (`teison-m3.x-cheng.com`).
2. Enter your app username and password.
3. If the account has more than one charger, pick which one to add.

## How it works

The integration polls the cloud every 30 seconds via a
`DataUpdateCoordinator`, fetching `cp/deviceDetail` (telemetry) and
`cp/getCpConfig` (settings). Writes (`startCharge`, `stopCharge`,
`changeCpConfig`) are pushed immediately and followed by a refresh. Session
tokens are refreshed transparently; a permanently rejected token starts the
Home Assistant re-authentication flow.

See [`custom_components/teison/api.py`](custom_components/teison/api.py) for the
documented protocol surface.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
pytest
ruff check . && ruff format --check .
```

## Credits

Protocol groundwork based on the community reverse-engineering effort behind the
[`volski/teison-ev-addon-repo`](https://github.com/volski/teison-ev-addon-repo)
Home Assistant add-on. This project reimplements it as a native, HACS-installable
custom integration.

## License

[MIT](LICENSE)

[hacs]: https://github.com/hacs/integration
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[validate-badge]: https://github.com/gmaslowski/teison-ha/actions/workflows/validate.yml/badge.svg
[validate-workflow]: https://github.com/gmaslowski/teison-ha/actions/workflows/validate.yml
