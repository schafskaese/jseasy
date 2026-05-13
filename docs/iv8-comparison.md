# iv8 Comparison

This comparison is based on the public iv8 PyPI project description checked on 2026-05-13.

`iv8` is a much broader V8-backed browser environment emulator. `jseasy` is intentionally smaller: a Python-first scraping runtime with a lightweight JavaScript DOM environment and no browser process.

## Summary

| Area | iv8 | jsEasy |
| --- | --- | --- |
| JS engine | V8 | QuickJS |
| Implementation style | C++ native extension | Python package with JavaScript runtime shim |
| DOM/BOM/CSSOM scope | broad browser API emulation | pragmatic scraping subset |
| Layout | Pro edition claims layout support | not implemented |
| DevTools | claimed support | not implemented |
| API monitoring | claimed support | not implemented |
| Fingerprint config | broad Chrome-like config | small viewport/user-agent config |
| Packaging goal | high-fidelity browser environment | lightweight Python scraping runtime |

## Added To Narrow The Gap

After comparing against iv8, `jseasy` now includes these additional APIs:

- `localStorage` and `sessionStorage`
- `document.cookie`
- `history.pushState()` and `history.replaceState()`
- mutable `location.assign()`, `location.replace()`, `location.reload()`
- `Request`, `Response`, and `Headers`
- `navigator.sendBeacon()`
- `atob()` and `btoa()`
- `CustomEvent`, `MouseEvent`, and `KeyboardEvent`
- basic `MutationObserver`
- `DocumentFragment`
- `Element.matches()` and `Element.closest()`
- `WebSocket` constants and constructor stub

## Still Intentionally Behind iv8

These iv8-claimed areas remain out of scope for now:

- C++ native browser APIs
- V8 isolate parallelism
- DevTools remote debugging
- API access monitoring
- Chrome-like fingerprint parity
- trusted input events with `isTrusted=true`
- canvas and WebGL
- Shadow DOM
- Custom Elements
- SVG DOM
- CSS Typed OM
- full CSS rule hierarchy
- layout, box model, cascade, inheritance
- WebSocket/WebTransport transport
- Streams
- Service Worker behavior
- full HTML parser navigation semantics

## Positioning

Use `jseasy` when you want a package that is easy to inspect, package, and extend in Python, and you mostly need rendered DOM extraction after small to medium JavaScript execution.

Use `iv8` or a real browser when you need high browser API compatibility, debugging/monitoring, fingerprint-sensitive execution, or complex frontend framework behavior.
