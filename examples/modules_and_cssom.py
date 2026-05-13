import httpx

from jseasy import Page


def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/app.js":
        return httpx.Response(
            200,
            text="""
            import { label } from "./labels.js";
            document.querySelector("#app").textContent = label;
            document.styleSheets[0].insertRule("#app { color: green; }");
            """,
        )
    if request.url.path == "/labels.js":
        return httpx.Response(200, text='export const label = "module ok";')
    return httpx.Response(404, text="not found")


client = httpx.Client(transport=httpx.MockTransport(handler))

page = Page.from_html(
    """
    <style>#app { color: red; }</style>
    <div id="app"></div>
    <script type="module" src="/app.js"></script>
    """,
    url="https://example.test",
    client=client,
)

print(page.select("#app").text)
print(page.eval('() => getComputedStyle(document.querySelector("#app")).getPropertyValue("color")'))
