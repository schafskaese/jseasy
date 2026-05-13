# Limitations And Compatibility

`jseasy` intentionally implements a small browser-like runtime, not a browser.

## Missing By Design

- layout
- paint
- canvas
- WebGL
- media APIs
- service workers
- browser fingerprint parity
- real navigation
- DevTools
- browser API monitoring
- trusted user input semantics

## Partial Support

CSSOM support covers simple stylesheet rules, `insertRule()`, `deleteRule()`, and `getComputedStyle()` for simple selectors. It does not compute layout, cascade priority, inheritance, pseudo-elements, or full CSS selector semantics.

Module support covers simple static imports. It does not cover import maps, dynamic `import()`, top-level await, or all ES module edge cases.

Selectors are intentionally small. Basic tags, classes, IDs, simple attributes, `tag.class`, descendant selectors, `>`, and basic `:nth-child(n)` are supported.

`MutationObserver` is basic and intended for scraping scripts. It does not implement every record field or timing nuance.

`Request`, `Response`, and `Headers` cover common fetch workflows. Streams and binary body handling are not implemented.

`Blob` support is text-backed and intended for form-style scraper workflows. Binary blobs, streams, and typed-array fidelity are not implemented.

`document.cookie` is a pragmatic in-memory cookie jar. It supports common `name=value` reads and writes for scripts and forwards those values to JS-initiated requests, but it does not implement full domain, path, expiry, `SameSite`, or secure cookie semantics.

`WebSocket` is currently a compatibility stub. It exposes constants and fails clearly when constructed.

Layout support is only a shim. `getBoundingClientRect()` and offset/client dimensions derive from simple computed pixel width/height styles and do not perform real layout.

Shadow DOM support is basic and intended for simple scripts that expect `attachShadow()` and `shadowRoot`; slotting, style scoping, and custom elements are not implemented.

## Security Challenges

The library can detect and report security challenge pages as normal DOM content, but it should not be used to automate or bypass CAPTCHAs or similar access controls.

## Compatibility Philosophy

jsEasy adds browser APIs when they are:

- deterministic;
- useful for scraping or test workflows;
- implementable without a layout/rendering engine;
- maintainable in a lightweight Python package.

If an API requires pixel layout, GPU behavior, media pipelines, or browser fingerprint fidelity, it is usually out of scope.
