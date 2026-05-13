import httpx

from jseasy import Page


def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/fetch-data":
        return httpx.Response(200, json={"value": "fetch ok"})
    if request.url.path == "/xhr-data":
        return httpx.Response(200, json={"value": "xhr ok"})
    return httpx.Response(404, text="not found")


client = httpx.Client(transport=httpx.MockTransport(handler))

page = Page.from_html(
    """
    <ul id="results"></ul>
    <script>
      fetch("/fetch-data")
        .then((response) => response.json())
        .then((data) => {
          const item = document.createElement("li");
          item.textContent = data.value;
          document.querySelector("#results").appendChild(item);
        });

      const xhr = new XMLHttpRequest();
      xhr.open("GET", "/xhr-data");
      xhr.onload = () => {
        const item = document.createElement("li");
        item.textContent = JSON.parse(xhr.responseText).value;
        document.querySelector("#results").appendChild(item);
      };
      xhr.send();
    </script>
    """,
    url="https://example.test",
    client=client,
)

for item in page.select_all("#results li"):
    print(item.text)
