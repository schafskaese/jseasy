from jseasy import Page


def test_inline_script_mutates_dom():
    page = Page.from_html(
        """
        <html><body><main id="app"></main></body></html>
        <script>
          const title = document.createElement("h1");
          title.textContent = "Loaded";
          document.querySelector("#app").appendChild(title);
        </script>
        """
    )

    assert page.select("#app h1").text == "Loaded"
    assert "<h1>Loaded</h1>" in page.html()


def test_inner_html_and_attributes():
    page = Page.from_html(
        """
        <div id="app"></div>
        <script>
          document.querySelector("#app").innerHTML = '<a class="item" href="/x">Link</a>';
        </script>
        """
    )

    link = page.select("a.item")
    assert link.text == "Link"
    assert link.attr("href") == "/x"


def test_fetch_updates_dom():
    def handler(request):
        return httpx.Response(200, json={"name": "Ada"})

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.from_html(
        """
        <div id="name"></div>
        <script>
          fetch("/api").then(r => r.json()).then(data => {
            document.querySelector("#name").textContent = data.name;
          });
        </script>
        """,
        url="https://example.test",
        client=client,
    )

    assert page.select("#name").text == "Ada"


def test_dom_content_loaded_listener_runs():
    page = Page.from_html(
        """
        <span id="status"></span>
        <script>
          document.addEventListener("DOMContentLoaded", () => {
            document.querySelector("#status").innerText = "ready";
          });
        </script>
        """
    )

    assert page.select("#status").text == "ready"


def test_timer_runs():
    page = Page.from_html(
        """
        <button id="btn">old</button>
        <script>
          setTimeout(() => {
            document.querySelector("#btn").textContent = "new";
          }, 50);
        </script>
        """
    )

    assert page.select("#btn").text == "new"


def test_open_loads_html_from_client():
    def handler(request):
        return httpx.Response(200, html="<h1>Remote</h1>")

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.open("https://example.test", client=client)

    assert page.select("h1").text == "Remote"


def test_page_is_context_manager():
    def handler(request):
        return httpx.Response(200, html="<h1>Remote</h1>")

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with Page.open("https://example.test", client=client) as page:
        assert page.select("h1").text == "Remote"


def test_xml_http_request_updates_dom():
    def handler(request):
        return httpx.Response(200, json={"name": "Grace"})

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.from_html(
        """
        <div id="name"></div>
        <script>
          const xhr = new XMLHttpRequest();
          xhr.open("GET", "/api");
          xhr.onload = () => {
            document.querySelector("#name").textContent = JSON.parse(xhr.responseText).name;
          };
          xhr.send();
        </script>
        """,
        url="https://example.test",
        client=client,
    )

    assert page.select("#name").text == "Grace"


def test_cssom_and_computed_style():
    page = Page.from_html(
        """
        <style>
          .item { color: red; display: block; }
        </style>
        <div class="item" style="color: blue"></div>
        <script>
          document.styleSheets[0].insertRule(".item { font-weight: 700; }");
        </script>
        """
    )

    assert page.eval("() => document.styleSheets.length") == 1
    assert page.eval("() => document.styleSheets[0].cssRules.length") == 2
    assert page.eval('() => getComputedStyle(document.querySelector(".item")).getPropertyValue("color")') == "blue"
    assert page.eval('() => getComputedStyle(document.querySelector(".item")).getPropertyValue("font-weight")') == "700"


def test_external_stylesheet_is_loaded():
    def handler(request):
        return httpx.Response(200, text=".item { color: green; }")

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.from_html(
        """
        <link rel="stylesheet" href="/style.css">
        <div class="item"></div>
        """,
        url="https://example.test",
        client=client,
    )

    assert page.eval('() => getComputedStyle(document.querySelector(".item")).getPropertyValue("color")') == "green"


def test_inline_module_script_runs():
    page = Page.from_html(
        """
        <div id="app"></div>
        <script type="module">
          const label = "module loaded";
          document.querySelector("#app").textContent = label;
        </script>
        """
    )

    assert page.select("#app").text == "module loaded"


