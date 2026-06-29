from __future__ import annotations

from collections import Counter
import re
from pathlib import Path

from repo_wiki.config import Settings
from repo_wiki.domain.ids import content_hash, stable_id
from repo_wiki.domain.models import SourceFile
from repo_wiki.ingest.filters import (
    detect_language,
    is_generated_path,
    is_test_path,
    is_text_candidate,
    matches_include_patterns,
    should_skip_path,
)


def discover_source_files(
    root: Path,
    snapshot_id: str,
    settings: Settings,
    *,
    include_patterns: tuple[str, ...] = (),
    exclude_patterns: tuple[str, ...] = (),
) -> list[SourceFile]:
    files: list[SourceFile] = []
    for path in sorted(root.rglob("*")):
        if (
            not path.is_file()
            or leaves_root(path, root)
            or is_data_dir_path(path, root, settings)
            or should_skip_path(
                path,
                root,
                excludes=settings.default_excludes,
                exclude_patterns=exclude_patterns,
            )
            or not matches_include_patterns(path, root, include_patterns)
            or not is_text_candidate(path)
        ):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        if stat.st_size > settings.max_file_size_bytes:
            continue
        raw = path.read_bytes()
        if is_binary_content(raw):
            continue
        text = redact_secrets(raw.decode("utf-8", errors="ignore"))
        relative = path.relative_to(root).as_posix()
        files.append(
            SourceFile(
                id=stable_id("file", snapshot_id, relative),
                snapshot_id=snapshot_id,
                path=relative,
                language=detect_language(path),
                mime_type=None,
                size_bytes=stat.st_size,
                line_count=max(1, text.count("\n") + 1),
                hash=content_hash(raw),
                content=text,
                is_test=is_test_path(Path(relative)),
                is_generated=is_generated_path(Path(relative)),
                is_dependency=False,
            )
        )
    return files


def is_binary_content(raw: bytes) -> bool:
    return b"\0" in raw[:4096]


def leaves_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return True
    return False


def is_data_dir_path(path: Path, root: Path, settings: Settings) -> bool:
    try:
        data_dir = settings.data_dir.resolve()
        path.resolve().relative_to(data_dir)
        data_dir.relative_to(root.resolve())
    except ValueError:
        return False
    return True


SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(
        r"(?i)['\"]?(api[_-]?key|secret|token|password)['\"]?\s*[:=]\s*"
        r"['\"]?[^'\"\s,}]{8,}['\"]?"
    ),
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
)


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def language_distribution(files: list[SourceFile]) -> dict[str, float]:
    counter = Counter(file.language for file in files if file.language and file.language != "JSON")
    total = sum(counter.values())
    if total == 0:
        return {}
    return {language: round(count / total, 4) for language, count in counter.items()}


def primary_language(files: list[SourceFile]) -> str | None:
    dist = language_distribution(files)
    if not dist:
        return None
    return max(dist.items(), key=lambda item: item[1])[0]
