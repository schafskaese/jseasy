from __future__ import annotations

import json
import re
import base64
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
import quickjs

from .html import Script, parse_html
from .runtime_source import RUNTIME_SOURCE


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class Selection:
    page: Page
    selector: str
    index: int = 0

    @property
    def text(self) -> str:
        return self.page.eval(
            """
            (selector, index) => {
              const node = document.querySelectorAll(selector)[index];
              return node ? node.textContent : "";
            }
            """,
            self.selector,
            self.index,
        )

    def attr(self, name: str) -> str | None:
        return self.page.eval(
            """
            (selector, index, name) => {
              const node = document.querySelectorAll(selector)[index];
              return node ? node.getAttribute(name) : null;
            }
            """,
            self.selector,
            self.index,
            name,
        )

    @property
    def html(self) -> str:
        return self.page.eval(
            """
            (selector, index) => {
              const node = document.querySelectorAll(selector)[index];
              return node ? node.outerHTML : "";
            }
            """,
            self.selector,
            self.index,
        )


class Page:
    def __init__(
        self,
        *,
        url: str = "about:blank",
        width: int = 1920,
        height: int = 1080,
        user_agent: str = DEFAULT_USER_AGENT,
        client: httpx.Client | None = None,
        raise_script_errors: bool = False,
    ) -> None:
        self.url = url
        self.width = width
        self.height = height
        self.user_agent = user_agent
        self.logs: list[tuple[str, str]] = []
        self.script_errors: list[str] = []
        self.resource_errors: list[str] = []
        self.raise_script_errors = raise_script_errors
        self._client = client or httpx.Client(follow_redirects=True, timeout=20)
        self._own_client = client is None
        self._ctx = quickjs.Context()
        self._install_host_functions()
        self._ctx.eval(RUNTIME_SOURCE)

    def __enter__(self) -> Page:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    @classmethod
    def from_html(
        cls,
        html: str,
        *,
        url: str = "about:blank",
        run_scripts: bool = True,
        **kwargs: Any,
    ) -> Page:
        page = cls(url=url, **kwargs)
        page.load_html(html, run_scripts=run_scripts)
        return page

    @classmethod
    def open(cls, url: str, *, run_scripts: bool = True, **kwargs: Any) -> Page:
        page = cls(url=url, **kwargs)
        page.goto(url, run_scripts=run_scripts)
        return page

    @classmethod
    async def aopen(cls, url: str, **kwargs: Any) -> Page:
        page = cls.open(url, **kwargs)
        await page.await_idle()
        return page

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def load_html(self, html: str, *, run_scripts: bool = True) -> None:
        tree, scripts = parse_html(html)
        environment = self._environment()
        self._ctx.set("__jseasy_tree_json", json.dumps(tree))
        self._ctx.set("__jseasy_environment_json", json.dumps(environment))
        self._ctx.eval(
            """
            globalThis.document = __jseasy.fromJson(JSON.parse(__jseasy_tree_json));
            __jseasy.installGlobals(globalThis.document, JSON.parse(__jseasy_environment_json));
            document.readyState = "interactive";
            """
        )
        self._install_stylesheets(tree)
        if run_scripts:
            self._run_scripts(scripts)
        self._ctx.eval(
            """
            document.dispatchEvent(new Event("DOMContentLoaded"));
            window.dispatchEvent(new Event("load"));
            """
        )
        self.wait_idle()
        self._ctx.eval('document.readyState = "complete";')

    def goto(self, url: str, *, run_scripts: bool = True) -> None:
        response = self._client.get(url, headers={"user-agent": self.user_agent})
        response.raise_for_status()
        self.url = str(response.url)
        self.load_html(response.text, run_scripts=run_scripts)
        self.wait_idle()

    def eval(self, source: str, *args: Any) -> Any:
        self._ctx.set("__jseasy_args_json", json.dumps(list(args)))
        self._ctx.set("__jseasy_source", source)
        result = self._ctx.eval(
            """
            (() => {
              const fn = eval(__jseasy_source);
              const __jseasy_args = JSON.parse(__jseasy_args_json);
              return fn(...__jseasy_args);
            })()
            """
        )
        self._drain_jobs()
        return self._to_python(result)

    def wait_idle(self, rounds: int = 5) -> None:
        for _ in range(rounds):
            self._ctx.eval("__jseasy.drainTimers()")
            self._drain_jobs()

    async def await_idle(self, rounds: int = 5) -> None:
        self.wait_idle(rounds)

    def select(self, selector: str, index: int = 0) -> Selection:
        return Selection(self, selector, index)

    def select_all(self, selector: str) -> list[Selection]:
        count = self.eval("(selector) => document.querySelectorAll(selector).length", selector)
        return [Selection(self, selector, index) for index in range(count)]

    def html(self) -> str:
        return self._ctx.eval("__jseasy.serialize(document)")

    def _run_scripts(self, scripts: list[Script]) -> None:
        for script in scripts:
            if not script.is_javascript:
                continue
            code = script.code
            if script.src:
                try:
                    code = self._load_script(script.src)
                except Exception as exc:
                    self.script_errors.append(f"{urljoin(self.url, script.src)}: {exc}")
                    if self.raise_script_errors:
                        raise
                    continue
            if not code.strip():
                continue
            try:
                if script.is_module:
                    self._run_module(code, self._script_base_url(script))
                else:
                    self._ctx.eval(code)
            except Exception as exc:
                self.script_errors.append(str(exc))
                if self.raise_script_errors:
                    raise
                continue
            self._drain_jobs()
            self._ctx.eval("__jseasy.drainTimers()")
            self._drain_jobs()

    def _run_module(self, code: str, base_url: str) -> None:
        self._ctx.module(self._bundle_module(code, base_url, entry=True))

    def _script_base_url(self, script: Script) -> str:
        if script.src:
            return urljoin(self.url, script.src)
        return self.url

    def _bundle_module(
        self,
        code: str,
        base_url: str,
        *,
        entry: bool = False,
        seen: set[str] | None = None,
    ) -> str:
        seen = seen or set()
        chunks: list[str] = []
        imports: list[str] = []

        def import_replacement(match: re.Match[str]) -> str:
            clause = match.group("clause").strip()
            specifier = match.group("specifier")
            dep_url = urljoin(base_url, specifier)
            module_name = "__jseasy_module_" + re.sub(r"\W+", "_", dep_url)
            if dep_url not in seen:
                seen.add(dep_url)
                dep_code = self._load_script(dep_url)
                chunks.append(
                    f"const {module_name} = (() => {{\n"
                    f"{self._bundle_module(dep_code, dep_url, seen=seen)}\n"
                    "})();"
                )
            imports.append(self._module_import_binding(clause, module_name))
            return ""

        import_pattern = re.compile(
            r"""import\s+(?P<clause>.+?)\s+from\s+['"](?P<specifier>[^'"]+)['"]\s*;?""",
        )
        side_effect_pattern = re.compile(
            r"""import\s+['"](?P<specifier>[^'"]+)['"]\s*;?""",
        )
        code = import_pattern.sub(import_replacement, code)

        def side_effect_replacement(match: re.Match[str]) -> str:
            dep_url = urljoin(base_url, match.group("specifier"))
            if dep_url not in seen:
                seen.add(dep_url)
                dep_code = self._load_script(dep_url)
                chunks.append(self._bundle_module(dep_code, dep_url, seen=seen))
            return ""

        code = side_effect_pattern.sub(side_effect_replacement, code)
        code, export_footer = self._rewrite_module_exports(code)
        body = "\n".join([*chunks, *imports, code, export_footer])
        if entry:
            return f"const exports = {{}};\n{body}"
        return f"const exports = {{}};\n{body}\nreturn exports;"

    def _module_import_binding(self, clause: str, module_name: str) -> str:
        if clause.startswith("{") and clause.endswith("}"):
            names = []
            for part in clause[1:-1].split(","):
                part = part.strip()
                if not part:
                    continue
                if " as " in part:
                    source, alias = [item.strip() for item in part.split(" as ", 1)]
                    names.append(f"{source}: {alias}")
                else:
                    names.append(part)
            return f"const {{ {', '.join(names)} }} = {module_name};"
        if clause.startswith("* as "):
            return f"const {clause[5:].strip()} = {module_name};"
        if "," in clause:
            default_name, rest = [item.strip() for item in clause.split(",", 1)]
            return f"const {default_name} = {module_name}.default;\n{self._module_import_binding(rest, module_name)}"
        return f"const {clause} = {module_name}.default;"

    def _rewrite_module_exports(self, code: str) -> tuple[str, str]:
        exports: list[tuple[str, str]] = []

        def declaration_replacement(match: re.Match[str]) -> str:
            kind = match.group("kind")
            name = match.group("name")
            exports.append((name, name))
            return f"{kind} {name}"

        code = re.sub(
            r"\bexport\s+(?P<kind>const|let|var|function|class)\s+(?P<name>[A-Za-z_$][\w$]*)",
            declaration_replacement,
            code,
        )

        def default_declaration_replacement(match: re.Match[str]) -> str:
            kind = match.group("kind")
            name = match.group("name")
            exports.append((name, "default"))
            return f"{kind} {name}"

        code = re.sub(
            r"\bexport\s+default\s+(?P<kind>function|class)\s+(?P<name>[A-Za-z_$][\w$]*)",
            default_declaration_replacement,
            code,
        )

        def named_replacement(match: re.Match[str]) -> str:
            for part in match.group("names").split(","):
                part = part.strip()
                if not part:
                    continue
                if " as " in part:
                    local, exported = [item.strip() for item in part.split(" as ", 1)]
                    exports.append((local, exported))
                else:
                    exports.append((part, part))
            return ""

        code = re.sub(r"\bexport\s+\{\s*(?P<names>[^}]+)\s*\}\s*;?", named_replacement, code)

        def default_replacement(match: re.Match[str]) -> str:
            expr = match.group("expr").strip()
            exports.append(("__default_export", "default"))
            return f"const __default_export = {expr}"

        code = re.sub(r"\bexport\s+default\s+(?P<expr>[^;]+);?", default_replacement, code)
        footer = "\n".join(f"exports[{json.dumps(exported)}] = {local};" for local, exported in exports)
        return code, footer

    def _load_script(self, src: str) -> str:
        url = urljoin(self.url, src)
        response = self._client.get(url, headers={"user-agent": self.user_agent})
        response.raise_for_status()
        return response.text

    def _install_stylesheets(self, tree: dict[str, Any]) -> None:
        stylesheets = self._collect_stylesheets(tree)
        self._ctx.set("__jseasy_stylesheets_json", json.dumps(stylesheets))
        self._ctx.eval("__jseasy.installStyleSheets(JSON.parse(__jseasy_stylesheets_json));")

    def _collect_stylesheets(self, tree: dict[str, Any]) -> list[dict[str, str]]:
        stylesheets: list[dict[str, str]] = []

        def text_content(node: dict[str, Any]) -> str:
            return "".join(
                child.get("data", "") if child.get("type") == "text" else text_content(child)
                for child in node.get("childNodes", [])
            )

        def visit(node: dict[str, Any]) -> None:
            if node.get("type") == "element":
                tag = node.get("tagName")
                attrs = node.get("attributes", {})
                if tag == "style":
                    stylesheets.append({"href": "", "text": text_content(node)})
                if tag == "link" and attrs.get("rel", "").lower() == "stylesheet" and attrs.get("href"):
                    href = urljoin(self.url, attrs["href"])
                    try:
                        response = self._client.get(href, headers={"user-agent": self.user_agent})
                        response.raise_for_status()
                        stylesheets.append({"href": href, "text": response.text})
                    except Exception as exc:
                        self.resource_errors.append(f"{href}: {exc}")
            for child in node.get("childNodes", []):
                visit(child)

        visit(tree)
        return stylesheets

    def _install_host_functions(self) -> None:
        self._ctx.add_callable("__py_console", self._console)
        self._ctx.add_callable("__py_fetch", self._fetch)
        self._ctx.add_callable("__py_atob", self._atob)
        self._ctx.add_callable("__py_btoa", self._btoa)

    def _console(self, level: str, message: str) -> None:
        self.logs.append((level, message))

    def _fetch(self, raw_url: str, raw_options: str) -> str:
        options = json.loads(raw_options)
        url = urljoin(self.url, raw_url)
        try:
            response = self._client.request(
                options.get("method", "GET"),
                url,
                content=options.get("body"),
                headers={
                    "user-agent": self.user_agent,
                    **dict(options.get("headers") or {}),
                },
            )
        except Exception as exc:
            return json.dumps({"error": f"{type(exc).__name__}: {exc}"})
        return json.dumps(
            {
                "status": response.status_code,
                "url": str(response.url),
                "headers": dict(response.headers),
                "text": response.text,
            }
        )

    def _atob(self, value: str) -> str:
        return base64.b64decode(value).decode("latin1")

    def _btoa(self, value: str) -> str:
        return base64.b64encode(value.encode("latin1")).decode("ascii")

    def _environment(self) -> dict[str, Any]:
        parsed = urlparse(self.url)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "null"
        return {
            "url": self.url,
            "origin": origin,
            "protocol": f"{parsed.scheme}:" if parsed.scheme else "",
            "host": parsed.netloc,
            "pathname": parsed.path or "/",
            "width": self.width,
            "height": self.height,
            "devicePixelRatio": 1,
            "userAgent": self.user_agent,
            "cookie": self._cookie_header(),
        }

    def _cookie_header(self) -> str:
        try:
            return "; ".join(f"{cookie.name}={cookie.value}" for cookie in self._client.cookies.jar)
        except Exception:
            return ""

    def _drain_jobs(self) -> None:
        execute_pending_job = getattr(self._ctx, "execute_pending_job", None)
        if execute_pending_job is None:
            return
        while execute_pending_job():
            pass

    def _to_python(self, value: Any) -> Any:
        if hasattr(value, "json"):
            return json.loads(value.json())
        return value
