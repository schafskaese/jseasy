# jsEasy

**jsEasy** (`jseasy`) is a lightweight Python runtime for scraping and testing HTML pages that need JavaScript execution, but not a full browser.

It gives Python code a browser-like DOM, executes page scripts with QuickJS, supports common network APIs such as `fetch()` and `XMLHttpRequest`, and returns the final DOM for extraction.

```text
requests + BeautifulSoup
< jsEasy
< Playwright / Selenium / real browsers
```

jsEasy is designed for the middle ground: pages where JavaScript mutates the DOM, loads JSON, runs timers, or executes small modules, but where layout, pixels, GPU APIs, and browser fingerprint parity are unnecessary.

## Highlights

- **No browser process**: no Chromium download, no WebDriver, no browser startup cost.
- **Python-first API**: `Page.open()`, `Page.from_html()`, `select()`, `select_all()`, `eval()`, `html()`.
- **Browser-like runtime**: DOM, events, timers, storage, history, location, CSSOM, `fetch`, XHR, module scripts.
- **Scraper-friendly behavior**: failed third-party scripts are collected in diagnostics instead of aborting the whole page.
- **Typed package**: ships `py.typed`.
- **PyPI-ready**: wheel/sdist build, docs, examples, tests, and release checklist.

## Installation

```bash
pip install jseasy
```

Python 3.10+ is supported.

## Quick Start

```python
from jseasy import Page

page = Page.from_html("""
<main id="app"></main>
<script>
  const title = document.createElement("h1");
  title.textContent = "Loaded without Chrome";
  document.querySelector("#app").appendChild(title);
</script>
""")

print(page.select("#app h1").text)
```

Output:

```text
Loaded without Chrome
```

## Loading A Real Page

```python
from jseasy import Page

with Page.open("https://example.com") as page:
    print(page.select("h1").text)
    print(len(page.html()))
```

`Page.open()` fetches the URL, parses HTML, loads stylesheets, executes scripts, drains pending work, and gives you the current DOM.

## Fetch And XHR

```python
import httpx
from jseasy import Page

def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"name": "Ada"})

client = httpx.Client(transport=httpx.MockTransport(handler))

page = Page.from_html(
    """
    <div id="name"></div>
    <script>
      fetch("/api")
        .then((response) => response.json())
        .then((data) => {
          document.querySelector("#name").textContent = data.name;
        });
    </script>
    """,
    url="https://example.test",
    client=client,
)

print(page.select("#name").text)
```

## Module Scripts

```python
import httpx
from jseasy import Page

def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/app.js":
        return httpx.Response(
            200,
            text="""
            import { label } from "./labels.js";
            document.querySelector("#app").textContent = label;
            """,
        )
    return httpx.Response(200, text='export const label = "module loaded";')

client = httpx.Client(transport=httpx.MockTransport(handler))

page = Page.from_html(
    '<div id="app"></div><script type="module" src="/app.js"></script>',
    url="https://example.test",
    client=client,
)

print(page.select("#app").text)
```

## Diagnostics

jsEasy is intentionally tolerant by default. A tracking script, analytics widget, or unsupported browser feature should not necessarily prevent scraping the rest of the DOM.

```python
with Page.open("https://example.com") as page:
    print(page.logs)            # console.log/warn/error output
    print(page.script_errors)   # script exceptions collected during load
    print(page.resource_errors) # stylesheet/resource failures
```

Set `raise_script_errors=True` during development when you want the first script failure to raise immediately.

```python
page = Page.from_html(html, raise_script_errors=True)
```

## Browser API Coverage

jsEasy implements a pragmatic subset of browser APIs:

| Area | Supported |
| --- | --- |
| DOM | `Document`, `Element`, `Node`, `Text`, `DocumentFragment` |
| Selection | `querySelector`, `querySelectorAll`, `matches`, `closest` |
| Mutation | `appendChild`, `removeChild`, `insertBefore`, `innerHTML`, `textContent`, basic `MutationObserver` |
| Events | `Event`, `CustomEvent`, `MouseEvent`, `KeyboardEvent`, `addEventListener`, `dispatchEvent` |
| Runtime | `setTimeout`, `setInterval`, `requestAnimationFrame`, Promise draining, `performance.now` |
| Network | `fetch`, `XMLHttpRequest`, `Request`, `Response`, `Headers`, `navigator.sendBeacon` |
| State | `localStorage`, `sessionStorage`, `document.cookie`, `history`, `location` |
| CSSOM | `document.styleSheets`, `CSSStyleSheet`, `CSSStyleRule`, `CSSStyleDeclaration`, `getComputedStyle` |
| Modules | classic scripts, `type="module"`, simple static local imports |
| Utilities | `atob`, `btoa`, `console` |

See [docs/api.md](docs/api.md) for details.

## When To Use jsEasy

Use jsEasy when:

- you need DOM extraction after simple or moderate JavaScript execution;
- content is loaded via `fetch()` or XHR;
- scripts manipulate the DOM but do not require layout;
- you want fast startup in CLI jobs, tests, CI, workers, or small containers;
- Playwright/Selenium feels too heavy for the target page.

Use a real browser when:

- the site depends on layout metrics, canvas, WebGL, media, Shadow DOM, or complex framework hydration;
- the target is fingerprint-sensitive;
- you need browser DevTools, screenshots, or user interaction fidelity;
- the page presents CAPTCHAs, payment walls, login walls, or other access controls.

## Security And Ethics

jsEasy is intended for legitimate scraping, testing, research, and data extraction where you are allowed to access the content. Respect site terms, robots policies, rate limits, copyright, privacy, and access controls.

Do not use jsEasy to bypass CAPTCHAs, authentication, payment walls, or other security mechanisms. For security challenge pages, use a human-in-the-loop checkpoint.

## Examples

See [examples/](examples):

- [basic.py](examples/basic.py)
- [network_page.py](examples/network_page.py)
- [fetch_and_xhr.py](examples/fetch_and_xhr.py)
- [modules_and_cssom.py](examples/modules_and_cssom.py)
- [manual_checkpoint.py](examples/manual_checkpoint.py)

## Documentation

- [API Reference](docs/api.md)
- [Limitations](docs/limitations.md)
- [Recipes](docs/recipes.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Release Checklist](docs/release.md)

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m build
twine check dist/*
```

## Status

Alpha. jsEasy is useful today for small to medium JavaScript-enhanced scraping workflows, but the API may change before `1.0`.

## License

MIT
