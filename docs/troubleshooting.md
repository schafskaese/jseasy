# Troubleshooting

## The Page Loads, But Expected Content Is Missing

Check diagnostics first:

```python
print(page.script_errors)
print(page.resource_errors)
print(page.logs)
```

Common causes:

- unsupported browser API;
- content depends on layout measurements;
- content is behind a manual security checkpoint;
- content is loaded after more async rounds.

Try:

```python
page.wait_idle(rounds=20)
```

## A Script Needs A Missing Browser API

If the missing API is small and deterministic, add a compatibility shim with `page.eval()`:

```python
page.eval("""
() => {
  window.matchMedia = window.matchMedia || (() => ({
    matches: false,
    addEventListener() {},
    removeEventListener() {}
  }));
}
""")
```

For broad APIs such as layout, canvas, WebGL, Shadow DOM, or browser fingerprint behavior, use a real browser.

## Fetch Or XHR Requests Fail

Use a custom `httpx.Client` so you control headers, cookies, redirects, and timeouts:

```python
import httpx
from jseasy import Page

client = httpx.Client(
    headers={"user-agent": "Mozilla/5.0"},
    follow_redirects=True,
    timeout=30,
)

page = Page.open("https://example.com", client=client)
```

## Selectors Do Not Match

Selector support is intentionally small. Supported selectors include:

- tags: `div`
- classes: `.item`
- IDs: `#app`
- tag plus class: `a.link`
- simple attributes: `[data-id]`, `[data-id="123"]`
- descendant selectors: `main .item a`

Complex CSS selectors may not work yet.

## Module Scripts Fail

Supported module behavior is intentionally limited. jsEasy supports simple static local imports, but not:

- dynamic `import()`;
- import maps;
- top-level await;
- all ESM binding edge cases.

## Security Challenge Pages

jsEasy can read the challenge page as DOM, but should not automate or bypass CAPTCHAs or equivalent access controls. Use a human-in-the-loop workflow.

## When To Switch To Playwright

Use Playwright/Selenium when the target needs:

- layout metrics such as `getBoundingClientRect()` or `offsetWidth`;
- canvas or WebGL;
- screenshots;
- real input fidelity;
- Shadow DOM or Custom Elements;
- browser fingerprint compatibility;
- login/CAPTCHA/payment-wall workflows.
