from __future__ import annotations

from pathlib import Path
from fnmatch import fnmatch

from repo_wiki.config import DEFAULT_EXCLUDES


TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".md",
    ".mdx",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".sql",
    ".css",
    ".html",
}


def should_skip_path(
    path: Path,
    root: Path,
    excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
    exclude_patterns: tuple[str, ...] = (),
) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    parts = set(relative.parts)
    relative_posix = relative.as_posix()
    return any(exclude in parts for exclude in excludes) or any(
        path_matches(relative_posix, pattern) for pattern in exclude_patterns
    )


def matches_include_patterns(path: Path, root: Path, include_patterns: tuple[str, ...]) -> bool:
    if not include_patterns:
        return True
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        return False
    return any(path_matches(relative, pattern) for pattern in include_patterns)


def path_matches(relative_path: str, pattern: str) -> bool:
    clean = pattern.strip()
    if not clean:
        return False
    if fnmatch(relative_path, clean):
        return True
    if clean.startswith("**/") and fnmatch(relative_path, clean[3:]):
        return True
    if clean.endswith("/**"):
        prefix = clean[:-3].rstrip("/")
        return relative_path == prefix or relative_path.startswith(prefix + "/")
    return False


def is_text_candidate(path: Path) -> bool:
    if path.name.lower().startswith(".env"):
        return False
    if path.name in {
        "Dockerfile",
        "Makefile",
        "requirements.txt",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "poetry.lock",
        "pyproject.toml",
        "setup.py",
    }:
        return True
    return path.suffix.lower() in TEXT_EXTENSIONS


def detect_language(path: Path) -> str | None:
    suffix = path.suffix.lower()
    mapping = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".md": "Markdown",
        ".mdx": "Markdown",
        ".json": "JSON",
        ".toml": "TOML",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".sql": "SQL",
        ".css": "CSS",
        ".html": "HTML",
    }
    if path.name == "requirements.txt" or path.name == "setup.py":
        return "Python"
    return mapping.get(suffix)


def is_test_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    return (
        "tests" in parts
        or "test" in parts
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.ts")
        or name.endswith(".test.tsx")
        or name.endswith(".spec.ts")
        or name.endswith(".spec.tsx")
        or name.endswith(".test.js")
        or name.endswith(".spec.js")
    )


def is_generated_path(path: Path) -> bool:
    lower = str(path).lower()
    return any(
        marker in lower
        for marker in (
            ".generated.",
            "__generated__",
            "generated/",
            ".env",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "poetry.lock",
        )
    )
