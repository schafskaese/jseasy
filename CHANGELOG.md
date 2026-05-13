# Changelog

All notable changes to jsEasy will be documented in this file.

The format is based on Keep a Changelog, and this project follows semantic versioning after `1.0`.

## 0.1.1 - 2026-05-13

### Added

- Basic `matchMedia()` support for width/height media queries.
- Layout metric shims: `getBoundingClientRect()`, `offsetWidth`, `offsetHeight`, `clientWidth`, and `clientHeight`.
- Basic `FormData` support for common form extraction.
- Basic `document.write()` support.
- Basic Shadow DOM support through `attachShadow()` and `shadowRoot`.
- Selector support for child combinator `>` and simple `:nth-child(n)`.
- Module support for default imports and namespace imports.

### Fixed

- Unquoted HTML attributes in `innerHTML` / fragment parsing.
- Module imports that share a line with following JavaScript.

## 0.1.0 - 2026-05-13

### Added

- Initial Python package.
- QuickJS-backed JavaScript execution.
- Lightweight DOM implementation.
- `Page.open()` and `Page.from_html()`.
- DOM selection API through `select()` and `select_all()`.
- Script execution for classic scripts and simple module scripts.
- Python-backed `fetch()` and `XMLHttpRequest`.
- `Request`, `Response`, and `Headers`.
- Basic CSSOM and `getComputedStyle()`.
- `localStorage`, `sessionStorage`, `history`, `location`, and `document.cookie`.
- Basic event system, custom events, mouse/keyboard events, and mutation observer support.
- Examples, tests, and PyPI packaging metadata.
