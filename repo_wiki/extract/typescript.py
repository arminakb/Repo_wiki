from __future__ import annotations

from dataclasses import dataclass

from repo_wiki.domain.ids import stable_id
from repo_wiki.domain.models import SourceFile, Symbol
from repo_wiki.extract.lines import line_for_offset, line_offsets


HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
DECLARATION_KEYWORDS = {"function", "class", "interface", "type", "const", "let", "var"}


@dataclass(frozen=True)
class Token:
    value: str
    start: int
    end: int


def extract_ts_symbols(file: SourceFile) -> list[Symbol]:
    if file.language not in {"TypeScript", "JavaScript"} or not file.content:
        return []
    masked = mask_comments_and_strings(file.content)
    tokens = tokenize(masked)
    line_starts = line_offsets(file.content)
    symbols: list[Symbol] = []
    for index, token in enumerate(tokens):
        if token.value not in DECLARATION_KEYWORDS:
            continue
        name_token = next_identifier(tokens, index + 1)
        if not name_token:
            continue
        prefix = tokens[max(0, index - 2) : index]
        exported = any(item.value in {"export", "default"} for item in prefix)
        if not exported and token.value in {"type", "interface"}:
            continue
        name = name_token.value
        start_line = line_for_offset(line_starts, token.start)
        end_line = line_for_offset(line_starts, declaration_end(masked, name_token.end))
        kind = symbol_kind(token.value, name, file.path, masked[name_token.end : declaration_end(masked, name_token.end)])
        symbols.append(
            Symbol(
                id=stable_id("sym", file.id, kind, name, start_line),
                file_id=file.id,
                snapshot_id=file.snapshot_id,
                name=name,
                kind=kind,
                qualified_name=f"{file.path}::{name}",
                start_line=start_line,
                end_line=end_line,
                signature=file.content[token.start : declaration_end(masked, name_token.end)].strip(),
                visibility="exported" if exported else "module",
            )
        )
    for method in route_methods(file):
        if any(symbol.name == method and symbol.kind == "route" for symbol in symbols):
            continue
        method_token = next((token for token in tokens if token.value == method), None)
        line = line_for_offset(line_starts, method_token.start) if method_token else 1
        symbols.append(
            Symbol(
                id=stable_id("sym", file.id, "route", method, line),
                file_id=file.id,
                snapshot_id=file.snapshot_id,
                name=method,
                kind="route",
                qualified_name=f"{file.path}::{method}",
                start_line=line,
                end_line=line,
                signature=f"export async function {method}(...)",
                visibility="exported",
            )
        )
    return symbols


def extract_ts_imports(file: SourceFile) -> list[str]:
    if file.language not in {"TypeScript", "JavaScript"} or not file.content:
        return []
    tokens = tokenize_imports(file.content)
    imports: set[str] = set()
    for index, token in enumerate(tokens):
        if token.value == "import":
            target = import_target(tokens, index)
            if target:
                imports.add(target)
        if token.value == "export":
            target = export_target(tokens, index)
            if target:
                imports.add(target)
    return sorted(imports)


def route_methods(file: SourceFile) -> list[str]:
    if file.language not in {"TypeScript", "JavaScript"} or not file.content:
        return []
    path = file.path.lower()
    if not (
        path.endswith("/route.ts")
        or path.endswith("/route.tsx")
        or path.endswith("/route.js")
        or path.endswith("/route.jsx")
        or "/api/" in path
        or "routes/" in path
    ):
        return []
    tokens = tokenize(mask_comments_and_strings(file.content))
    methods: list[str] = []
    for index, token in enumerate(tokens):
        if token.value not in HTTP_METHODS:
            continue
        prefix = tokens[max(0, index - 4) : index]
        if any(item.value == "export" for item in prefix) and any(
            item.value in {"function", "const", "let", "var"} for item in prefix
        ):
            methods.append(token.value)
    if methods:
        return sorted(set(methods))
    if path.endswith(("route.ts", "route.tsx", "route.js", "route.jsx")):
        return ["ROUTE"]
    return []


def mask_comments_and_strings(content: str) -> str:
    output = list(content)
    index = 0
    while index < len(content):
        char = content[index]
        nxt = content[index + 1] if index + 1 < len(content) else ""
        if char == "/" and nxt == "/":
            index = mask_until(content, output, index, "\n")
        elif char == "/" and nxt == "*":
            index = mask_until(content, output, index, "*/")
        elif char in {"'", '"', "`"}:
            index = mask_string(content, output, index, char)
        else:
            index += 1
    return "".join(output)


def mask_comments_and_templates(content: str) -> str:
    output = list(content)
    index = 0
    while index < len(content):
        char = content[index]
        nxt = content[index + 1] if index + 1 < len(content) else ""
        if char == "/" and nxt == "/":
            index = mask_until(content, output, index, "\n")
        elif char == "/" and nxt == "*":
            index = mask_until(content, output, index, "*/")
        elif char == "`":
            index = mask_string(content, output, index, char)
        else:
            index += 1
    return "".join(output)


