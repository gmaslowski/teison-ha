# Contributing

Thanks for helping improve the Teison EV Charger integration!

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
pre-commit install
```

## Standards

- Code targets the Home Assistant version pinned in `hacs.json` /
  `requirements_test.txt` and follows the
  [HA integration quality guidelines](https://developers.home-assistant.io/docs/creating_component_index).
- All I/O is async (`aiohttp`); no blocking calls in the event loop.
- Run `ruff check .`, `ruff format .`, and `pytest` before opening a PR.
- New entities need a `translation_key` and matching entries in `strings.json`
  (mirror the change into `translations/en.json`).

## Protocol notes

The vendor cloud is undocumented and occasionally changes. When adding an
endpoint, document the request/response shape in `api.py` and add a test in
`tests/test_api.py` that pins the payload contract.
