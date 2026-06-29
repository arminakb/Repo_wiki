from __future__ import annotations

import ast

from repo_wiki.domain.ids import stable_id
from repo_wiki.domain.models import SourceFile, Symbol


def extract_python_symbols(file: SourceFile) -> list[Symbol]:
    if file.language != "Python" or not file.content:
        return []
    try:
        tree = ast.parse(file.content)
    except SyntaxError:
        return []
    symbols: list[Symbol] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            symbols.append(
                Symbol(
                    id=stable_id("sym", file.id, "class", node.name, node.lineno),
                    file_id=file.id,
                    snapshot_id=file.snapshot_id,
                    name=node.name,
                    kind="class",
                    qualified_name=f"{file.path}::{node.name}",
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    signature=f"class {node.name}",
                    docstring=ast.get_docstring(node),
                    visibility="exported" if not node.name.startswith("_") else "private",
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            async_prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            symbols.append(
                Symbol(
                    id=stable_id("sym", file.id, "function", node.name, node.lineno),
                    file_id=file.id,
                    snapshot_id=file.snapshot_id,
                    name=node.name,
                    kind="function",
                    qualified_name=f"{file.path}::{node.name}",
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    signature=f"{async_prefix}def {node.name}({', '.join(args)})",
                    docstring=ast.get_docstring(node),
                    visibility="exported" if not node.name.startswith("_") else "private",
                )
            )
    return symbols


def extract_python_imports(file: SourceFile) -> list[str]:
    if file.language != "Python" or not file.content:
        return []
    try:
        tree = ast.parse(file.content)
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    return sorted(set(imports))


def extract_python_calls(file: SourceFile) -> list[dict[str, object]]:
    if file.language != "Python" or not file.content:
        return []
    try:
        tree = ast.parse(file.content)
    except SyntaxError:
        return []
    calls: list[dict[str, object]] = []
    for parent in ast.walk(tree):
        if not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(parent):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node.func)
            if name:
                calls.append({"caller": parent.name, "callee": name, "line": node.lineno})
    return calls


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