def mask_until(content: str, output: list[str], start: int, marker: str) -> int:
    end = content.find(marker, start + len(marker))
    if end == -1:
        end = len(content)
    else:
        end += len(marker)
    for pos in range(start, end):
        if output[pos] != "\n":
            output[pos] = " "
    return end


def mask_string(content: str, output: list[str], start: int, quote: str) -> int:
    index = start + 1
    output[start] = " "
    while index < len(content):
        if content[index] == "\\":
            output[index] = " "
            if index + 1 < len(content):
                output[index + 1] = " "
            index += 2
            continue
        if content[index] == quote:
            output[index] = " "
            return index + 1
        if output[index] != "\n":
            output[index] = " "
        index += 1
    return index


def tokenize(content: str) -> list[Token]:
    tokens: list[Token] = []
    index = 0
    while index < len(content):
        char = content[index]
        if char.isspace():
            index += 1
            continue
        if char.isalpha() or char in {"_", "$"}:
            start = index
            index += 1
            while index < len(content) and (content[index].isalnum() or content[index] in {"_", "$"}):
                index += 1
            tokens.append(Token(content[start:index], start, index))
            continue
        tokens.append(Token(char, index, index + 1))
        index += 1
    return tokens


def tokenize_imports(content: str) -> list[Token]:
    content = mask_comments_and_templates(content)
    tokens: list[Token] = []
    index = 0
    while index < len(content):
        char = content[index]
        if char.isspace():
            index += 1
            continue
        if char.isalpha() or char in {"_", "$"}:
            start = index
            index += 1
            while index < len(content) and (content[index].isalnum() or content[index] in {"_", "$"}):
                index += 1
            tokens.append(Token(content[start:index], start, index))
            continue
        if char in {"'", '"'}:
            end = read_raw_string(content, index, char)
            tokens.append(Token(content[index + 1 : end - 1], index, end))
            index = end
            continue
        tokens.append(Token(char, index, index + 1))
        index += 1
    return tokens


def read_raw_string(content: str, start: int, quote: str) -> int:
    index = start + 1
    while index < len(content):
        if content[index] == "\\":
            index += 2
            continue
        if content[index] == quote:
            return index + 1
        index += 1
    return len(content)


def next_identifier(tokens: list[Token], start: int) -> Token | None:
    for token in tokens[start:]:
        if token.value in {"async", "declare", "default"}:
            continue
        if token.value and (token.value[0].isalpha() or token.value[0] in {"_", "$"}):
            return token
        return None
    return None


def declaration_end(content: str, start: int) -> int:
    arrow = content.find("=>", start)
    semi = content.find(";", start)
    if arrow != -1 and (semi == -1 or arrow < semi):
        body_start = next_nonspace(content, arrow + 2)
        if body_start < len(content) and content[body_start] == "{":
            end = matching_brace(content, body_start) + 1
            trailing = next_nonspace(content, end)
            return trailing + 1 if trailing < len(content) and content[trailing] == ";" else end
        semi = content.find(";", arrow)
        return semi + 1 if semi != -1 else declaration_end(content, arrow + 2)
    brace = content.find("{", start)
    if brace != -1 and (semi == -1 or brace < semi):
        return matching_brace(content, brace) + 1
    if semi != -1:
        return semi + 1
    line_end = content.find("\n", start)
    return len(content) if line_end == -1 else line_end


def matching_brace(content: str, start: int) -> int:
    depth = 0
    for index in range(start, len(content)):
        if content[index] == "{":
            depth += 1
        elif content[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return len(content) - 1


def next_nonspace(content: str, start: int) -> int:
    while start < len(content) and content[start].isspace():
        start += 1
    return start


def symbol_kind(keyword: str, name: str, path: str, body: str) -> str:
    if keyword in {"class", "interface", "type"}:
        return keyword
    if _looks_like_component(name, path):
        return "component"
    if keyword == "function" or "=>" in body:
        return "function"
    return "variable"


def _looks_like_component(name: str, path: str) -> bool:
    return bool(name[:1].isupper()) and path.lower().endswith((".tsx", ".jsx"))


def import_target(tokens: list[Token], index: int) -> str | None:
    for pos, token in enumerate(tokens[index + 1 :], start=index + 1):
        if token.value == ";":
            return None
        if token.value == "from":
            after_from = tokens[pos + 1 :]
            return after_from[0].value if after_from else None
        if token.value and token.value[0] in {".", "/", "@"}:
            return token.value
    return None


def export_target(tokens: list[Token], index: int) -> str | None:
    for pos, token in enumerate(tokens[index + 1 :], start=index + 1):
        if token.value == ";":
            return None
        if token.value == "from":
            after_from = tokens[pos + 1 :]
            return after_from[0].value if after_from else None
    return None
