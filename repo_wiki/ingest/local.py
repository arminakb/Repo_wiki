from __future__ import annotations

from pathlib import Path

from repo_wiki.domain.errors import RepositoryNotFound


def resolve_local_repo(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise RepositoryNotFound(f"Repository path does not exist: {root}")
    return root