def test_external_module_script_runs():
    def handler(request):
        return httpx.Response(200, text='document.querySelector("#app").textContent = "external module";')

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.from_html(
        """
        <div id="app"></div>
        <script type="module" src="/app.js"></script>
        """,
        url="https://example.test",
        client=client,
    )

    assert page.select("#app").text == "external module"


def test_module_script_static_import_runs():
    def handler(request):
        if request.url.path == "/app.js":
            return httpx.Response(
                200,
                text="""
                import { label as importedLabel } from "./label.js";
                document.querySelector("#app").textContent = importedLabel;
                """,
            )
        return httpx.Response(200, text='export const label = "imported module";')

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.from_html(
        """
        <div id="app"></div>
        <script type="module" src="/app.js"></script>
        """,
        url="https://example.test",
        client=client,
    )

    assert page.select("#app").text == "imported module"


def test_event_listener_errors_do_not_abort_page_load():
    page = Page.from_html(
        """
        <div id="result"></div>
        <script>
          document.addEventListener("DOMContentLoaded", () => {
            throw new Error("listener failed");
          });
          document.addEventListener("DOMContentLoaded", () => {
            document.querySelector("#result").textContent = "ok";
          });
        </script>
        """
    )

    assert page.select("#result").text == "ok"
    assert page.logs


def test_missing_external_stylesheet_does_not_abort_page_load():
    def handler(request):
        return httpx.Response(404, text="missing")

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.from_html(
        """
        <link rel="stylesheet" href="/missing.css">
        <div id="result">ok</div>
        """,
        url="https://example.test",
        client=client,
    )

    assert page.select("#result").text == "ok"
    assert len(page.resource_errors) == 1


def test_storage_history_location_and_base64():
    page = Page.from_html(
        """
        <div id="result"></div>
        <script>
          localStorage.setItem("name", "Ada");
          sessionStorage.setItem("token", btoa("ok"));
          history.pushState({ page: 2 }, "", "/next");
          document.querySelector("#result").textContent = [
            localStorage.getItem("name"),
            atob(sessionStorage.getItem("token")),
            history.state.page,
            location.href
          ].join("|");
        </script>
        """,
        url="https://example.test/start",
    )

    assert page.select("#result").text == "Ada|ok|2|/next"


def test_fetch_request_response_headers():
    def handler(request):
        assert request.headers["x-test"] == "yes"
        return httpx.Response(201, json={"name": "Lin"})

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.from_html(
        """
        <div id="result"></div>
        <script>
          const request = new Request("/api", { headers: new Headers({ "x-test": "yes" }) });
          fetch(request).then(async response => {
            const cloned = response.clone();
            const data = await cloned.json();
            document.querySelector("#result").textContent =
              response.status + "|" + response.headers.get("content-type") + "|" + data.name;
          });
        </script>
        """,
        url="https://example.test",
        client=client,
    )

    assert page.select("#result").text == "201|application/json|Lin"


def test_mutation_observer_and_custom_events():
    page = Page.from_html(
        """
        <div id="app"></div><div id="result"></div>
        <script>
          const app = document.querySelector("#app");
          const events = [];
          new MutationObserver(records => {
            events.push(records[0].type);
            document.querySelector("#result").textContent = events.join(",");
          }).observe(app, { childList: true });
          app.addEventListener("ready", event => {
            const child = document.createElement("span");
            child.textContent = event.detail;
            app.appendChild(child);
          });
          app.dispatchEvent(new CustomEvent("ready", { detail: "ok" }));
        </script>
        """,
    )

    assert page.select("#app span").text == "ok"
    assert page.select("#result").text == "childList"


