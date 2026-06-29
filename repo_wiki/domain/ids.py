from __future__ import annotations

import hashlib
import uuid


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def stable_id(prefix: str, *parts: object) -> str:
    raw = "\0".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def content_hash(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()
