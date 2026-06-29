from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

PACKS_DIR = Path(__file__).resolve().parents[2] / "packs"


@dataclass(frozen=True)
class BootstrapRepo:
    url: str
    stars: int = 0
    license: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class BootstrapPack:
    name: str
    description: str
    language: str | None
    repos: list[BootstrapRepo]


def list_packs() -> list[BootstrapPack]:
    return [load_pack(path.stem) for path in sorted(PACKS_DIR.glob("*.toml"))]


def load_pack(name: str) -> BootstrapPack:
    path = PACKS_DIR / f"{name}.toml"
    if not path.exists():
        available = ", ".join(pack.name for pack in list_packs()) or "none"
        raise ValueError(f"unknown pack: {name} (available: {available})")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return BootstrapPack(
        name=str(data["name"]),
        description=str(data.get("description") or ""),
        language=data.get("language"),
        repos=[
            BootstrapRepo(
                url=str(repo["url"]),
                stars=int(repo.get("stars") or 0),
                license=repo.get("license"),
                reason=repo.get("reason"),
            )
            for repo in data.get("repos", [])
        ],
    )
