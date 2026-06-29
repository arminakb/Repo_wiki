from __future__ import annotations

import json
import re
import tomllib

from repo_wiki.domain.ids import stable_id
from repo_wiki.domain.models import Dependency, SourceFile


def extract_dependencies(files: list[SourceFile]) -> list[Dependency]:
    deps: list[Dependency] = []
    for file in files:
        if not file.content:
            continue
        if file.path.endswith("package.json"):
            deps.extend(_package_json(file))
        elif file.path.endswith("requirements.txt"):
            deps.extend(_requirements_txt(file))
        elif file.path.endswith("pyproject.toml"):
            deps.extend(_pyproject_toml(file))
        elif file.path.endswith("setup.py"):
            deps.extend(_setup_py(file))
        elif file.path.endswith("package-lock.json"):
            deps.extend(_package_lock(file))
        elif file.path.endswith("pnpm-lock.yaml"):
            deps.extend(_pnpm_lock(file))
        elif file.path.endswith("yarn.lock"):
            deps.extend(_yarn_lock(file))
        elif file.path.endswith("poetry.lock"):
            deps.extend(_poetry_lock(file))
    return deps


def _package_json(file: SourceFile) -> list[Dependency]:
    try:
        data = json.loads(file.content or "{}")
    except json.JSONDecodeError:
        return []
    deps: list[Dependency] = []
    sections = {
        "dependencies": "runtime",
        "devDependencies": "development",
        "peerDependencies": "peer",
        "optionalDependencies": "optional",
    }
    for section, scope in sections.items():
        values = data.get(section, {})
        if not isinstance(values, dict):
            continue
        for name, spec in values.items():
            deps.append(
                Dependency(
                    id=stable_id("dep", file.snapshot_id, "npm", name, file.path),
                    snapshot_id=file.snapshot_id,
                    manager="npm",
                    name=name,
                    version_spec=str(spec),
                    scope=scope,
                    manifest_path=file.path,
                )
            )
    return deps


def _requirements_txt(file: SourceFile) -> list[Dependency]:
    deps: list[Dependency] = []
    for line in (file.content or "").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#"):
            continue
        name = normalize_python_requirement_name(clean)
        deps.append(
            Dependency(
                id=stable_id("dep", file.snapshot_id, "pip", name, file.path),
                snapshot_id=file.snapshot_id,
                manager="pip",
                name=name,
                version_spec=clean,
                scope="runtime",
                manifest_path=file.path,
            )
        )
    return deps


def _pyproject_toml(file: SourceFile) -> list[Dependency]:
    try:
        data = tomllib.loads(file.content or "")
    except tomllib.TOMLDecodeError:
        return []
    deps: list[Dependency] = []
    project_deps = data.get("project", {}).get("dependencies", [])
    if isinstance(project_deps, list):
        for raw in project_deps:
            name = normalize_python_requirement_name(str(raw))
            deps.append(
                Dependency(
                    id=stable_id("dep", file.snapshot_id, "pip", name, file.path),
                    snapshot_id=file.snapshot_id,
                    manager="pip",
                    name=name,
                    version_spec=str(raw),
                    scope="runtime",
                    manifest_path=file.path,
                )
            )
    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    if isinstance(poetry_deps, dict):
        for name, spec in poetry_deps.items():
            if name.lower() == "python":
                continue
            deps.append(
                Dependency(
                    id=stable_id("dep", file.snapshot_id, "poetry", name, file.path),
                    snapshot_id=file.snapshot_id,
                    manager="poetry",
                    name=name,
                    version_spec=str(spec),
                    scope="runtime",
                    manifest_path=file.path,
                )
            )
    return deps


def _setup_py(file: SourceFile) -> list[Dependency]:
    deps: list[Dependency] = []
    content = file.content or ""
    for raw in re.findall(r"['\"]([A-Za-z0-9_.-]+(?:\[[^\]]+\])?\s*(?:[<>=!~]=?.*)?)['\"]", content):
        if not any(token in raw for token in (">", "<", "=", "~")):
            continue
        name = normalize_python_requirement_name(raw)
        deps.append(
            Dependency(
                id=stable_id("dep", file.snapshot_id, "setup.py", name, file.path),
                snapshot_id=file.snapshot_id,
                manager="setuptools",
                name=name,
                version_spec=raw.strip(),
                scope="runtime",
                manifest_path=file.path,
            )
        )
    return unique_dependencies(deps)


def _package_lock(file: SourceFile) -> list[Dependency]:
    try:
        data = json.loads(file.content or "{}")
    except json.JSONDecodeError:
        return []
    deps: list[Dependency] = []
    packages = data.get("packages")
    if isinstance(packages, dict):
        for path, payload in packages.items():
            if not path.startswith("node_modules/") or not isinstance(payload, dict):
                continue
            name = path.removeprefix("node_modules/")
            deps.append(npm_lock_dependency(file, name, payload.get("version")))
    elif isinstance(data.get("dependencies"), dict):
        for name, payload in data["dependencies"].items():
            version = payload.get("version") if isinstance(payload, dict) else None
            deps.append(npm_lock_dependency(file, name, version))
    return unique_dependencies(deps)


