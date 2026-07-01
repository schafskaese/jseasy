# Changelog

All notable changes to jsEasy will be documented in this file.

The format is based on Keep a Changelog, and this project follows semantic versioning after `1.0`.

## 0.1.2 - 2026-07-01

### Fixed

- Failed external script downloads no longer abort the whole page load; they are collected in `page.script_errors` (unless `raise_script_errors=True`).
- Non-JavaScript script types such as `application/ld+json` and `text/template` are no longer executed as JavaScript.
- `clearTimeout()` and `clearInterval()` actually cancel timers; `setInterval()` now repeats until cleared instead of running once.
- `cancelAnimationFrame()` cancels the scheduled frame callback.
- Timers scheduled inside `DOMContentLoaded` / `load` listeners now run during `Page.from_html()` and `page.load_html()`.
- Stray closing tags (for example `</p>` without a matching open tag) no longer collapse the parsed DOM tree.
- HTML character references (`&amp;`, `&#65;`, ...) are decoded during parsing and no longer double-escaped during serialization; `innerHTML` fragment parsing decodes entities too.
- Void elements (`<img>`, `<br>`, ...) are handled correctly in `innerHTML` fragment parsing and serialized without invalid closing tags.
- `<script>` and `<style>` contents are serialized raw instead of HTML-escaped.
- Selector lists with commas (`h1, h2`) are supported in `querySelectorAll()` and `matches()`.
- Descendant selectors return each node once, in document order, instead of duplicates.
- Network failures in `fetch()` reject the returned promise with a `TypeError` instead of throwing synchronously into page scripts; XHR network failures trigger `onerror`.
- `localStorage`, `sessionStorage`, and JS-set `document.cookie` values survive `page.goto()` and `page.load_html()`, as documented.
- Pending timers and mutation observers from the previous document no longer leak into the next document after navigation.
- HTML comments in `innerHTML` fragments are ignored instead of being parsed as elements.

## 0.1.1 - 2026-05-13

### Added

- Basic `matchMedia()` support for width/height media queries.
- Layout metric shims: `getBoundingClientRect()`, `offsetWidth`, `offsetHeight`, `clientWidth`, and `clientHeight`.
- Basic `FormData` support for common form extraction.
- Basic `document.write()` support.
- Basic Shadow DOM support through `attachShadow()` and `shadowRoot`.
- Selector support for child combinator `>` and simple `:nth-child(n)`.
- Module support for default imports and namespace imports.
- `Page.goto()` for loading a new URL into an existing page.
- `URLSearchParams` and text-backed `Blob` / `Blob.slice()` for common request body workflows.
- Forwarding of JS-set `document.cookie` values into Python-backed `fetch()` and XHR calls.
- Browser-like `document.head` / `document.body` fallback for fragment HTML.
- Layout metric shims now consider simple stylesheet-derived pixel width and height values.

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
