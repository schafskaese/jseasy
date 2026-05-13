# API Reference

This document describes the public Python API and the browser-like JavaScript APIs exposed inside a `Page`.

## Package Import

```python
from jseasy import Page
```

## `Page`

`Page` is the main runtime object. It owns:

- one QuickJS context;
- a lightweight DOM;
- a Python-backed HTTP client;
- page diagnostics.

### `Page.from_html()`

```python
Page.from_html(
    html: str,
    *,
    url: str = "about:blank",
    run_scripts: bool = True,
    width: int = 1920,
    height: int = 1080,
    user_agent: str = DEFAULT_USER_AGENT,
    client: httpx.Client | None = None,
    raise_script_errors: bool = False,
) -> Page
```

Create a page from an HTML string.

```python
page = Page.from_html("""
<div id="app"></div>
<script>
  document.querySelector("#app").textContent = "ready";
</script>
""")

assert page.select("#app").text == "ready"
```

### `Page.open()`

```python
Page.open(
    url: str,
    *,
    run_scripts: bool = True,
    width: int = 1920,
    height: int = 1080,
    user_agent: str = DEFAULT_USER_AGENT,
    client: httpx.Client | None = None,
    raise_script_errors: bool = False,
) -> Page
```

Fetch a URL and create a page.

```python
with Page.open("https://example.com") as page:
    print(page.select("h1").text)
```

`Page.open()` uses `httpx.Client` internally. If you pass your own client, jsEasy will not close it.

### `Page.aopen()`

```python
await Page.aopen(url: str, **options) -> Page
```

Async-compatible wrapper around `Page.open()`. The current implementation still uses synchronous HTTP internally.

### Context Manager

```python
with Page.open("https://example.com") as page:
    ...
```

If jsEasy created the internal HTTP client, it is closed when the context exits.

### `page.load_html()`

```python
page.load_html(html: str, *, run_scripts: bool = True) -> None
```

Replace the current document with new HTML.

### `page.select()`

```python
page.select(selector: str, index: int = 0) -> Selection
```

Return a `Selection` wrapper for the matching element at `index`.

```python
title = page.select("h1").text
href = page.select("a.download").attr("href")
```

If no node matches, `Selection.text` and `Selection.html` return `""`, and `Selection.attr()` returns `None`.

### `page.select_all()`

```python
page.select_all(selector: str) -> list[Selection]
```

Return all matching elements.

```python
for row in page.select_all("table tr"):
    print(row.text)
```

### `page.eval()`

```python
page.eval(source: str, *args: Any) -> Any
```

Run JavaScript in the page. `source` must evaluate to a function. Arguments are JSON-serialized into JavaScript.

```python
count = page.eval(
    "(selector) => document.querySelectorAll(selector).length",
    ".item",
)
```

Objects and arrays returned by QuickJS are converted back to Python when possible.

### `page.wait_idle()`

```python
page.wait_idle(rounds: int = 5) -> None
```

Drain timers and pending Promise jobs. Use this after running JavaScript that schedules additional async work.

### `page.html()`

```python
page.html() -> str
```

Serialize the current DOM.

### `page.close()`

```python
page.close() -> None
```

Close the owned HTTP client.

## `Selection`

`Selection` is a small wrapper around a selector and index. It re-queries the DOM when accessed.

```python
selection.text -> str
selection.html -> str
selection.attr(name: str) -> str | None
```

## Diagnostics

```python
page.logs: list[tuple[str, str]]
page.script_errors: list[str]
page.resource_errors: list[str]
```

`page.logs` receives JavaScript `console.log`, `console.warn`, and `console.error` output.

`page.script_errors` receives script exceptions when `raise_script_errors=False`.

`page.resource_errors` receives stylesheet/resource failures that did not abort page loading.

## Browser-Like JavaScript APIs

### DOM

- `document`
- `Document`
- `Element`
- `Node`
- `Text`
- `DocumentFragment`
- `document.createElement()`
- `document.createTextNode()`
- `document.createDocumentFragment()`
- `document.documentElement`
- `document.body`
- `document.head`
- `document.title`
- `document.scripts`
- `document.getElementById()`
- `querySelector()`
- `querySelectorAll()`
- `matches()`
- `closest()`

### DOM Mutation

- `appendChild()`
- `removeChild()`
- `insertBefore()`
- `remove()`
- `append()`
- `innerHTML`
- `outerHTML`
- `textContent`
- `innerText`
- `getAttribute()`
- `setAttribute()`
- `hasAttribute()`
- `removeAttribute()`
- `className`
- `classList.contains()`
- `classList.add()`
- `classList.remove()`

### Events

- `Event`
- `CustomEvent`
- `MouseEvent`
- `KeyboardEvent`
- `addEventListener()`
- `removeEventListener()`
- `dispatchEvent()`
- `click()`
- basic bubbling

### Observation

- basic `MutationObserver`

### Network

- `fetch()`
- `XMLHttpRequest`
- `Request`
- `Response`
- `Headers`
- `navigator.sendBeacon()`

### Runtime

- `setTimeout()`
- `clearTimeout()`
- `setInterval()`
- `clearInterval()`
- `requestAnimationFrame()`
- `cancelAnimationFrame()`
- Promise job draining
- `performance.now()`
- `atob()`
- `btoa()`
- `console`

### Browser State

- `navigator`
- `location`
- `history`
- `screen`
- `localStorage`
- `sessionStorage`
- `document.cookie`

### CSSOM

- `CSSStyleDeclaration`
- `CSSRule`
- `CSSStyleRule`
- `CSSStyleSheet`
- `document.styleSheets`
- `insertRule()`
- `deleteRule()`
- `getComputedStyle()`

### Modules

Supported:

- classic `<script>`
- inline `<script type="module">`
- external `<script type="module" src="...">`
- simple static local imports
- named exports
- default exports in simple expression form

Not supported:

- dynamic `import()`
- import maps
- top-level await
- full ES module edge cases