def _pnpm_lock(file: SourceFile) -> list[Dependency]:
    deps: list[Dependency] = []
    for line in (file.content or "").splitlines():
        match = re.match(r"\s{2}(/[^:\s]+):\s*$", line)
        if not match:
            continue
        raw = match.group(1).strip("/")
        name, version = split_lock_name_version(raw)
        deps.append(npm_lock_dependency(file, name, version, manager="pnpm"))
    return unique_dependencies(deps)


def _yarn_lock(file: SourceFile) -> list[Dependency]:
    deps: list[Dependency] = []
    for line in (file.content or "").splitlines():
        if not line or line.startswith(" ") or line.startswith("#"):
            continue
        raw = line.split(":", 1)[0].strip().strip('"')
        for item in raw.split(","):
            name = item.strip().strip('"')
            if "@" not in name:
                continue
            deps.append(npm_lock_dependency(file, yarn_package_name(name), None, manager="yarn"))
    return unique_dependencies(deps)


def _poetry_lock(file: SourceFile) -> list[Dependency]:
    deps: list[Dependency] = []
    current_name: str | None = None
    current_version: str | None = None
    for line in (file.content or "").splitlines():
        if line.strip() == "[[package]]":
            if current_name:
                deps.append(poetry_lock_dependency(file, current_name, current_version))
            current_name = None
            current_version = None
        elif line.startswith("name = "):
            current_name = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("version = "):
            current_version = line.split("=", 1)[1].strip().strip('"')
    if current_name:
        deps.append(poetry_lock_dependency(file, current_name, current_version))
    return unique_dependencies(deps)


def npm_lock_dependency(
    file: SourceFile,
    name: str,
    version: object | None,
    *,
    manager: str = "npm",
) -> Dependency:
    return Dependency(
        id=stable_id("dep", file.snapshot_id, manager, name, file.path),
        snapshot_id=file.snapshot_id,
        manager=manager,
        name=name,
        version_spec=str(version) if version is not None else None,
        scope="locked",
        manifest_path=file.path,
    )


def poetry_lock_dependency(file: SourceFile, name: str, version: str | None) -> Dependency:
    return Dependency(
        id=stable_id("dep", file.snapshot_id, "poetry", name, file.path),
        snapshot_id=file.snapshot_id,
        manager="poetry",
        name=name,
        version_spec=version,
        scope="locked",
        manifest_path=file.path,
    )


def normalize_python_requirement_name(raw: str) -> str:
    clean = raw.strip()
    clean = clean.split(";", 1)[0].strip()
    return re.split(r"\s*(?:==|>=|<=|~=|!=|>|<)\s*", clean, maxsplit=1)[0].strip()


def split_lock_name_version(raw: str) -> tuple[str, str | None]:
    if raw.startswith("@"):
        parts = raw.rsplit("@", 1)
        if len(parts) == 2 and "/" in parts[0]:
            return parts[0], parts[1]
        return raw, None
    if "@" not in raw:
        return raw, None
    return raw.rsplit("@", 1)


def yarn_package_name(raw: str) -> str:
    if raw.startswith("@"):
        parts = raw.split("@")
        return "@" + parts[1] if len(parts) > 1 else raw
    return raw.split("@", 1)[0]


def unique_dependencies(deps: list[Dependency]) -> list[Dependency]:
    by_key = {(dep.manager, dep.name, dep.manifest_path): dep for dep in deps if dep.name}
    return list(by_key.values())


def detect_frameworks(dependencies: list[Dependency], files: list[SourceFile]) -> list[str]:
    names = {dep.name.lower() for dep in dependencies}
    frameworks: set[str] = set()
    mapping = {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "next": "Next.js",
        "react": "React",
        "vue": "Vue",
        "svelte": "Svelte",
        "express": "Express",
        "prisma": "Prisma",
        "sqlalchemy": "SQLAlchemy",
        "pytest": "pytest",
        "jest": "Jest",
        "vitest": "Vitest",
    }
    for dep_name, framework in mapping.items():
        if dep_name in names:
            frameworks.add(framework)
    paths = {file.path.lower() for file in files}
    if any(path.startswith("app/") for path in paths) and "next" in names:
        frameworks.add("Next.js")
    if any(path.endswith("manage.py") for path in paths):
        frameworks.add("Django")
    return sorted(frameworks)


def detect_project_type(frameworks: list[str], files: list[SourceFile]) -> str:
    paths = {file.path.lower() for file in files}
    if any(framework in frameworks for framework in ("Next.js", "React", "Vue", "Svelte")):
        if any("api" in path or "server" in path for path in paths):
            return "fullstack"
        return "frontend"
    if any(framework in frameworks for framework in ("FastAPI", "Django", "Flask", "Express")):
        return "api"
    if any(file.is_test for file in files) and any(path.startswith("src/") for path in paths):
        return "library"
    return "unknown"
