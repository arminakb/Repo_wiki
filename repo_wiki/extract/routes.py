from __future__ import annotations

import re
from typing import Any

from repo_wiki.domain.models import SourceFile, Symbol
from repo_wiki.extract.lines import line_for_offset, line_offsets
from repo_wiki.extract.typescript import route_methods


FASTAPI_ROUTE_RE = re.compile(
    r"^\s*@(?P<router>[A-Za-z_][\w]*)\.(?P<method>get|post|put|patch|delete|options|head)\(\s*['\"](?P<path>[^'\"]+)['\"]",
    re.MULTILINE,
)
FLASK_ROUTE_RE = re.compile(
    r"^\s*@(?P<app>[A-Za-z_][\w]*)\.route\(\s*['\"](?P<path>[^'\"]+)['\"](?P<args>[^)]*)\)",
    re.MULTILINE,
)


def extract_routes(file: SourceFile, symbols: list[Symbol]) -> list[dict[str, Any]]:
    if not file.content:
        return []
    if file.language == "Python":
        return extract_python_routes(file, symbols)
    if file.language in {"TypeScript", "JavaScript"}:
        return extract_ts_routes(file, symbols)
    return []


def extract_python_routes(file: SourceFile, symbols: list[Symbol]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    line_starts = line_offsets(file.content or "")
    for match in FASTAPI_ROUTE_RE.finditer(file.content or ""):
        line = line_for_offset(line_starts, match.start())
        routes.append(
            {
                "path": match.group("path"),
                "method": match.group("method").upper(),
                "framework": "FastAPI",
                "handler": _next_function_after(symbols, line),
                "line": line,
            }
        )
    for match in FLASK_ROUTE_RE.finditer(file.content or ""):
        line = line_for_offset(line_starts, match.start())
        routes.append(
            {
                "path": match.group("path"),
                "method": _flask_method(match.group("args")),
                "framework": "Flask",
                "handler": _next_function_after(symbols, line),
                "line": line,
            }
        )
    return routes


def extract_ts_routes(file: SourceFile, symbols: list[Symbol]) -> list[dict[str, Any]]:
    methods = route_methods(file)
    if not methods:
        return []
    route_path = route_path_from_file(file.path)
    routes = []
    for method in methods:
        handler = next((sym.name for sym in symbols if sym.name == method), None)
        line = next((sym.start_line for sym in symbols if sym.name == method), None)
        routes.append(
            {
                "path": route_path,
                "method": method,
                "framework": "Next.js" if "/api/" in file.path.lower() or "/app/" in file.path.lower() else None,
                "handler": handler,
                "line": line or 1,
            }
        )
    return routes


def route_path_from_file(path: str) -> str:
    lower = path.lower()
    if "/api/" in lower:
        _, api_path = path.split("/api/", 1)
        parts = [part for part in api_path.split("/") if part.lower() not in {"route.ts", "route.tsx", "route.js", "route.jsx"}]
        return "/api/" + "/".join(_clean_segment(part) for part in parts)
    return "/" + path.rsplit(".", 1)[0]


def _clean_segment(segment: str) -> str:
    if segment.startswith("[") and segment.endswith("]"):
        return "{" + segment[1:-1] + "}"
    return segment


def _next_function_after(symbols: list[Symbol], line: int) -> str | None:
    functions = [
        sym for sym in symbols if sym.kind in {"function", "route"} and sym.start_line and sym.start_line >= line
    ]
    functions.sort(key=lambda sym: sym.start_line or 0)
    return functions[0].name if functions else None


def _flask_method(args: str) -> str:
    match = re.search(r"methods\s*=\s*\[([^\]]+)\]", args)
    if not match:
        return "GET"
    methods = re.findall(r"['\"]([A-Za-z]+)['\"]", match.group(1))
    return ",".join(method.upper() for method in methods) if methods else "GET"
