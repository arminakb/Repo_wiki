from __future__ import annotations

import json
import math
import re

from repo_wiki.domain.ids import content_hash


MODEL_NAME = "local-hash-v1"
DIMENSION = 64
VECTOR_URI_PREFIX = "json:"


def embed_text(text: str, *, dimension: int = DIMENSION) -> list[float]:
    vector = [0.0] * dimension
    for term in tokenize(text):
        index = stable_index(term, dimension)
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def vector_content_hash(text: str) -> str:
    return content_hash(text.encode("utf-8"))


def vector_to_uri(vector: list[float]) -> str:
    return VECTOR_URI_PREFIX + json.dumps(vector, separators=(",", ":"))


def vector_from_uri(uri: str) -> list[float] | None:
    if not uri.startswith(VECTOR_URI_PREFIX):
        return None
    try:
        raw = json.loads(uri.removeprefix(VECTOR_URI_PREFIX))
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, list):
        return None
    return [float(value) for value in raw]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return round(sum(a * b for a, b in zip(left, right, strict=True)), 6)


def text_for_knowledge_embedding(
    *,
    title: str,
    summary: str,
    problem: str | None,
    solution: str | None,
    tags: list[str],
    payload: dict,
) -> str:
    path = payload.get("path", "")
    symbols = " ".join(
        str(symbol.get("name", ""))
        for symbol in payload.get("symbols", [])
        if isinstance(symbol, dict)
    )
    routes = " ".join(
        f"{route.get('method', '')} {route.get('path', '')}"
        for route in payload.get("routes", [])
        if isinstance(route, dict)
    )
    return " ".join(
        [
            title,
            summary,
            problem or "",
            solution or "",
            " ".join(tags),
            str(path),
            symbols,
            routes,
        ]
    )


def tokenize(text: str) -> list[str]:
    return [
        term.lower()
        for term in re.findall(r"[A-Za-z0-9_./-]+", text)
        if len(term) >= 2
    ]


def stable_index(term: str, dimension: int) -> int:
    total = 0
    for char in term:
        total = (total * 33 + ord(char)) % dimension
    return total
