from __future__ import annotations

TOPIC_EXPANSIONS = {
    "fastapi": ["fastapi", "fastapi authentication", "fastapi sqlalchemy", "fastapi testing"],
    "nextjs": ["nextjs", "nextjs app router", "nextjs auth", "nextjs stripe"],
    "django": ["django", "django rest framework", "django celery", "django testing"],
    "rust-cli": ["rust cli", "clap rust", "tokio rust", "rust error handling"],
}


def expand_topic(topic: str) -> list[str]:
    clean = " ".join(topic.split())
    key = clean.lower().replace(" ", "-").replace("_", "-")
    return TOPIC_EXPANSIONS.get(key, [clean, f"{clean} examples", f"{clean} testing"])
