from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any


VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


@dataclass(frozen=True)
class Script:
    src: str | None
    code: str
    type: str

    @property
    def is_module(self) -> bool:
        return self.type.lower() == "module"


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.root: dict[str, Any] = {
            "type": "document",
            "childNodes": [],
        }
        self.stack: list[dict[str, Any]] = [self.root]
        self.scripts: list[Script] = []
        self._script_node: dict[str, Any] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        node = {
            "type": "element",
            "tagName": tag,
            "attributes": {key.lower(): value or "" for key, value in attrs},
            "childNodes": [],
        }
        self.stack[-1]["childNodes"].append(node)
        if tag == "script":
            self._script_node = node
        if tag not in VOID_ELEMENTS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        while len(self.stack) > 1:
            node = self.stack.pop()
            if node.get("tagName") == tag:
                if tag == "script":
                    self.scripts.append(
                        Script(
                            src=node["attributes"].get("src"),
                            code="".join(
                                child.get("data", "")
                                for child in node["childNodes"]
                                if child["type"] == "text"
                            ),
                            type=node["attributes"].get("type", "text/javascript"),
                        )
                    )
                    self._script_node = None
                return

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1]["childNodes"].append({"type": "text", "data": data})

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")


def parse_html(html: str) -> tuple[dict[str, Any], list[Script]]:
    parser = TreeBuilder()
    parser.feed(html)
    parser.close()
    return parser.root, parser.scripts
