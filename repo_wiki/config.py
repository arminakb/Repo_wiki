from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_EXCLUDES = (
    ".git",
    ".repo-wiki",
    ".skills",
    ".codex",
    ".agents",
    "node_modules",
    "vendor",
    "dist",
    "build",
    ".next",
    "coverage",
    ".venv",
    "venv",
    ".tox",
    "site-packages",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
)


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    sqlite_path: Path
    clone_dir: Path
    vault_path: Path
    max_file_size_bytes: int = 1_000_000
    license_policy: str = "permissive_only"
    default_excludes: tuple[str, ...] = DEFAULT_EXCLUDES
    default_max_tokens: int = 4000
    llm_provider: str | None = None

    @classmethod
    def from_env(cls, root: Path | None = None) -> "Settings":
        project_root = root or Path.cwd()
        config = load_toml(project_root / "repo-wiki.toml")
        storage = table(config, "storage")
        ingestion = table(config, "ingestion")
        retrieval = table(config, "retrieval")
        license_config = table(config, "license")
        llm = table(config, "llm")

        data_dir = config_path(
            os.getenv("REPO_WIKI_DATA_DIR") or storage.get("data_dir"),
            project_root,
            project_root / ".repo-wiki",
        )
        sqlite_path = config_path(
            os.getenv("REPO_WIKI_DB") or storage.get("sqlite_path"),
            project_root,
            data_dir / "repo-wiki.db",
        )
        return cls(
            data_dir=data_dir,
            sqlite_path=sqlite_path,
            clone_dir=config_path(
                os.getenv("REPO_WIKI_CLONES") or storage.get("clone_dir"),
                project_root,
                data_dir / "clones",
            ),
            vault_path=config_path(
                os.getenv("REPO_WIKI_VAULT") or storage.get("vault_path"),
                project_root,
                data_dir / "vault",
            ),
            max_file_size_bytes=int(
                os.getenv(
                    "REPO_WIKI_MAX_FILE_SIZE",
                    str(ingestion.get("max_file_size_bytes", 1_000_000)),
                )
            ),
            license_policy=str(
                os.getenv(
                    "REPO_WIKI_LICENSE_POLICY",
                    license_config.get("policy", "permissive_only"),
                )
            ),
            default_excludes=tuple(ingestion.get("default_excludes", DEFAULT_EXCLUDES)),
            default_max_tokens=int(
                os.getenv("REPO_WIKI_MAX_TOKENS", str(retrieval.get("max_tokens", 4000)))
            ),
            llm_provider=provider_or_none(os.getenv("REPO_WIKI_LLM_PROVIDER", llm.get("provider"))),
        )

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.clone_dir.mkdir(parents=True, exist_ok=True)
        self.vault_path.mkdir(parents=True, exist_ok=True)


def load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as file:
        return tomllib.load(file)


def table(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key)
    return value if isinstance(value, dict) else {}


def config_path(value: object, root: Path, default: Path) -> Path:
    if value is None:
        return default
    path = Path(str(value))
    return path if path.is_absolute() else root / path


def provider_or_none(value: object) -> str | None:
    if value is None:
        return None
    provider = str(value).strip()
    return None if provider in {"", "disabled", "none"} else provider
