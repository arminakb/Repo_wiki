from __future__ import annotations

from repo_wiki.domain.models import KnowledgeObject


def dedupe_knowledge(objects: list[KnowledgeObject]) -> list[KnowledgeObject]:
    seen: set[tuple[str, str, str | None, str | None]] = set()
    result: list[KnowledgeObject] = []
    for obj in sorted(objects, key=lambda item: item.quality_score, reverse=True):
        key = (obj.type, obj.title.lower(), obj.language, obj.domain)
        if key in seen:
            continue
        seen.add(key)
        result.append(obj)
    return result
