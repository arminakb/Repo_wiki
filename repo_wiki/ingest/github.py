from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import urlparse

from repo_wiki.domain.errors import UnsupportedSource
from repo_wiki.domain.ids import stable_id


def parse_github_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if parsed.scheme not in {"http", "https"} or parsed.netloc not in {
        "github.com",
        "www.github.com",
    } or len(parts) != 2:
        raise UnsupportedSource(f"Unsupported GitHub URL: {url}")
    name = parts[1][:-4] if parts[1].endswith(".git") else parts[1]
    return parts[0], name


def clone_github_repo(url: str, clone_dir: Path, branch: str | None = None) -> Path:
    owner, name = parse_github_url(url)
    target = clone_dir / f"{owner}__{name}_{stable_id('clone', url, branch or '')[-8:]}"
    if target.exists():
        return target
    clone_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd.extend(["--branch", branch])
    cmd.extend([url, str(target)])
    subprocess.run(cmd, check=True)
    return target