def test_matches_closest_fragment_and_keyboard_event():
    page = Page.from_html(
        """
        <section class="root"><div id="result"></div></section>
        <script>
          const fragment = document.createDocumentFragment();
          const item = document.createElement("button");
          item.className = "item";
          fragment.appendChild(item);
          document.querySelector("#result").appendChild(item);
          item.addEventListener("keydown", event => {
            item.textContent = [
              item.matches("button.item"),
              item.closest("section").className,
              event.key
            ].join("|");
          });
          item.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter" }));
        </script>
        """,
    )

    assert page.select("button.item").text == "true|root|Enter"


def test_common_selectors_layout_match_media_formdata_shadow_and_document_write():
    page = Page.from_html(
        """
        <ul><li>a</li><li>b</li></ul>
        <form><input name="q" value="abc"></form>
        <div id="box" style="width: 10px; height: 5px"></div>
        <div id="host"></div>
        <script>
          document.write("<div id=written>ok</div>");
          const root = document.querySelector("#host").attachShadow({ mode: "open" });
          root.innerHTML = "<span>shadow</span>";
        </script>
        """,
        width=1200,
    )

    assert page.eval("() => document.querySelectorAll('ul > li').length") == 2
    assert page.eval("() => document.querySelector('li:nth-child(2)').textContent") == "b"
    assert page.eval("() => document.querySelector('#box').getBoundingClientRect().width") == 10
    assert page.eval("() => matchMedia('(min-width: 1000px)').matches") is True
    assert page.eval("() => new FormData(document.querySelector('form')).get('q')") == "abc"
    assert page.eval("() => document.querySelector('#host').shadowRoot.querySelector('span').textContent") == "shadow"
    assert page.select("#written").text == "ok"


def test_module_default_and_namespace_import():
    def handler(request):
        if request.url.path == "/app.js":
            return httpx.Response(
                200,
                text="""
                import value, * as ns from "./dep.js";
                document.querySelector("#out").textContent = value + ":" + ns.named;
                """,
            )
        return httpx.Response(200, text="export const named = 'N'; export default 'D';")

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.from_html(
        '<div id="out"></div><script type="module" src="/app.js"></script>',
        url="https://example.test",
        client=client,
    )

    assert page.select("#out").text == "D:N"


def test_url_search_params_blob_cookie_fetch_and_goto():
    seen = []

    def handler(request):
        seen.append((request.url.path, request.headers.get("cookie"), request.content))
        if request.url.path == "/first":
            return httpx.Response(200, html="<h1>First</h1>")
        if request.url.path == "/second":
            return httpx.Response(200, html="<h1>Second</h1>")
        return httpx.Response(200, json={"ok": True})

    import httpx

    client = httpx.Client(transport=httpx.MockTransport(handler))
    page = Page.open("https://example.test/first", client=client)
    assert page.select("h1").text == "First"
    page.goto("https://example.test/second")
    assert page.select("h1").text == "Second"

    page.load_html(
        """
        <div id="result"></div>
        <script>
          document.cookie = "sid=abc";
          const params = new URLSearchParams({ q: "hello world" });
          params.append("page", "1");
          fetch("/api", { method: "POST", body: new Blob([params.toString()]) })
            .then(r => r.json())
            .then(data => {
              document.querySelector("#result").textContent = data.ok + ":" + params.get("q");
            });
        </script>
        """,
    )

    assert page.select("#result").text == "true:hello world"
    assert seen[-1] == ("/api", "sid=abc", b"q=hello+world&page=1")


def test_fragment_pages_have_browser_like_body_for_scripts():
    page = Page.from_html(
        """
        <main id="app"></main>
        <script>
          const node = document.createElement("p");
          node.textContent = document.body.localName + ":" + document.head.localName;
          document.body.appendChild(node);
        </script>
        """
    )

    assert page.select("p").text == "body:head"


def test_layout_shim_uses_simple_stylesheet_dimensions():
    page = Page.from_html(
        """
        <style>.box { width: 42px; height: 9px; }</style>
        <div class="box"></div>
        """
    )

    assert page.eval("() => document.querySelector('.box').getBoundingClientRect().width") == 42
    assert page.eval("() => document.querySelector('.box').offsetHeight") == 9
