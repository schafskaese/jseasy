# Recipes

Practical patterns for common jsEasy workflows.

## Extract Content After Inline JavaScript

```python
from jseasy import Page

page = Page.from_html("""
<div id="price"></div>
<script>
  document.querySelector("#price").textContent = "$19.99";
</script>
""")

print(page.select("#price").text)
```

## Scrape JSON-Backed Content

```python
from jseasy import Page

with Page.open("https://example.com/products") as page:
    for product in page.select_all(".product-card"):
        print(product.text)
```

If the site loads products with `fetch()`, jsEasy will route the request through Python HTTP.

## Bring Your Own HTTP Client

Use this when you need custom headers, cookies, proxies, retries, or a mocked transport.

```python
import httpx
from jseasy import Page

client = httpx.Client(
    headers={"accept-language": "en-US,en;q=0.9"},
    follow_redirects=True,
    timeout=20,
)

with Page.open("https://example.com", client=client) as page:
    print(page.select("title").text)

client.close()
```

jsEasy does not close a client that you pass in.

## Test Frontend Fragments Without A Browser

```python
from jseasy import Page

def test_widget():
    page = Page.from_html("""
    <button id="button">Run</button>
    <span id="status"></span>
    <script>
      document.querySelector("#button").addEventListener("click", () => {
        document.querySelector("#status").textContent = "done";
      });
      document.querySelector("#button").click();
    </script>
    """)

    assert page.select("#status").text == "done"
```

## Inspect Failures Without Aborting

```python
from jseasy import Page

with Page.open("https://example.com") as page:
    if page.script_errors:
        print("Non-fatal script failures:")
        for error in page.script_errors:
            print(error)
```

During development, switch to strict mode:

```python
Page.open("https://example.com", raise_script_errors=True)
```

## Detect Manual Checkpoints

jsEasy should not automate CAPTCHAs or other access controls. You can still detect that a manual step is required.

```python
from jseasy import Page

def needs_manual_checkpoint(page: Page) -> bool:
    text = page.eval("() => document.documentElement.textContent.toLowerCase()")
    return "captcha" in text or "security challenge" in text or "sicherheitsabfrage" in text

with Page.open("https://example.com/protected") as page:
    if needs_manual_checkpoint(page):
        print("Manual checkpoint required:", page.url)
    else:
        print(page.html())
```

## Use MockTransport For Repeatable Tests

```python
import httpx
from jseasy import Page

def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/api/items":
        return httpx.Response(200, json=["a", "b", "c"])
    return httpx.Response(404)

client = httpx.Client(transport=httpx.MockTransport(handler))

page = Page.from_html(
    """
    <ul id="items"></ul>
    <script>
      fetch("/api/items")
        .then((response) => response.json())
        .then((items) => {
          document.querySelector("#items").innerHTML =
            items.map((item) => `<li>${item}</li>`).join("");
        });
    </script>
    """,
    url="https://example.test",
    client=client,
)

assert [item.text for item in page.select_all("#items li")] == ["a", "b", "c"]
```
