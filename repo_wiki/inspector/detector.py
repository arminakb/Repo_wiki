from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class StackProfile:
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    test_tools: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    package_manager: str | None = None


class LocalProjectInspector:
    def detect_stack(self, path: Path | str | None = None) -> StackProfile:
        root = Path(path or Path.cwd())
        found: dict[str, set[str]] = {
            "languages": set(),
            "frameworks": set(),
            "test_tools": set(),
            "databases": set(),
        }
        package_manager = None

        package_json = root / "package.json"
        if package_json.exists():
            package_manager = "npm"
            self._scan_dependencies(
                {**_json_deps(package_json, "dependencies"), **_json_deps(package_json, "devDependencies")},
                found,
                language="TypeScript" if (root / "tsconfig.json").exists() else "JavaScript",
            )

        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            package_manager = package_manager or "uv"
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            deps = list(data.get("project", {}).get("dependencies", []))
            optional = data.get("project", {}).get("optional-dependencies", {})
            for values in optional.values():
                deps.extend(values)
            self._scan_dependencies({dep: "" for dep in deps}, found, language="Python")

        requirements = root / "requirements.txt"
        if requirements.exists():
            package_manager = package_manager or "pip"
            deps = {
                line.strip().split("=", 1)[0].split("<", 1)[0].split(">", 1)[0]: ""
                for line in requirements.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            }
            self._scan_dependencies(deps, found, language="Python")

        if (root / "Cargo.toml").exists():
            found["languages"].add("Rust")
            package_manager = package_manager or "cargo"

        return StackProfile(
            languages=sorted(found["languages"]),
            frameworks=sorted(found["frameworks"]),
            test_tools=sorted(found["test_tools"]),
            databases=sorted(found["databases"]),
            package_manager=package_manager,
        )

    def _scan_dependencies(
        self, deps: dict[str, object], found: dict[str, set[str]], *, language: str
    ) -> None:
        names = {name.lower() for name in deps}
        found["languages"].add(language)
        for dep, framework in {
            "fastapi": "FastAPI",
            "django": "Django",
            "flask": "Flask",
            "next": "Next.js",
            "react": "React",
            "express": "Express",
        }.items():
            if dep in names:
                found["frameworks"].add(framework)
        for dep, tool in {"pytest": "pytest", "vitest": "vitest", "jest": "jest"}.items():
            if dep in names:
                found["test_tools"].add(tool)
        for dep, database in {"sqlalchemy": "SQLAlchemy", "prisma": "Prisma", "duckdb": "DuckDB"}.items():
            if dep in names:
                found["databases"].add(database)


def _json_deps(path: Path, key: str) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get(key, {})
    except json.JSONDecodeError:
        return {}
