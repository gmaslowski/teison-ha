# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant **custom integration** (HACS-installable) for Teison Mini EV chargers. It drives the chargers through the vendor cloud's HTTP API — the same one the *My Teison* / *Teison Me* mobile apps use — which was reverse-engineered. There is no OCPP or local-network path. Everything lives under `custom_components/teison/`.

## Commands

```bash
python3.13 -m venv .venv && source .venv/bin/activate   # CI runs 3.13; project needs >=3.12
pip install -r requirements_test.txt   # pulls in Home Assistant + test harness

pytest                                  # full suite
pytest tests/test_api.py                # one file
pytest tests/test_config_flow.py::test_user_flow_single_device   # one test
pytest --cov=custom_components.teison --cov-report=term-missing   # what CI runs

ruff check .            # lint
ruff format --check .   # format check (drop --check to apply)
pre-commit run -a       # ruff + json/yaml/whitespace hooks
```

`requirements_test.txt` pins `homeassistant`, the test harness, and `ruff` **against a specific HA release line**. When you bump it, bump `hacs.json`'s `homeassistant` floor to match. The `ruff` pin is duplicated in **three** places that must move together — `requirements_test.txt`, `.pre-commit-config.yaml`, and `.github/workflows/test.yml` (an explicit `pip install ruff==…`). Because the lint job installs that pinned ruff explicitly, bumping `requirements_test.txt` alone is **not** exercised by CI, so keep all three in lockstep.

## Architecture

The data flow is a standard HA coordinator pipeline, but the cloud protocol has sharp edges worth knowing before touching it.

- **`api.py` — `TeisonApiClient`.** The only place that talks to the network. Two clouds share one `cpAm2/*` REST surface but differ at login: **My Teison** (`cloud.teison.com`) posts JSON with the password RSA/PKCS1v15-encrypted against a hardcoded public key; **Teison Me** (`teison-m3.x-cheng.com`) posts a plain form. Which cloud is chosen at config time (`CONF_APP`) and stored in the entry. Two gotchas: (1) the cloud returns **403 to non-browser clients**, so requests carry spoofed `User-Agent`/`Origin`/`Referer` headers — do not remove them; (2) auth failure is signaled **both** by HTTP 401/403 **and** by a `code`/`message` field inside a 200 JSON body, so both are checked. `_request` transparently re-logs-in and replays **once** on token expiry; a second failure raises `TeisonAuthError`.

- **`coordinator.py` — `TeisonCoordinator`.** One coordinator per charger, polling every 30s (`DEFAULT_SCAN_INTERVAL`). Each cycle fetches **both** `deviceDetail` (telemetry) and `getCpConfig` (settings) and bundles them into a single `TeisonData(detail, config)`. `TeisonAuthError` is translated to `ConfigEntryAuthFailed` (kicks off HA reauth); other errors become `UpdateFailed`. The coordinator is stored on `entry.runtime_data` (typed as `TeisonConfigEntry`), not in `hass.data`.

- **`config_flow.py`.** User step logs in, lists chargers, and either auto-creates the entry (single charger) or shows a picker. Unique ID is the charger serial (falling back to its id). Reauth re-prompts for the password only. A **snapshot of device metadata** (`DATA_DEVICE_INFO`) is captured here so `entity.py` can build the device-registry entry without an extra API round-trip.

- **Entity platforms** (`sensor.py`, `switch.py`, `number.py`) all extend `TeisonEntity` (`entity.py`), read straight from `coordinator.data`, and use `_attr_has_entity_name` + `translation_key`. Sensors/numbers are table-driven via `*EntityDescription` dataclasses with a `value_fn` lambda reading `detail`/`config` dicts. Writes (switch on/off, number set) call the client, then `async_request_refresh()`.

- **Status mapping** lives in `const.py`: numeric `connStatus` → OCPP-style enum strings (`CHARGE_POINT_STATUS`). `STATUS_CHARGING = 2` is the "is charging" check. Config write keys (`VendorMaxWorkCurrent`, etc.) are constants here too.

Strings/translations: `strings.json` is the source; `translations/en.json` mirrors it. Keep them in sync when adding entities or flow steps.

## Branding / icons

The brand icon is **bundled locally** at `custom_components/teison/brand/` (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`), served via Home Assistant **2026.3+**'s Brands Proxy API — it overrides the CDN with no external repo. **Do not** re-add a `brands/` staging directory: `home-assistant/brands` no longer accepts custom-integration PRs, so that path is a dead end. This is also why `validate.yml` keeps `ignore: brands` on the HACS action (that check queries the brands repo and can never pass). The bundled icon only renders on cores ≥ 2026.3; older cores silently show nothing.

## Release process

Releases are **tag-driven** — cutting a version is publishing a GitHub Release, not editing a file.

- The `version` in `manifest.json` is **vestigial**. `.github/workflows/release.yml` fires on *release published*, derives the version from the tag name (strips the `v`), **stamps `manifest.json` in the build only**, zips `custom_components/teison/` into `teison.zip`, and attaches it. So the manifest version in git does not need to match the tag, and bumping it by hand does nothing.
- Tags follow the `v0.0.x` scheme. HACS serves the attached `teison.zip` (`hacs.json` sets `zip_release: true`, `filename: teison.zip`).

Full flow to ship a change (substitute your version for `vX.Y.Z`):

```bash
# 1. Work on a branch, PR, merge (repo convention; direct pushes to main are avoided):
git checkout -b feat/my-change
# ...commit...
git push -u origin feat/my-change
gh pr create --base main --head feat/my-change --title "..." --body "..."
gh pr merge <n> --merge          # merge commit style, matching history

# 2. Cut the release off main — this triggers release.yml to build & attach the zip:
gh release create vX.Y.Z --target main --title "vX.Y.Z" --notes "..."

# 3. Verify:
gh run list --limit 5                                    # Release / Validate / Test runs
gh release view vX.Y.Z --json assets --jq '.assets[].name'   # expect teison.zip
```

CI on every push/PR: **Test** (`ruff`, then `pytest` with coverage) and **Validate** (`hassfest` + `hacs/action` with `ignore: brands`).

## Keeping this file current

Treat updating this file as part of the definition of done for any change. After implementing functionality, update it so it stays accurate — but only with **durable, generic** facts that belong in project instructions, not change-by-change detail. Update it when you change:

- **Code structure / architecture** — a new module, a shift in how data flows, a new entity platform, a changed responsibility boundary.
- **External APIs / protocols** — new cloud endpoints, auth changes, new quirks worth warning the next person about.
- **Build, lint, or test** — new commands, changed tooling or pinned versions.
- **Releasing / deployment** — any change to the release or CI workflow.

Do **not** log one-off task history, individual release version numbers, or transient details here.
