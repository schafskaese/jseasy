# Contributing

Thanks for considering a contribution to jsEasy.

## Development Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Project Structure

```text
src/jseasy/
  page.py            Python API and host bridge
  html.py            HTML parser and script discovery
  runtime_source.py  JavaScript DOM/runtime implementation
tests/
examples/
docs/
```

## Contribution Guidelines

- Keep the runtime lightweight and scraping-oriented.
- Prefer small browser API shims over broad browser emulation.
- Add focused tests for every new API or behavior.
- Do not add CAPTCHA bypass, fingerprint evasion, credential automation, or payment-wall bypass features.
- Keep public API changes documented in `README.md` and `docs/api.md`.

## Testing

Run:

```bash
pytest
python -m build
twine check dist/*
```

## Release Changes

Update:

- `pyproject.toml`
- `CHANGELOG.md`
- `README.md` if behavior changed
- `docs/api.md` if API changed
